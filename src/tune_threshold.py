
import pandas as pd

from sklearn.metrics import (
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from xgboost import XGBClassifier

from src.preprocessing import build_preprocessor, split_data


def evaluate_threshold(y_true, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(int)

    return {
        "Threshold": threshold,
        "Precision": precision_score(
            y_true, predictions, zero_division=0
        ),
        "Recall": recall_score(
            y_true, predictions, zero_division=0
        ),
        "F1": f1_score(
            y_true, predictions, zero_division=0
        ),
        "Predicted Defaults": int(predictions.sum()),
    }


def tune_threshold():
    # Get the original training data.
    # The separate test set is not used here.
    X_train, _, y_train, _ = split_data()

    # Create a validation split from training data.
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train,
        y_train,
        test_size=0.20,
        random_state=42,
        stratify=y_train,
    )

    # Calculate class imbalance using fitting data only.
    scale_pos_weight = (
        (y_fit == 0).sum() / (y_fit == 1).sum()
    )

    # Build the same XGBoost configuration.
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

    # Train on the fitting subset.
    model.fit(X_fit, y_fit)

    # Get default probabilities for the validation subset.
    probabilities = model.predict_proba(X_val)[:, 1]

    # Compare selected thresholds.
    thresholds_to_check = [0.30, 0.40, 0.50, 0.60, 0.70]

    results = [
        evaluate_threshold(y_val, probabilities, threshold)
        for threshold in thresholds_to_check
    ]

    results_df = pd.DataFrame(results)

    print("THRESHOLD COMPARISON - VALIDATION SET")
    print("=" * 60)
    print(results_df.round(4).to_string(index=False))

    # Find the threshold that maximizes validation F1.
    precision, recall, thresholds = precision_recall_curve(
        y_val,
        probabilities,
    )

    f1_scores = (
        2 * precision[:-1] * recall[:-1]
        / (precision[:-1] + recall[:-1] + 1e-10)
    )

    best_index = f1_scores.argmax()
    best_threshold = thresholds[best_index]

    print("\nBEST F1 THRESHOLD ON VALIDATION SET")
    print("-" * 45)

    best_result = evaluate_threshold(
        y_val,
        probabilities,
        best_threshold,
    )

    for metric, value in best_result.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")


if __name__ == "__main__":
    tune_threshold()
