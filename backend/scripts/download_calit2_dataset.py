"""Download and parse UCI Machine Learning Repository CalIt2 Building People Counter.

UCI Dataset Citation:
- Name: CalIt2 Building People Counts
- Official Source: UCI Machine Learning Repository (ID 156 / 178)
- URL: https://archive.ics.uci.edu/dataset/156/calit2+building+people+counts
- Authors: Jon Hutchins, Alexander Ihler, Padhraic Smyth (UC Irvine)
- Description: 10,080 continuous half-hour observations of pedestrian flow (inflow/outflow)
  recorded by video/optical sensors over 15 weeks, with 30 ground-truth crowd surge events.
"""

from __future__ import annotations

import csv
from datetime import datetime
import io
from pathlib import Path
import urllib.request
import zipfile

UCI_URL = "https://archive.ics.uci.edu/static/public/156/calit2+building+people+counts.zip"
BASE_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = BASE_DIR / "data" / "datasets"
TARGET_DIR = DATASETS_DIR / "calit2"
OUT_CSV = DATASETS_DIR / "calit2_people_counter.csv"
OUT_EVENTS_CSV = DATASETS_DIR / "calit2_events.csv"


def download_and_extract() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TARGET_DIR / "calit2.zip"

    if (TARGET_DIR / "CalIt2.data").exists() and (TARGET_DIR / "CalIt2.events").exists():
        print(f"[CACHE] CalIt2 dataset already extracted in {TARGET_DIR}")
        return

    print(f"[DOWNLOAD] Fetching CalIt2 from UCI ML Repository: {UCI_URL}...")
    req = urllib.request.Request(UCI_URL, headers={"User-Agent": "CrowdPulse-Benchmark/1.0"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()

    print(f"[DOWNLOAD] Received {len(content)} bytes. Extracting...")
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        zf.extractall(TARGET_DIR)
    print(f"[EXTRACT] Extracted files: {[p.name for p in TARGET_DIR.iterdir()]}")


def parse_events(events_path: Path) -> list[dict]:
    """Parse CalIt2.events containing ground truth surge events."""
    events = []
    if not events_path.exists():
        return events

    with open(events_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                # date, start_time, end_time, event_name
                events.append({
                    "date": parts[0],
                    "start_time": parts[1],
                    "end_time": parts[2],
                    "description": ",".join(parts[3:]),
                })
    return events


def parse_data(data_path: Path, events: list[dict]) -> int:
    """Parse CalIt2.data: Flow_ID (7=out, 9=in), Date, Time, Count."""
    print(f"[PARSE] Processing {data_path.name}...")
    
    # Store by (date_str, time_str) -> {inflow: 0, outflow: 0}
    time_slices: dict[tuple[str, str], dict[str, int]] = {}

    with open(data_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 4:
                continue
            flow_id = parts[0]
            date_str = parts[1]
            time_str = parts[2]
            count = int(parts[3])

            key = (date_str, time_str)
            if key not in time_slices:
                time_slices[key] = {"inflow": 0, "outflow": 0}

            if flow_id == "9":
                time_slices[key]["inflow"] = count
            elif flow_id == "7":
                time_slices[key]["outflow"] = count

    # Build event interval lookup: date -> list of (start_t, end_t)
    event_lookup: dict[str, list[tuple[str, str]]] = {}
    for ev in events:
        d = ev["date"]
        event_lookup.setdefault(d, []).append((ev["start_time"], ev["end_time"]))

    # Sort chronological
    rows = []
    occupancy = 0

    for (date_str, time_str), counts in time_slices.items():
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%y %H:%M:%S")
            iso_ts = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            iso_ts = f"{date_str} {time_str}"

        inf = counts["inflow"]
        outf = counts["outflow"]
        net = inf - outf
        occupancy = max(0, occupancy + net)

        # Check if inside an active surge event
        is_surge = False
        day_events = event_lookup.get(date_str, [])
        for start_t, end_t in day_events:
            if start_t <= time_str <= end_t:
                is_surge = True
                break

        rows.append({
            "timestamp": iso_ts,
            "date": date_str,
            "time": time_str,
            "inflow": inf,
            "outflow": outf,
            "net_flow": net,
            "estimated_occupancy": occupancy,
            "is_surge_event": 1 if is_surge else 0,
        })

    # Write unified CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp", "date", "time", "inflow", "outflow",
            "net_flow", "estimated_occupancy", "is_surge_event"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Write events CSV
    with open(OUT_EVENTS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["date", "start_time", "end_time", "description"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

    print(f"[EXPORT] Generated {OUT_CSV.name} with {len(rows)} chronological time-slices.")
    print(f"[EXPORT] Generated {OUT_EVENTS_CSV.name} with {len(events)} surge events.")
    return len(rows)


def main():
    download_and_extract()
    events = parse_events(TARGET_DIR / "CalIt2.events")
    parse_data(TARGET_DIR / "CalIt2.data", events)
    print("\n[SUCCESS] UCI CalIt2 People Counter dataset ingested and ready for CrowdPulse!")


if __name__ == "__main__":
    main()
