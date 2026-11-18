# Dynamic Crowd Risk Score (DCRS)

## Objective

Predict zone risk 5–10 minutes ahead using multi-factor signals, not density alone.

## Features φ_i

| Feature | Definition | Range |
|---|---|---|
| `density_norm` | persons/m² / capacity_density | [0, 2+] |
| `speed_drop` | 1 − v_t / v_baseline | [0, 1] |
| `opposing_flow` | cosine conflict of bidirectional flow | [0, 1] |
| `group_cohesion` | clustering coefficient of local tracks | [0, 1] |
| `abnormal_motion` | optical-flow / track jerk anomaly score | [0, 1] |
| `exit_pressure` | queue_length / exit_throughput | [0, 2+] |
| `weather_factor` | rainfall/heat penalty | [0, 1] |
| `time_prior` | event-phase prior (ingress/egress/peak) | [0, 1] |
| `historical_hotspot` | empirical P(congestion\|zone,phase) | [0, 1] |
| `emergency_flag` | binary active incident | {0,1} |
| `forecast_surge` | predicted Δdensity over horizon | [0, 2+] |

## Score

```
logit = b + Σ w_i · clip(φ_i)
DCRS = 100 · sigmoid(logit)
```

Default weights (tunable via calibration on venue history):

```
w_density=1.4, w_speed_drop=1.1, w_opposing=1.2, w_exit=1.3,
w_forecast=1.5, w_abnormal=1.0, w_history=0.6, w_weather=0.5,
w_time=0.4, w_group=0.3, w_emergency=2.0
```

## Decision Rule

- Persist DCRS every 5s per zone
- Raise alert if `DCRS >= 60` OR `forecast_DCRS(t+10m) >= 60`
- Attach ERA: top-k positive feature contributions

## Calibration

Isotonic regression on labeled near-miss / incident windows per venue.
