
from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "credit_risk_cleaned.csv"

TARGET = "loan_status"

NUMERICAL_FEATURES = [
    "person_age",
    "person_income",
    "person_emp_length",
    "loan_amnt",
    "loan_int_rate",
    "loan_percent_income",
    "cb_person_cred_hist_length",
]

CATEGORICAL_FEATURES = [
    "person_home_ownership",
    "loan_intent",
    "cb_person_default_on_file",
]

FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def split_data():
    df = pd.read_csv(DATA_PATH)

    X = df[FEATURES]
    y = df[TARGET]

    return train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )


def build_preprocessor():

    numerical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_pipeline, NUMERICAL_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    return preprocessor


def main():
    X_train, X_test, y_train, y_test = split_data()

    preprocessor = build_preprocessor()

    # Learn preprocessing parameters from training data only
    X_train_processed = preprocessor.fit_transform(X_train)

    # Apply the learned transformations to testing data
    X_test_processed = preprocessor.transform(X_test)

    print("PREPROCESSING SUMMARY")
    print("-" * 35)

    print(f"Training shape before: {X_train.shape}")
    print(f"Testing shape before: {X_test.shape}")

    print(f"Training shape after: {X_train_processed.shape}")
    print(f"Testing shape after: {X_test_processed.shape}")

    print(
        "\nNumber of generated features:",
        len(preprocessor.get_feature_names_out())
    )

    print("\nPreprocessing completed successfully!")


if __name__ == "__main__":
    main()
