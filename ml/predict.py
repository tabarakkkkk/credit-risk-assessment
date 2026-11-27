"""Safe prediction boundary for application and service callers."""

from src.predict import predict_credit_risk


def risk_credit_predict(applicant_data):
    try:
        return {"status": "ok", "result": predict_credit_risk(applicant_data)}
    except (TypeError, ValueError, FileNotFoundError) as error:
        return {"status": "error", "message": str(error)}
