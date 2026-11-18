# Literature Review (IEEE / Peer-Reviewed, 2023–2025)

## Comparison Table

| Paper Name | Year | Dataset | Algorithms Used | Features | Architecture | Limitations | Missing Research Gap | Possible Improvement |
|---|---|---|---|---|---|---|---|---|
| Realtime Crowd Monitoring—Estimating Count, Speed and Direction Using Hybridized YOLOv4 (IEEE Access) | 2023 | JHU Crowd | Hybrid YOLOv4 + CBAM + pruning + DeepSORT | Count, speed, direction | Edge-oriented detection + tracking | No multi-horizon risk forecast; no actionable decisions; single-view bias | Cognitive decision support + predictive risk | Add temporal risk model + multi-cam fusion |
| Crowd Multi Prediction: Single Network for Counting, Localization, Anomaly (IEEE ICCE) | 2023 | Crowd counting benchmarks | Multi-task CNN | Count + localization + anomaly | Single shared network | Reactive anomaly only; no venue twin; no resource optimization | Proactive stampede risk + digital twin | Couple with zone graph + evacuation planner |
| A Convolutional Neural Network Approach for Crowd Counting (IEEE ICOSEC) | 2023 | Standard counting sets | CNN regression | Density map / count | End-to-end CNN | Counting only; no motion/risk semantics | Beyond counting → governance | Multi-factor dynamic risk score |
| Integrated Crowd Counting Using IoT, OpenCV and YOLO (IEEE IC-CGU) | 2024 | Custom / live IP camera | YOLOv5 / YOLOv8 / YOLOv8-NAS | Real-time density | IoT + YOLO pipeline | Detection-centric; no forecasting, XAI, or what-if | Predictive + explainable operations | LSTM/GNN forecast + SHAP attributions |
| Crowd Density Forecasting with Distributed Cameras using Encoder–Decoder LSTM (IEEE I2CACIS) | 2024 | Multi-node camera emulation | Encoder–Decoder LSTM + NN overcount correction | Multi-camera density forecast | Distributed sensing + forecasting | Density-only; no decision engine / twin / GenAI reports | Closed-loop authority actions | Fuse risk, decisions, simulation |
| Heterogeneous Dual-Attentional Network for WiFi–Video Crowd Counting (IEEE TMC) | 2024 | Real multi-modal deployments | Dual attention fusion (WiFi + video) | Large-area counting stability | Multi-modal sensing | Sensing fusion ≠ operational twin; limited risk semantics | Operational digital twin + risk governance | Zone twin + resource optimizer |
| Advancing Urban Evacuation via Cloud Big Data & IoT (IEEE CONIT) | 2024 | Stadium case study | IoT + MQTT + Kafka + Spark risk scoring | Exit risk scores | Cloud streaming | Sensor-heavy; weak vision forecasting & XAI | Vision-native predictive twin | CV + GNN flow + explainable alerts |
| A Novel AI-Based Predictive Crowd Monitoring and Stampede Prevention (IEEE GIEST) | 2025 | Conceptual / CCTV-drone grids | YOLOv8 + LSTM (≤2 min horizon) | Density grid forecast + graded alerts | Detection → LSTM → alerts | Short horizon; no multi-cam anti-double-count; no what-if / GenAI / resource opt | 5–10 min multi-factor risk + decisions | Extend horizon + decision DSL + twin |
| Toward an Integrated Intelligent Framework for Crowd Control (IICCM) (IEEE Access) | 2025 | Hajj-oriented scenarios | CV + AI + IoT | Tracking, behavior, evacuation planning | Integrated control framework | Broad framework; limited unified XAI + what-if + GenAI reports | End-to-end explainable cognitive twin | Implement closed-loop VigilantTwin stack |
| STDCformer: Spatial–Temporal Causal De-Confounding Transformer for Crowd Flow (Information Fusion) | 2025 | Crowd/traffic ST datasets | Transformer + causal de-confounding | Crowd flow prediction | ST encoder–decoder Transformer | Research model; not ops platform | Production decision twin | Embed as forecast backbone in ops system |
| Smart Building Evacuation Multi-Camera + Explainable Re-ID (Eng. Appl. AI) | 2025 | Custom Re-ID + drill | Detection + tracking + attention Re-ID | Multi-cam identity continuity | Multi-camera Re-ID network | Evacuation monitoring; not predictive venue risk twin | Predictive risk + decision support | Add risk forecast + action engine |
| Predicting & Optimizing Crowd Evacuations with XAI (Computer Animation & Virtual Worlds) | 2025 | BioCrowds simulations | MLP + SHAP | Evacuation time/density prediction | Simulation → XAI recommendations | Offline architectural advice, not live CCTV twin | Live what-if on real streams | Online scenario planner on live twin |
| D-Shield: Digital Twin Stampede Hazard Identification | 2025 | Edge + twin prototypes | Edge perception + digital twin | Hazard ID via twin | Edge → twin | Limited cognitive decisions / GenAI / multi-horizon fusion | Full cognitive governance loop | Add DSS + reports + resource OR |
| Dual-Metric Stampede Risk (YOLOv11 + Optical Flow Chaos Score) | 2025 | Live video / custom | YOLOv11 + optical flow | Density + chaos dual threshold | Analyzer + FastAPI dashboard | Binary thresholds; weak multi-factor & forecast | Multi-factor dynamic risk + forecast | Composite risk with XAI |

---

## Cross-Cutting Findings

Most 2023–2025 systems optimize **perception** (YOLO counting/tracking) or **isolated forecasting**. Few close the loop from **multi-camera perception → multi-horizon risk → explainable decisions → digital twin → what-if → resource optimization → GenAI after-action reports**.

---

## Unsolved Research Gaps (Targeted by VigilantTwin)

1. **Reactive vs predictive**: Alerts fire after density/chaos thresholds; 5–10 minute multi-factor risk foresight is rare in operational stacks.
2. **Detection without decisions**: Systems say “High Density”; they rarely recommend gate/PA/guard/route actions via a formal decision engine.
3. **Fragmented twins**: Digital twins exist, but rarely fuse anti-double-count multi-cam analytics with live risk coloring and predictive heatmaps.
4. **Opaque alerts**: Few production systems attach causal feature attributions to every risk score.
5. **No closed-loop simulation**: What-if (exit closure, weather, VIP) on a live twin is uncommon.
6. **Missing resource OR**: Police/medical/evac routing rarely co-optimized with predicted congestion.
7. **Weak historical learning**: Recurring hotspot analytics across events are underused for recommendations.
8. **No GenAI after-action**: Automated IEEE-style incident PDFs with timeline + risk graphs are largely absent.
9. **Edge–cloud gap**: Papers show either edge detection or cloud analytics, seldom a clean scalable split with shared zone ontology.
10. **Single-metric risk**: Density-only or density+chaos; missing composite scores (speed drop, opposing flow, exits, weather, history, emergencies).
