
from pathlib import Path

import pandas as pd


RAW_DATA_PATH = Path("data/raw/credit_risk_dataset.csv")
PROCESSED_DATA_PATH = Path("data/processed/credit_risk_cleaned.csv")


def clean_data():
    df = pd.read_csv(RAW_DATA_PATH)

    original_rows = len(df)

    # Remove exact duplicate rows
    duplicate_count = df.duplicated().sum()
    df = df.drop_duplicates().copy()

    # Remove records with implausible ages
    invalid_age_mask = df["person_age"] > 100
    invalid_age_count = invalid_age_mask.sum()
    df = df.loc[~invalid_age_mask].copy()

    # Replace impossible employment lengths with missing values
    invalid_emp_mask = df["person_emp_length"] > df["person_age"]
    invalid_emp_count = invalid_emp_mask.sum()
    df.loc[invalid_emp_mask, "person_emp_length"] = float("nan")

    # Save cleaned data separately
    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DATA_PATH, index=False)

    print("DATA CLEANING SUMMARY")
    print("-" * 35)
    print(f"Original rows: {original_rows}")
    print(f"Duplicate rows removed: {duplicate_count}")
    print(f"Invalid-age rows removed: {invalid_age_count}")
    print(f"Invalid employment values corrected: {invalid_emp_count}")
    print(f"Final rows: {len(df)}")

    print("\nMissing values after cleaning:")
    print(df.isnull().sum())

    print(f"\nSaved to: {PROCESSED_DATA_PATH}")


if __name__ == "__main__":
    clean_data()
