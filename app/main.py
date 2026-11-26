
import sys
from pathlib import Path

import streamlit as st


# Make the project root available for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import predict_credit_risk


# Page configuration
st.set_page_config(
    page_title="Credit Risk Assessment",
    page_icon="📊",
    layout="wide",
)


# Page header
st.title("Credit Risk Assessment Assistant")

st.write(
    "Enter the applicant's financial information "
    "to estimate their credit default risk."
)

st.info(
    "This tool provides a machine-learning risk assessment. "
    "It does not approve or reject loan applications."
)


# Applicant information form
st.header("Applicant Information")

with st.form("applicant_information_form"):

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Personal Information")

        person_age = st.number_input(
            "Age",
            min_value=18,
            max_value=100,
            value=30,
            step=1,
        )

        person_income = st.number_input(
            "Annual Income",
            min_value=1,
            value=75000,
            step=1000,
            help="Use the same currency units as the training dataset.",
        )

        person_home_ownership = st.selectbox(
            "Home Ownership",
            options=[
                "RENT",
                "MORTGAGE",
                "OWN",
                "OTHER",
            ],
        )

        employment_known = st.checkbox(
            "Employment length is known",
            value=True,
        )

        if employment_known:
            person_emp_length = st.number_input(
                "Employment Length (Years)",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.5,
            )
        else:
            person_emp_length = None

        cb_person_cred_hist_length = st.number_input(
            "Credit History Length (Years)",
            min_value=0,
            max_value=100,
            value=5,
            step=1,
        )

    with col2:

        st.subheader("Loan Information")

        loan_intent = st.selectbox(
            "Loan Purpose",
            options=[
                "EDUCATION",
                "MEDICAL",
                "VENTURE",
                "PERSONAL",
                "DEBTCONSOLIDATION",
                "HOMEIMPROVEMENT",
            ],
        )

        loan_amnt = st.number_input(
            "Loan Amount",
            min_value=1,
            value=10000,
            step=500,
        )

        cb_person_default_on_file = st.selectbox(
            "Previous Credit Default on File",
            options=["N", "Y"],
            format_func=lambda value: (
                "No" if value == "N" else "Yes"
            ),
        )

        # Calculate loan percentage automatically
        loan_percent_income = round(
            loan_amnt / person_income,
            2,
        )

        st.caption(
            f"Loan-to-Income Ratio: "
            f"{loan_percent_income:.2f} "
            f"({loan_percent_income:.0%})"
        )

    st.caption(
        "The loan-to-income ratio is calculated automatically "
        "from the loan amount and annual income."
    )

    submitted = st.form_submit_button(
        "Assess Credit Risk",
        type="primary",
    )


# Run the prediction after form submission
if submitted:

    applicant_data = {
        "person_age": person_age,
        "person_income": person_income,
        "person_home_ownership": person_home_ownership,
        "person_emp_length": person_emp_length,
        "loan_intent": loan_intent,
        "loan_amnt": loan_amnt,
        "loan_percent_income": loan_percent_income,
        "cb_person_default_on_file": cb_person_default_on_file,
        "cb_person_cred_hist_length": cb_person_cred_hist_length,
    }

    try:

        with st.spinner("Assessing credit risk..."):

            result = predict_credit_risk(applicant_data)

        st.divider()

        st.header("Credit Risk Assessment Results")

        metric1, metric2, metric3 = st.columns(3)

        with metric1:
            st.metric(
                "Estimated Default Score",
                f"{result['default_probability']:.2%}",
            )

        with metric2:
            st.metric(
                "Predicted Class",
                result["predicted_label"],
            )

        with metric3:
            st.metric(
                "Risk Category",
                result["risk_category"],
            )

        if result["predicted_class"] == 1:
            st.warning(
                "The model identifies this applicant as "
                "Higher Risk."
            )
        else:
            st.success(
                "The model identifies this applicant as "
                "Lower Risk."
            )

        st.caption(
            f"Classification Threshold: "
            f"{result['decision_threshold']:.2f}"
        )

        st.caption(
            "The displayed score is the model's estimate "
            "and has not been independently calibrated. "
            "It is not a lending decision."
        )

    except FileNotFoundError:
        st.error(
            "The trained model file was not found. "
            "Please check the models directory."
        )

    except (ValueError, TypeError) as error:
        st.error(f"Invalid applicant information: {error}")

    except Exception as error:
        st.error(
            f"An unexpected error occurred: {error}"
        )


# Model information
st.divider()

with st.expander("About this assessment"):

    st.write(
        "This application uses an XGBoost classification model "
        "trained on the Credit Risk Dataset."
    )

    st.write(
        "The model uses nine applicant features. "
        "Loan grade and interest rate are intentionally "
        "excluded from the current model."
    )
