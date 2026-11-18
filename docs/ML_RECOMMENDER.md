# Decision Intelligence — Which Algorithm & Why

## Benchmark result (CrowdPulse action recommendation)

Test setup: 3000 synthetic multi-factor crowd-risk samples, 75/25 split.

| Model | F1-micro | Exact Match | Inference | Windows reliability |
|---|---|---|---|---|
| **Gradient Boosting** | **0.9983** | **0.9907** | very fast | excellent (sklearn) |
| Random Forest | 0.9974 | 0.9853 | fast | excellent |
| HistGradientBoosting | 0.9971 | 0.9840 | fast | excellent |

## Selected for CrowdPulse

**Gradient Boosting Classifier (scikit-learn)** as multi-label action recommender.

### Why this one
1. Highest accuracy in our benchmark
2. Built into scikit-learn → project runs reliably on Windows laptops
3. Gives confidence score per action
4. Easy to explain in viva
5. No XGBoost/LightGBM install pain

### Why not only rules
Rules alone are weak for major-project evaluation.  
Gradient Boosting learns action patterns from risk features.

### Why not deep learning here
For tabular recommendation features, boosting is usually more accurate and more stable than a neural net for this project size.

## Viva answer

> We compared Random Forest and Gradient Boosting for action recommendation.  
> Gradient Boosting gave the best F1 and exact-match accuracy, so CrowdPulse uses Gradient Boosting to decide recommendations.  
> A safety layer only blocks unsafe actions such as closing the last exit.

## Run benchmark again

```bash
cd backend
python scripts/benchmark_recommender.py
```
