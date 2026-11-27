# Credit-risk model metrics

Model artifact: `models/credit_risk_xgboost.joblib`

Dataset: `data/raw/credit_risk_dataset.csv` after duplicate removal and validation cleaning.

Split: stratified 80/20 train/test split with `random_state=42`.

| Metric | Test result |
|---|---:|
| Accuracy | 0.8994 |
| Precision | 0.7588 |
| Recall | 0.7920 |
| F1 | 0.7750 |
| ROC-AUC | 0.9352 |

The current model exceeds the initial ROC-AUC target of 0.85. The saved artifact contains the full preprocessing and classifier pipeline, the feature schema, target name, and decision threshold.
