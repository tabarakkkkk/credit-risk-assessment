
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from src.validation import validate_applicant_data


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "credit_risk_xgboost.joblib"
)


@lru_cache(maxsize=1)
def load_model_artifact():
    """Load and cache the saved model artifact."""

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Trained model not found at: {MODEL_PATH}"
        )

    artifact = joblib.load(MODEL_PATH)

    required_keys = {"model", "threshold", "features"}

    if not required_keys.issubset(artifact):
        raise ValueError(
            "The saved model artifact is incomplete."
        )

    return artifact


def predict_credit_risk(applicant_data):
    """
    Validate applicant information and predict credit risk.

    Returns:
        dict: Default probability, predicted class,
              predicted label, and risk category.
    """

    # 1. Validate the applicant information
    validated_data = validate_applicant_data(applicant_data)

    # 2. Load the trained model
    artifact = load_model_artifact()

    model = artifact["model"]
    threshold = float(artifact["threshold"])
    features = artifact["features"]

    # 3. Convert the applicant data into a DataFrame
    input_data = pd.DataFrame(
        [validated_data],
        columns=features,
    )

    # 4. Get the estimated probability of default
    default_probability = float(
        model.predict_proba(input_data)[0, 1]
    )

    # 5. Classify the applicant using the saved threshold
    predicted_class = int(
        default_probability >= threshold
    )

    # 6. Assign the corresponding risk category
    predicted_label = (
        "Default" if predicted_class == 1
        else "Non-default"
    )

    risk_category = (
        "Higher Risk" if predicted_class == 1
        else "Lower Risk"
    )

    return {
        "default_probability": round(
            default_probability, 4
        ),
        "predicted_class": predicted_class,
        "predicted_label": predicted_label,
        "risk_category": risk_category,
        "decision_threshold": threshold,
    }
