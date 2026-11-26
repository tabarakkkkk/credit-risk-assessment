
import pytest

from src.predict import predict_credit_risk


VALID_APPLICANT = {
    "person_age": 30,
    "person_income": 75000,
    "person_home_ownership": "RENT",
    "person_emp_length": 5,
    "loan_intent": "PERSONAL",
    "loan_amnt": 10000,
    "loan_percent_income": 0.13,
    "cb_person_default_on_file": "N",
    "cb_person_cred_hist_length": 5,
}


def test_prediction_returns_expected_fields():
    result = predict_credit_risk(VALID_APPLICANT)

    expected_fields = {
        "default_probability",
        "predicted_class",
        "predicted_label",
        "risk_category",
        "decision_threshold",
    }

    assert set(result.keys()) == expected_fields


def test_probability_is_between_zero_and_one():
    result = predict_credit_risk(VALID_APPLICANT)

    assert 0 <= result["default_probability"] <= 1


def test_prediction_matches_threshold():
    result = predict_credit_risk(VALID_APPLICANT)

    expected_class = int(
        result["default_probability"]
        >= result["decision_threshold"]
    )

    assert result["predicted_class"] == expected_class


def test_prediction_labels_are_consistent():
    result = predict_credit_risk(VALID_APPLICANT)

    if result["predicted_class"] == 1:
        assert result["predicted_label"] == "Default"
        assert result["risk_category"] == "Higher Risk"
    else:
        assert result["predicted_label"] == "Non-default"
        assert result["risk_category"] == "Lower Risk"


def test_invalid_applicant_is_rejected():
    applicant = VALID_APPLICANT.copy()
    applicant["person_income"] = -5000

    with pytest.raises(ValueError):
        predict_credit_risk(applicant)
