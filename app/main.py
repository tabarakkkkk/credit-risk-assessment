import hashlib
import hmac
import json
import os
import random
import re
import secrets
import sqlite3
import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.predict import predict_credit_risk
from app.services.service_agent import ask_agent
from app.repositories.application_repository import ApplicationRepository

st.set_page_config(page_title="CreditLens", page_icon=":material/insights:", layout="wide", initial_sidebar_state="expanded")
DB = ROOT / "data" / "app" / "users.db"
APPLICATIONS = ApplicationRepository(DB)
SEED_EMAIL = os.getenv("CREDITLENS_SEEDED_EMAIL", "analyst@creditlens.local")
SEED_PASSWORD = os.getenv("CREDITLENS_SEEDED_PASSWORD", "CreditLens@2026")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def database():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS users(email TEXT PRIMARY KEY,name TEXT NOT NULL,salt BLOB NOT NULL,password_hash BLOB NOT NULL,created REAL NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,email TEXT NOT NULL,created REAL NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT NOT NULL,created REAL NOT NULL,payload TEXT NOT NULL,result TEXT NOT NULL)")
    return con

def hashed(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)

def seed_account():
    with database() as con:
        if con.execute("SELECT 1 FROM users WHERE email=?", (SEED_EMAIL.lower(),)).fetchone() is None:
            salt=os.urandom(16); con.execute("INSERT INTO users VALUES(?,?,?,?,?)", (SEED_EMAIL.lower(),"Credit analyst",salt,hashed(SEED_PASSWORD,salt),time.time()))

def authenticate(email,password):
    with database() as con: row=con.execute("SELECT name,salt,password_hash FROM users WHERE email=?",(email.lower(),)).fetchone()
    if row and hmac.compare_digest(hashed(password,row[1]),row[2]): return {"name":row[0],"email":email.lower()}
    return None

def create_session(email):
    token=secrets.token_urlsafe(32)
    token_hash=hashlib.sha256(token.encode()).hexdigest()
    with database() as con: con.execute("INSERT OR REPLACE INTO sessions VALUES(?,?,?)",(token_hash,email.lower(),time.time()))
    return token

def session_user(token):
    token_hash=hashlib.sha256(token.encode()).hexdigest()
    with database() as con: row=con.execute("SELECT users.name,users.email FROM sessions JOIN users ON users.email=sessions.email WHERE sessions.token_hash=?",(token_hash,)).fetchone()
    return {"name":row[0],"email":row[1]} if row else None

def delete_session(token):
    token_hash=hashlib.sha256(token.encode()).hexdigest()
    with database() as con: con.execute("DELETE FROM sessions WHERE token_hash=?",(token_hash,))

def create_user(name,email,password):
    salt=os.urandom(16)
    try:
        with database() as con: con.execute("INSERT INTO users VALUES(?,?,?,?,?)",(email.lower(),name,salt,hashed(password,salt),time.time()))
        return True
    except sqlite3.IntegrityError: return False

def update_password(email,password):
    salt=os.urandom(16)
    with database() as con: con.execute("UPDATE users SET salt=?,password_hash=? WHERE email=?",(salt,hashed(password,salt),email.lower()))

def password_issue(password):
    if len(password)<8:return "Use at least 8 characters."
    if not re.search(r"[A-Za-z]",password) or not re.search(r"\d",password):return "Include letters and numbers."
    return None

def init_state():
    for key,value in {"user":None,"auth_view":"signin","page":"Applicant form","step":1,"application":{},"assessment":None,"reset_code":None,"reset_email":None}.items(): st.session_state.setdefault(key,value)
    token=st.query_params.get("session")
    if st.session_state.user is None and token:
        st.session_state.user=session_user(token)

def auth_view(view):
    st.session_state.auth_view=view; st.session_state.reset_code=None; st.session_state.reset_email=None

def styles():
    st.markdown("""<style>
    :root{--ink:#173b37;--muted:#58716a;--green:#2f6b55;--green-dark:#245440;--line:#d6e2db;--page:#f4f7f5}
    html,body,.stApp{color:var(--ink)!important;background:var(--page)!important;color-scheme:light}.block-container{max-width:1180px;padding-top:1.5rem;padding-bottom:2rem}[data-testid=stHeader],#MainMenu,footer{display:none}.rail-subtitle{color:var(--muted);font-size:11px;margin:7px 0 24px 37px}.rail-label{color:var(--muted);font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin:25px 0 8px}.stButton>button{min-height:44px}
    .brand{color:var(--ink);font-size:19px;font-weight:750}.mark{display:inline-grid;place-items:center;width:29px;height:29px;margin-right:8px;border-radius:50%;background:var(--green);color:#fff;vertical-align:-5px}.auth-title{color:var(--ink);font-size:34px;font-weight:750;letter-spacing:-1px;margin:64px 0 8px}.auth-subtitle{color:var(--muted);font-size:14px;margin-bottom:26px}.auth-side{min-height:690px;padding:54px 12%;border-radius:18px;background:linear-gradient(145deg,#d9ebdc,#c3e0d0)}.auth-side h2{color:#123b39;font-size:42px;line-height:1.03;letter-spacing:-1.6px;margin:68px 0 14px}.auth-side p{max-width:380px;color:#416c5a;line-height:1.55}.side-line{margin-top:42px;padding-left:14px;border-left:3px solid var(--green);color:var(--ink)}
    .chat-subtitle{color:var(--muted);font-size:14px;margin-top:-10px;margin-bottom:22px}.chat-shell{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px 22px 16px;box-shadow:0 8px 24px rgba(23,59,55,.05)}.chat-window{min-height:340px;max-height:470px;overflow-y:auto;padding:4px 2px 18px}.chat-bubble{max-width:78%;padding:13px 16px;border-radius:14px;margin:10px 0;line-height:1.5;font-size:14px}.chat-bubble.assistant{background:#f0f6f1;color:var(--ink);border:1px solid #e0ebe2;border-top-left-radius:5px}.chat-bubble.user{background:var(--green);color:#fff;margin-left:auto;border-top-right-radius:5px}.chat-bubble.user *{color:#fff!important}.chat-suggestions{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 14px}.chat-hint{color:var(--muted);font-size:12px;margin-top:10px}
    [data-testid=stForm]{border:0;padding:0;background:transparent}label p,[data-testid=stWidgetLabel] p{color:var(--ink)!important;font-size:12px!important;font-weight:650!important}p,li{color:var(--ink)}.stCaption,[data-testid=stCaptionContainer]{color:var(--muted)!important}[data-testid=stTextInput] input,[data-testid=stNumberInput] input{min-height:44px;border:1px solid var(--line);border-radius:8px;background:#fff!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important}[data-testid=stTextInput] input::placeholder{color:#78908a!important;opacity:1}[data-testid=stTextInput] input:focus,[data-testid=stNumberInput] input:focus{border-color:var(--green);box-shadow:0 0 0 3px #dceade}[data-testid=stFormSubmitButton] button{width:100%;min-height:44px;background:var(--green);border:0;border-radius:8px;color:#fff!important;font-weight:700}[data-testid=stFormSubmitButton] button:hover,[data-testid=stFormSubmitButton] button:focus,[data-testid=stFormSubmitButton] button:active{background:var(--green-dark)!important;color:#fff!important}[data-testid=stFormSubmitButton] button:hover p,[data-testid=stFormSubmitButton] button:hover span,[data-testid=stFormSubmitButton] button:focus p,[data-testid=stFormSubmitButton] button:focus span{color:#fff!important}.stButton>button{color:var(--ink);border-color:var(--line);background:#fff}.stButton>button:hover,.stButton>button:focus,.stButton>button:active{color:#fff!important;background:var(--green-dark)!important;border-color:var(--green-dark)!important}.stButton>button:hover p,.stButton>button:hover span,.stButton>button:focus p,.stButton>button:focus span{color:#fff!important}.muted{text-align:center;color:var(--muted);font-size:12px}.workspace-card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:28px}.step-label{color:var(--muted);font-size:12px;font-weight:650;text-transform:uppercase;letter-spacing:.8px}.step-active{color:var(--green);font-weight:750}.progress-line{height:4px;border-radius:4px;background:#dce8df}.progress-fill{height:4px;border-radius:4px;background:var(--green)}.empty-state{padding:50px 24px;text-align:center;border:1px dashed #b8ccc0;color:var(--muted)}
    [data-testid=stSidebar]{background:#fff;border-right:1px solid var(--line)}[data-testid=stSidebar] [data-testid=stSidebarContent]{padding:1.2rem .9rem}.sidebar-rail{margin:1.2rem 0;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:#f2f7f3;color:var(--muted);font-size:11px}.sidebar-rail strong{display:block;color:var(--ink);font-size:12px;margin-bottom:4px}
    @media(max-width:850px){.auth-side{display:none}.auth-title{margin-top:35px}.block-container{padding:1rem}}
    [data-testid=stFormSubmitButton] button p,[data-testid=stFormSubmitButton] button span{color:#fff!important}[data-testid=stFormSubmitButton] button:hover p,[data-testid=stFormSubmitButton] button:hover span{color:#fff!important}
    </style>""",unsafe_allow_html=True)

def auth_page():
    left,right=st.columns([.92,1.08],gap="large")
    with left:
        with st.container(border=True):
            st.markdown("<div class='brand'><span class='mark'>◈</span>CreditLens</div>",unsafe_allow_html=True)
            view=st.session_state.auth_view
            if view=="signin":
                st.markdown("<div class='auth-title'>Welcome back</div><div class='auth-subtitle'>Sign in to continue to your risk workspace.</div>",unsafe_allow_html=True)
                with st.form("signin",border=False):
                    email=st.text_input("Email",placeholder="Enter your work email"); password=st.text_input("Password",placeholder="Enter your password",type="password"); remember=st.checkbox("Remember for 30 days"); submitted=st.form_submit_button("Sign in",width="stretch")
                if submitted:
                    user=authenticate(email,password) if email and password else None
                    if user:
                        st.session_state.user=user
                        if remember: st.query_params["session"]=create_session(user["email"])
                        st.rerun()
                    else: st.error("Email or password is incorrect.")
                st.markdown("<div class='muted' style='margin:22px 0 8px'>Need help signing in?</div>",unsafe_allow_html=True)
                a,b=st.columns(2)
                with a:
                    if st.button("Forgot password",key="forgot",width="stretch"):auth_view("forgot");st.rerun()
                with b:
                    if st.button("Create account",key="signup",width="stretch"):auth_view("signup");st.rerun()
            elif view=="signup":
                st.markdown("<div class='auth-title'>Create your account</div><div class='auth-subtitle'>Create access to the credit risk workspace.</div>",unsafe_allow_html=True)
                with st.form("signup",border=False):
                    name=st.text_input("Full name");email=st.text_input("Work email");password=st.text_input("Password",type="password");confirmation=st.text_input("Confirm password",type="password");accepted=st.checkbox("I agree to handle customer data under company policy");submitted=st.form_submit_button("Create account",width="stretch")
                if submitted:
                    issue=password_issue(password)
                    if not name.strip() or not EMAIL_RE.match(email):st.error("Enter a name and valid email address.")
                    elif issue:st.error(issue)
                    elif password!=confirmation:st.error("Passwords do not match.")
                    elif not accepted:st.error("Accept the data policy to continue.")
                    elif create_user(name.strip(),email,password):st.success("Account created. Sign in to continue.");auth_view("signin");st.rerun()
                    else:st.error("An account with this email already exists.")
                if st.button("Back to sign in",key="back_signin",width="stretch"):auth_view("signin");st.rerun()
            else:
                st.markdown("<div class='auth-title'>Reset password</div><div class='auth-subtitle'>Use a verification code to choose a new password.</div>",unsafe_allow_html=True)
                if st.session_state.reset_code is None:
                    with st.form("request_reset",border=False):email=st.text_input("Email");submitted=st.form_submit_button("Send reset code",width="stretch")
                    if submitted:
                        if not EMAIL_RE.match(email):st.error("Enter a valid email address.")
                        else:st.session_state.reset_email=email.lower();st.session_state.reset_code=f"{random.randint(0,999999):06d}";st.rerun()
                else:
                    st.info(f"Demo reset code: {st.session_state.reset_code}")
                    with st.form("complete_reset",border=False):code=st.text_input("Verification code",max_chars=6);password=st.text_input("New password",type="password");confirmation=st.text_input("Confirm new password",type="password");submitted=st.form_submit_button("Update password",width="stretch")
                    if submitted:
                        issue=password_issue(password)
                        if code!=st.session_state.reset_code:st.error("That verification code is not valid.")
                        elif issue:st.error(issue)
                        elif password!=confirmation:st.error("Passwords do not match.")
                        else:update_password(st.session_state.reset_email,password);auth_view("signin");st.rerun()
                if st.button("Back to sign in",key="back_reset",width="stretch"):auth_view("signin");st.rerun()
    with right:st.markdown("<div class='auth-side'><div class='mark'>◈</div><h2>Credit decisions,<br>made clearer.</h2><p>Review applicant information and understand default risk in one focused workspace.</p><div class='side-line'><strong>Assessment tools ready</strong><br><span style='color:#416c5a;font-size:12px'>Use the model when you are ready to review an application.</span></div></div>",unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        st.markdown("<div class='brand'><span class='mark'>◈</span>CreditLens</div><div style='color:#6a8078;font-size:12px;margin:5px 0 24px 37px'>Risk workspace</div>",unsafe_allow_html=True)
        st.session_state.page=st.radio("Workspace",["Applicant form","Risk assessment","Chatbot"],index=["Applicant form","Risk assessment","Chatbot"].index(st.session_state.page),label_visibility="collapsed")
        st.markdown("<div class='sidebar-rail'><strong>Workspace</strong>Assessment tools and future project sections will appear here.</div>",unsafe_allow_html=True)
        st.divider();st.caption(f"Signed in as {st.session_state.user['name']}")
        if st.button("Sign out",icon=":material/logout:",width="stretch"):
            if st.query_params.get("session"): delete_session(st.query_params.get("session"))
            st.query_params.clear();st.session_state.user=None;st.rerun()

def workspace_layout():
    rail,content=st.columns([.28,.72],gap="small")
    with rail:
        with st.container(border=True):
            st.markdown("<div class='brand'><span class='mark'>◈</span>CreditLens</div><div class='rail-subtitle'>Risk workspace</div><div class='rail-label'>Workspace</div>",unsafe_allow_html=True)
            for option in ["Applicant form","Risk assessment","Application history","Chatbot"]:
                if st.button(option,key=f"rail_{option}",width="stretch",type="primary" if st.session_state.page==option else "secondary"):
                    st.session_state.page=option;st.rerun()
            st.markdown("<div class='rail-label'>Account</div>",unsafe_allow_html=True)
            if st.button("Sign out",key="rail_signout",width="stretch"):
                if st.query_params.get("session"): delete_session(st.query_params.get("session"))
                st.query_params.clear();st.session_state.user=None;st.rerun()
    with content:
        {"Applicant form":applicant_form,"Risk assessment":risk_page,"Application history":history_page,"Chatbot":chatbot_page}[st.session_state.page]()

def progress():
    for index,label in enumerate(["About the applicant","Work and home","The loan"],1):
        with st.columns(3)[index-1]:st.markdown(f"<div class='step-label {'step-active' if index<=st.session_state.step else ''}'>{label}</div><div class='progress-line'><div class='progress-fill' style='width:{'100' if index<=st.session_state.step else '12'}%'></div></div>",unsafe_allow_html=True)

def applicant_form():
    st.title("New loan application")
    if st.session_state.assessment:
        st.caption("This application has been submitted and cannot be edited.")
        with st.container(border=True):
            st.info("To change any information, start a new loan request. The submitted application remains in your history.")
            if st.button("Start a new loan request", type="primary", key="new_request_from_form"):
                st.session_state.application = {}
                st.session_state.assessment = None
                st.session_state.step = 1
                st.rerun()
        return
    st.caption("Three short steps using fields required by the current risk model.");progress();data=st.session_state.application
    with st.container(border=True):
        if st.session_state.step==1:
            st.subheader("About the applicant");a,b,c=st.columns(3);data["full_name"]=a.text_input("Full name",data.get("full_name",""));data["person_age"]=b.number_input("Age",18,100,data.get("person_age",30));data["person_income"]=c.number_input("Yearly income",1,value=data.get("person_income",75000),step=1000)
            if st.button("Next",type="primary"):
                if not data.get("full_name", "").strip():
                    st.error("Full name is required.")
                else:
                    data["full_name"] = data["full_name"].strip()
                    st.session_state.step=2;st.rerun()
        elif st.session_state.step==2:
            st.subheader("Work and home");a,b=st.columns(2);data["person_emp_length"]=a.number_input("Years in current job",0.0,100.0,data.get("person_emp_length",5.0),.5);data["cb_person_cred_hist_length"]=b.number_input("Years of credit history",0,100,data.get("cb_person_cred_hist_length",5));data["person_home_ownership"]=st.pills("Home situation",["RENT","OWN","MORTGAGE","OTHER"],default=data.get("person_home_ownership","RENT"),selection_mode="single") or "RENT";data["cb_person_default_on_file"]=st.pills("Prior default on file",["N","Y"],format_func=lambda v:"No" if v=="N" else "Yes",default=data.get("cb_person_default_on_file","N"),selection_mode="single") or "N";a,b=st.columns(2)
            if a.button("Back"):st.session_state.step=1;st.rerun()
            if b.button("Next",type="primary"):st.session_state.step=3;st.rerun()
        else:
            st.subheader("The loan");data["loan_intent"]=st.pills("Loan purpose",["EDUCATION","MEDICAL","VENTURE","PERSONAL","DEBTCONSOLIDATION","HOMEIMPROVEMENT"],default=data.get("loan_intent","PERSONAL"),selection_mode="single") or "PERSONAL"
            data["loan_amnt"] = st.number_input("Loan amount", min_value=1000, max_value=100000, value=int(data.get("loan_amnt",10000)), step=500)
            data["loan_int_rate"] = st.number_input("Interest rate (%)", min_value=0.0, max_value=30.0, value=float(data.get("loan_int_rate",10.0)), step=0.1, format="%.1f")
            ratio=round(data["loan_amnt"]/data["person_income"],2);st.info(f"This loan is {ratio:.0%} of the applicant's yearly income.");a,b=st.columns(2)
            if a.button("Back"):st.session_state.step=2;st.rerun()
            if b.button("Assess risk",type="primary"):
                model_data={key:data[key] for key in ["person_age","person_income","person_home_ownership","person_emp_length","loan_intent","loan_amnt","loan_int_rate","cb_person_default_on_file","cb_person_cred_hist_length"]};model_data["loan_percent_income"]=ratio
                try:
                    result = predict_credit_risk(model_data)
                    st.session_state.assessment = result
                    APPLICATIONS.save(st.session_state.user["email"], data, result)
                    st.session_state.page="Risk assessment"
                    st.rerun()
                except (ValueError,TypeError,FileNotFoundError) as error:st.error(str(error))

def risk_page():
    st.title("Risk assessment");st.caption("Real model output from the submitted application.");result=st.session_state.assessment;application=st.session_state.application
    if not result:
            with st.container(border=True):
                st.markdown("<div class='empty-state'>Start with a loan application and the result will appear here.</div>",unsafe_allow_html=True)
                if st.button("Open applicant form",type="primary", key="open_applicant_form"):
                    st.session_state.page="Applicant form"
                    st.rerun()
            return
    with st.container(border=True):
        st.subheader("ML prediction")
        score=result["default_probability"]
        score_col,summary_col=st.columns([.42,.58])
        with score_col:
            st.metric("Estimated default probability",f"{score:.2%}")
            st.progress(score, text="Model probability")
            st.caption("Low < 25% · Medium 25–50% · High ≥ 50%")
        with summary_col:
            st.metric("Risk tier",result["risk_tier"])
            st.write(f"Predicted class: **{result['predicted_label']}**")
            st.write(f"Risk category: **{result['risk_category']}**")
    with st.container(border=True):
        st.subheader("Application details")
        left,right=st.columns(2)
        left.write(f"**Applicant age:** {application.get('person_age','—')}")
        left.write(f"**Yearly income:** {application.get('person_income','—')}")
        left.write(f"**Home situation:** {application.get('person_home_ownership','—')}")
        right.write(f"**Loan purpose:** {application.get('loan_intent','—')}")
        right.write(f"**Loan amount:** {application.get('loan_amnt','—')}")
        right.write(f"**Loan-to-income ratio:** {application.get('loan_amnt',0) / application.get('person_income',1):.0%}")
    with st.container(border=True):
        st.subheader("Assessment note")
        st.write("This result is generated by the saved credit-risk model. It is an assessment aid, not an approval or rejection decision.")
    if st.button("Start a new loan request", type="primary", key="new_request_from_result"):
        st.session_state.application = {}
        st.session_state.assessment = None
        st.session_state.step = 1
        st.session_state.page = "Applicant form"
        st.rerun()

def chatbot_page():
    st.title("Ask the assistant")
    st.markdown("<div class='chat-subtitle'>Ask about applicant risk, loan policies, or possible scenarios.</div>", unsafe_allow_html=True)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history=[]
    suggestions=[
        "Check applicant risk",
        "Prior default policy",
        "Required documents",
        "Compare loan amount",
        "Standard DTI range",
    ]
    with st.container(border=True):
        st.markdown("<div class='chat-window'>", unsafe_allow_html=True)
        if not st.session_state.chat_history:
            st.markdown("<div class='chat-bubble assistant'>Hi, I can help check applicant risk and look up lending policies. What do you need?</div>", unsafe_allow_html=True)
        else:
            for message in st.session_state.chat_history:
                role=message["role"]
                text=message["content"]
                st.markdown(f"<div class='chat-bubble {role}'>{text}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='chat-suggestions'>", unsafe_allow_html=True)
        suggestion_cols=st.columns(3)
        for index,suggestion in enumerate(suggestions):
            with suggestion_cols[index % 3]:
                if st.button(suggestion,key=f"chat_suggestion_{index}",width="stretch"):
                    st.session_state.pending_prompt=suggestion
                    st.rerun()
        pending=st.session_state.pop("pending_prompt", "")
        with st.form("chat_form", clear_on_submit=True, border=False):
            input_col,send_col=st.columns([.86,.14],gap="small")
            with input_col:
                prompt=st.text_input("Message",value=pending,placeholder="Type a question...",label_visibility="collapsed")
            with send_col:
                submitted=st.form_submit_button("Send",type="primary",width="stretch")
        st.markdown("<div class='chat-hint'>The assistant will use available risk and policy tools as they are connected.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    if submitted and prompt.strip():
        st.session_state.chat_history.append({"role":"user","content":prompt.strip()})
        response=ask_agent(prompt.strip())
        st.session_state.chat_history.append({"role":"assistant","content":response["message"]})
        st.rerun()

def history_page():
    st.title("Application history")
    st.caption("Previous applications submitted from this account.")
    records=APPLICATIONS.history(st.session_state.user["email"])
    if not records:
        with st.container(border=True):
            st.info("No applications have been submitted yet.")
        return
    for created,payload_text,result_text in records:
        payload=json.loads(payload_text); result=json.loads(result_text)
        submitted_at=time.strftime("%d %b %Y, %H:%M",time.localtime(created))
        with st.container(border=True):
            a,b,c=st.columns(3)
            a.write(f"**Submitted:** {submitted_at}")
            b.write(f"**Risk tier:** {result.get('risk_tier','—')}")
            c.write(f"**Default score:** {result.get('default_probability',0):.2%}")
            st.caption(f"{payload.get('loan_intent','—')} · Loan amount {payload.get('loan_amnt','—')} · {result.get('predicted_label','—')}")

init_state();seed_account();styles()
if st.session_state.user:
    workspace_layout()
else:auth_page()
