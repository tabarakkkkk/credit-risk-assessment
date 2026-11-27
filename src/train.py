
from pathlib import Path

import joblib

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from xgboost import XGBClassifier

from src.preprocessing import (
    FEATURES,
    TARGET,
    build_preprocessor,
    split_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "credit_risk_xgboost.joblib"
DECISION_THRESHOLD = 0.50


def train_and_save_model():

    # Load the existing training and testing split
    X_train, X_test, y_train, y_test = split_data()

    # Calculate class imbalance using training data
    scale_pos_weight = (
        (y_train == 0).sum() / (y_train == 1).sum()
    )

    # Build the complete preprocessing and ML pipeline
    model = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=300,
                    max_depth=5,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    scale_pos_weight=scale_pos_weight,
                    objective="binary:logistic",
                    eval_metric="logloss",
                    tree_method="hist",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    # Train on the complete training set
    model.fit(X_train, y_train)

    # Evaluate on the held-out test set
    probabilities = model.predict_proba(X_test)[:, 1]

    predictions = (
        probabilities >= DECISION_THRESHOLD
    ).astype(int)

    print("FINAL MODEL EVALUATION")
    print("=" * 45)

    print(f"Threshold: {DECISION_THRESHOLD}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
    print(
        f"Precision: "
        f"{precision_score(y_test, predictions):.4f}"
    )
    print(f"Recall: {recall_score(y_test, predictions):.4f}")
    print(f"F1-score: {f1_score(y_test, predictions):.4f}")
    print(f"ROC-AUC: {roc_auc_score(y_test, probabilities):.4f}")

    print("\nCONFUSION MATRIX:")
    print(confusion_matrix(y_test, predictions))

    print("\nCLASSIFICATION REPORT:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=["Non-default", "Default"],
            zero_division=0,
        )
    )

    # Store the complete model package
    artifact = {
        "model": model,
        "threshold": DECISION_THRESHOLD,
        "features": FEATURES,
        "target": TARGET,
        "model_name": "XGBoost",
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(artifact, MODEL_PATH)

    print("\nMODEL SAVED SUCCESSFULLY")
    print(f"Path: {MODEL_PATH}")
    print(
        f"File size: "
        f"{MODEL_PATH.stat().st_size / (1024 * 1024):.2f} MB"
    )


if __name__ == "__main__":
    train_and_save_model()
