
import math

from src.preprocessing import (
    FEATURES,
    NUMERICAL_FEATURES,
)


ALLOWED_CATEGORIES = {
    "person_home_ownership": {
        "RENT",
        "MORTGAGE",
        "OWN",
        "OTHER",
    },
    "loan_intent": {
        "EDUCATION",
        "MEDICAL",
        "VENTURE",
        "PERSONAL",
        "DEBTCONSOLIDATION",
        "HOMEIMPROVEMENT",
    },
    "cb_person_default_on_file": {
        "Y",
        "N",
    },
}


def validate_applicant_data(applicant_data):
    """
    Validate and normalize applicant information.

    Returns:
        dict: Validated applicant data in the expected format.

    Raises:
        TypeError: If the input is not a dictionary.
        ValueError: If required fields or values are invalid.
    """

    if not isinstance(applicant_data, dict):
        raise TypeError("Applicant data must be a dictionary.")

    # Check missing and unexpected fields
    missing_fields = set(FEATURES) - set(applicant_data)
    extra_fields = set(applicant_data) - set(FEATURES)

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {sorted(missing_fields)}"
        )

    if extra_fields:
        raise ValueError(
            f"Unexpected fields: {sorted(extra_fields)}"
        )

    validated = {}

    # Validate numerical features
    for field in NUMERICAL_FEATURES:

        value = applicant_data[field]

        # Employment length can be missing because
        # our preprocessing pipeline handles missing values.
        if field == "person_emp_length" and (
            value is None
            or (
                isinstance(value, str)
                and not value.strip()
            )
        ):
            validated[field] = float("nan")
            continue

        if isinstance(value, bool):
            raise ValueError(
                f"{field} must be a numeric value."
            )

        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{field} must be a numeric value."
            )

        if math.isnan(number):
            if field == "person_emp_length":
                validated[field] = float("nan")
                continue

            raise ValueError(
                f"{field} cannot be missing."
            )

        if not math.isfinite(number):
            raise ValueError(
                f"{field} must be a finite number."
            )

        validated[field] = number

    # Validate integer-valued features
    integer_fields = [
        "person_age",
        "person_income",
        "loan_amnt",
        "cb_person_cred_hist_length",
    ]

    for field in integer_fields:
        if not validated[field].is_integer():
            raise ValueError(
                f"{field} must be a whole number."
            )

        validated[field] = int(validated[field])

    # Validate numerical ranges
    if not 18 <= validated["person_age"] <= 100:
        raise ValueError(
            "person_age must be between 18 and 100."
        )

    if validated["person_income"] <= 0:
        raise ValueError(
            "person_income must be greater than zero."
        )

    if not 0 <= validated["loan_percent_income"] <= 1:
        raise ValueError(
            "loan_percent_income must be between 0 and 1."
        )

    if not math.isnan(validated["person_emp_length"]):
        employment_length = validated["person_emp_length"]

        if not 0 <= employment_length <= validated["person_age"]:
            raise ValueError(
                "Employment length must be between zero and age."
            )

    if validated["loan_amnt"] <= 0:
        raise ValueError(
            "loan_amnt must be greater than zero."
        )

    if not 0 <= validated["loan_percent_income"] <= 1:
        raise ValueError(
            "loan_percent_income must be between 0 and 1."
        )

    if not 0 <= validated["cb_person_cred_hist_length"] <= validated["person_age"]:
        raise ValueError(
            "Credit history length must be between zero and age."
        )

    # Validate categorical features
    for field, allowed_values in ALLOWED_CATEGORIES.items():

        value = applicant_data[field]

        if not isinstance(value, str):
            raise ValueError(
                f"{field} must be a text value."
            )

        normalized_value = value.strip().upper()

        if normalized_value not in allowed_values:
            raise ValueError(
                f"Invalid value for {field}: {value}"
            )

        validated[field] = normalized_value

    return validated
