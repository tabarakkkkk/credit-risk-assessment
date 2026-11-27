
import math

import pytest

from src.validation import validate_applicant_data


VALID_APPLICANT = {
    "person_age": 30,
    "person_income": 75000,
    "person_home_ownership": "RENT",
    "person_emp_length": 5,
    "loan_intent": "PERSONAL",
    "loan_amnt": 10000,
    "loan_int_rate": 10.5,
    "loan_percent_income": 0.13,
    "cb_person_default_on_file": "N",
    "cb_person_cred_hist_length": 5,
}


def test_valid_applicant_is_accepted():
    result = validate_applicant_data(VALID_APPLICANT)

    assert result["person_age"] == 30
    assert result["person_income"] == 75000


def test_categorical_values_are_normalized():
    applicant = VALID_APPLICANT.copy()
    applicant["person_home_ownership"] = " rent "

    result = validate_applicant_data(applicant)

    assert result["person_home_ownership"] == "RENT"


def test_zero_loan_percent_income_is_accepted():
    applicant = VALID_APPLICANT.copy()
    applicant["loan_percent_income"] = 0.0

    result = validate_applicant_data(applicant)

    assert result["loan_percent_income"] == 0.0


def test_missing_employment_length_is_allowed():
    applicant = VALID_APPLICANT.copy()
    applicant["person_emp_length"] = None

    result = validate_applicant_data(applicant)

    assert math.isnan(result["person_emp_length"])


def test_missing_required_field_is_rejected():
    applicant = VALID_APPLICANT.copy()
    del applicant["person_income"]

    with pytest.raises(ValueError):
        validate_applicant_data(applicant)


def test_unexpected_field_is_rejected():
    applicant = VALID_APPLICANT.copy()
    applicant["unknown_field"] = 100

    with pytest.raises(ValueError):
        validate_applicant_data(applicant)


def test_invalid_age_is_rejected():
    applicant = VALID_APPLICANT.copy()
    applicant["person_age"] = 144

    with pytest.raises(ValueError):
        validate_applicant_data(applicant)


def test_negative_income_is_rejected():
    applicant = VALID_APPLICANT.copy()
    applicant["person_income"] = -5000

    with pytest.raises(ValueError):
        validate_applicant_data(applicant)


def test_employment_length_greater_than_age_is_rejected():
    applicant = VALID_APPLICANT.copy()
    applicant["person_emp_length"] = 40

    with pytest.raises(ValueError):
        validate_applicant_data(applicant)


def test_invalid_home_ownership_is_rejected():
    applicant = VALID_APPLICANT.copy()
    applicant["person_home_ownership"] = "UNKNOWN"

    with pytest.raises(ValueError):
        validate_applicant_data(applicant)
