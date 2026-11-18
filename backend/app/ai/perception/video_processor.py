"""Process CCTV video into person-count + per-zone tracked analytics."""

from __future__ import annotations

import logging
import math
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np

from app.ai.perception.analytics import TrackSample, compute_zone_analytics
from app.ai.perception.detector import PersonDetector, get_person_detector
from app.ai.perception.tracker import CentroidTracker, Track
from app.ai.perception.zone_assigner import ZoneAssigner, ZoneDef, zones_from_venue_dict

logger = logging.getLogger(__name__)


@dataclass
class TimelinePoint:
    frame_index: int
    time_sec: float
    count: int
    avg_confidence: float
    zone_counts: dict[str, int] = field(default_factory=dict)
    active_tracks: int = 0
    mean_speed: float = 0.0
    opposing_flow: float = 0.0


@dataclass
class VideoDetectionResult:
    engine: str
    backend: str
    tracker: str
    fps: float
    frame_count: int
    frames_processed: int
    frame_stride: int
    duration_sec: float
    max_count: int
    avg_count: float
    timeline: list[TimelinePoint]
    sample_boxes: list[dict]
    zone_summary: dict[str, dict]
    unique_tracks: int
    zone_analytics: dict[str, dict]
    annotated_path: str | None = None
    preview_path: str | None = None


def _draw_detections(
    frame: np.ndarray,
    active: list[Track],
    *,
    frame_count: int,
    unique_so_far: int,
) -> np.ndarray:
    """Draw numbered person boxes + live count banner for operator proof."""
    out = frame.copy()
    h, w = out.shape[:2]
    for t in active:
        x1, y1, x2, y2 = [int(v) for v in t.bbox]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)
        color = (0, 180, 80)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"#{t.track_id}"
        conf = f"{t.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        ty = max(0, y1 - 8)
        cv2.rectangle(out, (x1, ty - th - 6), (x1 + tw + 8, ty + 2), color, -1)
        cv2.putText(out, label, (x1 + 4, ty - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(out, conf, (x1, min(h - 4, y2 + 16)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    banner = f"CrowdPulse  |  People in frame: {frame_count}  |  Unique IDs: {unique_so_far}"
    cv2.rectangle(out, (0, 0), (w, 36), (20, 40, 70), -1)
    cv2.putText(out, banner, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    return out


MAX_DETECT_SIDE = 1280


def _ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        return None


def transcode_to_h264(src: Path, dest: Path, *, fps: float | None = None, timeout: int = 600) -> bool:
    """Transcode any CCTV codec (H.265/MJPEG/etc.) to H.264 MP4 OpenCV + browsers can read."""
    ffmpeg = _ffmpeg_exe()
    if not ffmpeg:
        logger.warning("imageio-ffmpeg not installed — cannot transcode CCTV clip")
        return False
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
    ]
    if fps is not None:
        cmd.extend(["-r", str(max(2.0, fps))])
    cmd.append(str(dest))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0 or not dest.exists() or dest.stat().st_size < 1000:
            logger.warning("H.264 transcode failed: %s", (proc.stderr or "")[-400:])
            dest.unlink(missing_ok=True)
            return False
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("H.264 transcode error: %s", exc)
        dest.unlink(missing_ok=True)
        return False


def ensure_opencv_readable(path: Path) -> Path:
    """Open a real CCTV file; if OpenCV fails (H.265, odd container), transcode then retry."""
    path = Path(path)
    cap = cv2.VideoCapture(str(path))
    opened = cap.isOpened()
    ok, frame = (False, None)
    if opened:
        ok, frame = cap.read()
    cap.release()
    if opened and ok and frame is not None:
        return path

    dest = path.with_name(f"{path.stem}_readable.mp4")
    logger.info("OpenCV could not read %s — transcoding to H.264", path.name)
    if not transcode_to_h264(path, dest):
        raise ValueError(
            f"Cannot open CCTV video (unsupported codec or corrupt): {path.name}. "
            "Try exporting the clip as H.264 MP4."
        )
    cap2 = cv2.VideoCapture(str(dest))
    ok2 = cap2.isOpened()
    grabbed, frame2 = cap2.read() if ok2 else (False, None)
    cap2.release()
    if not ok2 or not grabbed or frame2 is None:
        raise ValueError(f"Transcoded file still unreadable: {dest.name}")
    return dest


def _maybe_downscale(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    side = max(h, w)
    if side <= MAX_DETECT_SIDE:
        return frame
    scale = MAX_DETECT_SIDE / float(side)
    nw, nh = max(2, int(w * scale)), max(2, int(h * scale))
    nw, nh = nw - (nw % 2), nh - (nh % 2)
    return cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)


def transcode_browser_mp4(src: Path, *, fps: float = 4.0) -> Path | None:
    """Re-encode OpenCV mp4v → H.264 so Chrome/Edge can play it."""
    src = Path(src)
    if not src.exists():
        return None
    tmp = src.with_name(src.stem + "_h264.mp4")
    if not transcode_to_h264(src, tmp, fps=fps, timeout=300):
        return None
    try:
        src.unlink(missing_ok=True)
        tmp.replace(src)
        logger.info("Annotated video transcoded to H.264 path=%s", src.name)
        return src
    except Exception as exc:  # noqa: BLE001
        logger.warning("H.264 transcode error: %s", exc)
        tmp.unlink(missing_ok=True)
        return None


def process_video_file(
    path: str | Path,
    *,
    frame_stride: int = 10,
    max_frames: int = 120,
    detector: PersonDetector | None = None,
    zones: list[ZoneDef] | None = None,
    venue_zones: list[dict] | None = None,
    annotated_out: str | Path | None = None,
    preview_out: str | Path | None = None,
) -> VideoDetectionResult:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {path}")
    if path.stat().st_size <= 0:
        raise ValueError(f"Video file is empty: {path.name}")

    path = ensure_opencv_readable(path)
    det = detector or get_person_detector()
    tracker = CentroidTracker()
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video (unsupported or corrupt): {path.name}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    if fps <= 0 or fps > 240:
        fps = 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 360)
    if src_w <= 0 or src_h <= 0:
        cap.release()
        raise ValueError(f"Video has invalid dimensions: {path.name}")
    # Sample across the *entire* clip so a 10-minute CCTV file is not reduced to the first few seconds.
    if total > max_frames:
        stride = max(1, int(math.ceil(total / float(max_frames))))
    else:
        stride = 1 if total > 0 else max(1, frame_stride)
    width, height = src_w, src_h
    if max(src_w, src_h) > MAX_DETECT_SIDE:
        scale = MAX_DETECT_SIDE / float(max(src_w, src_h))
        width = max(2, int(src_w * scale) - int(src_w * scale) % 2)
        height = max(2, int(src_h * scale) - int(src_h * scale) % 2)
    logger.info(
        "pipeline.detect start path=%s total_frames=%s fps=%.1f stride=%s max_frames=%s size=%sx%s",
        path.name,
        total,
        fps,
        stride,
        max_frames,
        width,
        height,
    )

    zone_defs = zones or zones_from_venue_dict(venue_zones or [])
    assigner = ZoneAssigner(zone_defs, width, height) if zone_defs else None

    timeline: list[TimelinePoint] = []
    sample_boxes: list[dict] = []
    samples: list[TrackSample] = []
    idx = 0
    processed = 0
    counts: list[int] = []
    zone_series: dict[str, list[int]] = {z.code: [] for z in zone_defs}
    seen_tracks: set[int] = set()
    prev_centroids: dict[int, tuple[float, float, float]] = {}  # tid -> x,y,t

    writer: cv2.VideoWriter | None = None
    annotated_path: str | None = None
    preview_path: str | None = None
    best_preview: tuple[int, np.ndarray] | None = None  # (count, frame)
    write_fps = max(2.0, min(fps / stride, 12.0))
    frames_dir: Path | None = None
    if annotated_out:
        out_p = Path(annotated_out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        # Raw OpenCV writer (mp4v) — will be transcoded to H.264 for browsers
        raw_p = out_p.with_name(out_p.stem + "_raw.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(raw_p), fourcc, write_fps, (width, height))
        if writer.isOpened():
            annotated_path = str(raw_p.resolve())
        else:
            logger.warning("Annotated VideoWriter failed to open path=%s", raw_p)
            writer = None
        frames_dir = out_p.parent / f"{out_p.stem}_frames"
        if frames_dir.exists():
            for old in frames_dir.glob("*.jpg"):
                old.unlink(missing_ok=True)
        frames_dir.mkdir(parents=True, exist_ok=True)

    while processed < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % stride != 0:
            idx += 1
            continue

        if frame is None or not isinstance(frame, np.ndarray):
            idx += 1
            continue

        frame = _maybe_downscale(frame)

        detections = det.detect(frame)
        active = tracker.update(detections)
        for t in active:
            seen_tracks.add(t.track_id)

        t_sec = idx / fps if fps > 0 else float(idx)
        frame_speeds: list[float] = []
        frame_headings: list[float] = []

        zone_counts: dict[str, int] = {z.code: 0 for z in zone_defs}
        for t in active:
            foot = ((t.bbox[0] + t.bbox[2]) / 2.0, t.bbox[3])
            z = assigner.assign(foot) if assigner else None
            zc = z.code if z else None
            if zc:
                zone_counts[zc] = zone_counts.get(zc, 0) + 1
            samples.append(
                TrackSample(
                    track_id=t.track_id,
                    zone_code=zc,
                    x=foot[0],
                    y=foot[1],
                    time_sec=t_sec,
                    confidence=t.confidence,
                )
            )
            prev = prev_centroids.get(t.track_id)
            if prev:
                dt = max(t_sec - prev[2], 1e-3)
                dist = float(np.hypot(foot[0] - prev[0], foot[1] - prev[1]))
                speed = (dist / 25.0) / dt
                frame_speeds.append(speed)
                frame_headings.append(float(np.arctan2(foot[1] - prev[1], foot[0] - prev[0])))
            prev_centroids[t.track_id] = (foot[0], foot[1], t_sec)

        for code in zone_series:
            zone_series[code].append(int(zone_counts.get(code, 0)))

        count = len(active)
        confs = [t.confidence for t in active]
        avg_conf = float(np.mean(confs)) if confs else 0.0
        mean_speed = float(np.mean(frame_speeds)) if frame_speeds else 0.0
        opposing = 0.0
        if len(frame_headings) >= 2:
            arr = np.asarray(frame_headings)
            R = float(np.hypot(np.mean(np.cos(arr)), np.mean(np.sin(arr))))
            opposing = float(np.clip(1.0 - R, 0.0, 1.0))

        timeline.append(
            TimelinePoint(
                frame_index=idx,
                time_sec=round(t_sec, 3),
                count=count,
                avg_confidence=round(avg_conf, 3),
                zone_counts=zone_counts,
                active_tracks=count,
                mean_speed=round(mean_speed, 3),
                opposing_flow=round(opposing, 3),
            )
        )
        counts.append(count)
        if not sample_boxes and active:
            sample_boxes = [
                {
                    "track_id": t.track_id,
                    "bbox": t.bbox,
                    "confidence": round(t.confidence, 3),
                }
                for t in active[:12]
            ]

        annotated = _draw_detections(
            frame,
            active,
            frame_count=count,
            unique_so_far=len(seen_tracks),
        )
        if writer is not None:
            writer.write(annotated)
        if frames_dir is not None:
            cv2.imwrite(str(frames_dir / f"{processed:04d}.jpg"), annotated)
        if active and (best_preview is None or count >= best_preview[0]):
            best_preview = (count, annotated.copy())

        processed += 1
        idx += 1

    cap.release()
    if writer is not None:
        writer.release()

    # Convert raw mp4v → H.264 browser-playable file at annotated_out path
    if annotated_path and annotated_out:
        raw = Path(annotated_path)
        final = Path(annotated_out)
        converted = transcode_browser_mp4(raw, fps=write_fps)
        if converted and converted.exists():
            if converted.resolve() != final.resolve():
                if final.exists():
                    final.unlink(missing_ok=True)
                converted.replace(final)
            annotated_path = str(final.resolve())
        elif raw.exists():
            # Fallback: keep raw (may not play in Chrome)
            if final.exists():
                final.unlink(missing_ok=True)
            raw.replace(final)
            annotated_path = str(final.resolve())

    if best_preview is not None and preview_out:
        prev_p = Path(preview_out)
        prev_p.parent.mkdir(parents=True, exist_ok=True)
        if cv2.imwrite(str(prev_p), best_preview[1]):
            preview_path = str(prev_p.resolve())
    elif annotated_path and preview_out is None:
        pass

    duration = (total / fps) if fps > 0 and total > 0 else (timeline[-1].time_sec if timeline else 0.0)

    if processed == 0:
        logger.warning("pipeline.detect empty_frames path=%s — no readable frames", path.name)
    else:
        logger.info(
            "pipeline.detect done path=%s frames=%s max_count=%s tracks=%s",
            path.name,
            processed,
            max(counts) if counts else 0,
            len(seen_tracks),
        )

    latest_counts = {z.code: (zone_series[z.code][-1] if zone_series[z.code] else 0) for z in zone_defs}
    zone_areas = {z.code: z.area_m2 for z in zone_defs}
    zone_analytics = compute_zone_analytics(
        samples,
        zone_areas=zone_areas,
        latest_counts=latest_counts,
    )

    zone_summary: dict[str, dict] = {}
    for z in zone_defs:
        series = zone_series.get(z.code, [])
        latest = series[-1] if series else 0
        analytics = zone_analytics.get(z.code, {})
        zone_summary[z.code] = {
            "zone_id": z.id,
            "name": z.name,
            "area_m2": z.area_m2,
            "latest_count": latest,
            "max_count": max(series) if series else 0,
            "avg_count": round(float(np.mean(series)), 3) if series else 0.0,
            "density": analytics.get("density", round(latest / max(z.area_m2, 1e-6), 4)),
            "mean_speed": analytics.get("mean_speed", 0.0),
            "opposing_flow": analytics.get("opposing_flow", 0.0),
            "congestion_index": analytics.get("congestion_index", 0.0),
            "abnormal_motion": analytics.get("abnormal_motion", 0.0),
            "group_cohesion": analytics.get("group_cohesion", 0.0),
            "exit_pressure": analytics.get("exit_pressure", 0.0),
        }

    return VideoDetectionResult(
        engine=det.info.name,
        backend=det.info.backend,
        tracker="centroid-iou",
        fps=round(fps, 3),
        frame_count=total,
        frames_processed=processed,
        frame_stride=stride,
        duration_sec=round(float(duration), 3),
        max_count=max(counts) if counts else 0,
        avg_count=round(float(np.mean(counts)), 3) if counts else 0.0,
        timeline=timeline,
        sample_boxes=sample_boxes,
        zone_summary=zone_summary,
        unique_tracks=len(seen_tracks),
        zone_analytics=zone_analytics,
        annotated_path=annotated_path,
        preview_path=preview_path,
    )


def result_to_dict(result: VideoDetectionResult) -> dict:
    return {
        "engine": result.engine,
        "backend": result.backend,
        "tracker": result.tracker,
        "fps": result.fps,
        "frame_count": result.frame_count,
        "frames_processed": result.frames_processed,
        "frame_stride": result.frame_stride,
        "duration_sec": result.duration_sec,
        "max_count": result.max_count,
        "avg_count": result.avg_count,
        "unique_tracks": result.unique_tracks,
        "zone_summary": result.zone_summary,
        "zone_analytics": result.zone_analytics,
        "timeline": [asdict(p) for p in result.timeline],
        "sample_boxes": result.sample_boxes,
        "annotated_path": result.annotated_path,
        "preview_path": result.preview_path,
    }
