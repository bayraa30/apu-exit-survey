import streamlit as st
from snowflake.snowpark import Session
from app_setup import apply_custom_font
import math

apply_custom_font()

def get_session():
    return Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# ---- CONFIGURATION ----
COMPANY_NAME = "АПУ ХХК"
SCHEMA_NAME = "APU"
EMPLOYEE_TABLE = "APU_EMP_DATA"
LOGO_URL = "https://i.imgur.com/DgCfZ9B.png"

# --- Snowflake credentials (replace with your actual or use Streamlit secrets) ---
SNOWFLAKE_USER = "YOUR_USER"
SNOWFLAKE_PASSWORD = "YOUR_PASSWORD"
SNOWFLAKE_ACCOUNT = "YOUR_ACCOUNT"
SNOWFLAKE_WAREHOUSE = "YOUR_WAREHOUSE"
SNOWFLAKE_DATABASE = "CDNA_HR_DATA"



# ---- CONFIG ----
COMPANY_NAME = "АПУ ХХК"
SCHEMA_NAME = "APU"
EMPLOYEE_TABLE = "APU_EMP_DATA_JULY2025"
ANSWER_TABLE = f"{SCHEMA_NAME}_SURVEY_ANSWERS"
DATABASE_NAME = "CDNA_HR_DATA"
LOGO_URL = "https://i.imgur.com/DgCfZ9B.png"
LINK_TABLE = f"{SCHEMA_NAME}_SURVEY_LINKS"  # -> APU_SURVEY_LINKS
BASE_URL = "https://apu-exit-survey-cggmobn4x6kmsmpavyuu5z.streamlit.app/"  



# ---- Answer storing ----
import json
from datetime import datetime

def submit_answers():
    emp_code = st.session_state.get("confirmed_empcode")
    first_name = st.session_state.get("confirmed_firstname")
    survey_type = st.session_state.get("survey_type", "")
    schema = SCHEMA_NAME
    table = f"{schema}_SURVEY_ANSWERS"
    submitted_at = datetime.utcnow()
    a = st.session_state.answers

    print("🚀 DEBUG: Submitting empcode and firstname:", emp_code, first_name)

    values = [
        emp_code,
        first_name,
        survey_type,
        submitted_at,
        a.get("Reason_for_Leaving", ""),
        a.get("Alignment_with_Daily_Tasks", ""),
        a.get("Unexpected_Responsibilities", ""),
        a.get("Onboarding_Effectiveness", ""),
        a.get("Company_Culture", ""),
        a.get("Atmosphere", ""),
        a.get("Conflict_Resolution", ""),
        a.get("Feedback", ""),
        a.get("Leadership_Style", ""),
        a.get("Team_Collaboration", ""),
        a.get("Team_Support", ""),
        a.get("Motivation", ""),
        a.get("Motivation_Other", ""),
        a.get("Engagement", ""),
        a.get("Engagement_Other", ""),
        a.get("Well_being", ""),
        a.get("Performance_Compensation", ""),
        a.get("Value_of_Benefits", ""),
        a.get("KPI_Accuracy", ""),
        a.get("Career_Growth", ""),
        a.get("Traning_Quality", ""),
        a.get("Loyalty1", ""),
        a.get("Loyalty1_Other", ""),
        a.get("Loyalty2", ""),
        a.get("Loyalty2_Other", "")
    ]

    try:
        session = get_session()

        escaped_values = ["'{}'".format(str(v).replace("'", "''")) if v is not None else "''" for v in values]

        insert_query = f"""
            INSERT INTO {table} (
                EMPCODE, FIRSTNAME, SURVEY_TYPE, SUBMITTED_AT,
                Reason_for_Leaving,
                Alignment_with_Daily_Tasks,
                Unexpected_Responsibilities,
                Onboarding_Effectiveness,
                Company_Culture,
                Atmosphere,
                Conflict_Resolution,
                Feedback,
                Leadership_Style,
                Team_Collaboration,
                Team_Support,
                Motivation,
                Motivation_Other,
                Engagement,
                Engagement_Other,
                Well_being,
                Performance_Compensation,
                Value_of_Benefits,
                KPI_Accuracy,
                Career_Growth,
                Traning_Quality,
                Loyalty1,
                Loyalty1_Other,
                Loyalty2,
                Loyalty2_Other
            )
            VALUES ({','.join(escaped_values)})
        """

        session.sql(insert_query).collect()
        return True

    except Exception as e:
        st.error(f"❌ Failed to submit answers: {e}")
        return False




# ---- Survey types per category ----
survey_types = {
    "Компанийн санаачилгаар": ["1 жил хүртэл", "1-ээс дээш"],
    "Ажилтны санаачлагаар": [
        "6 сар дотор гарч байгаа", "7 сараас 3 жил ",
        "4-10 жил", "11 болон түүнээс дээш"
    ],
}

# ---- Total questions number dictionary by survey type & employment duration ----
total_questions_number_dict = {
    "Ажил олгогчийн санаачилгаар": {"1 жил хүртэл" : {"start_idx": 2, "total_questions": 11}, "1-ээс дээш": {"start_idx": 3, "total_questions": 11}},
    "Ажилтны санаачлагаар": {"1 жил хүртэл" : {"start_idx": 1, "total_questions": 13}, "1-ээс дээш": {"start_idx": 1, "skip_idx": 2, "total_questions": 11}}
}


def categorize_employment_duration(total_months: int) -> str:
    if total_months <= 12:
            return "1 жил хүртэл"
    else:
        return "1-ээс дээш"
    

# ---- PAGE SETUP ----
st.set_page_config(page_title=f"{COMPANY_NAME} Судалгаа", layout="wide")

# ---- Submit answer into answers dictionory inside session state ----
def submitAnswer(answer_key, answer):
    if(answer and answer_key):
        st.session_state.answers[answer_key]= answer

def logo():
    st.image(LOGO_URL, width=210)

def progress_chart():
    total_questions_by_type = {
        "1 жил хүртэл": 17,
        "1-ээс дээш": 16,
        "6 сар дотор гарч байгаа": 20,
        "7 сараас 3 жил ": 19,
        "4-10 жил": 19,
        "11 болон түүнээс дээш": 19
    }

    if st.session_state.page < 3:
        return  # Skip showing progress before Q1 starts

    current_page = st.session_state.page
    total = total_questions_by_type.get(st.session_state.survey_type, 19)
    question_index = max(1, current_page - 3 + 1)  # Never below 1
    progress = min(100, max(0, int((question_index / total) * 100)))  # Clamp between 0–100
    percentage = math.ceil(( question_index / total ) * 100)
    st.progress(progress)
    # st.markdown(f"#### {percentage}%",width="content")

def goToNextPage():
    curr_page = st.session_state.page
    if(curr_page < 15):
        next_page = curr_page + 1
        st.session_state.page = next_page 
        st.rerun()  

def nextPageBtn(disabled):
    col1,col2 = st.columns([5,1])
    st.markdown("""
        <style>
               div[data-testid="stButton"] button{
                    justify-self: end;
                    align-self: end;
                    padding: 15px 30px;
                    margin-top: 10em;
                    color: #fff;
                    background-color: #ec1c24 !important;  
                    border-radius: 20px; 
                } 
               div[data-testid="stButton"] button p{
                    font-size: 1.5em;
                } 
        </style>

    """,unsafe_allow_html=True)
    with col2:
        if(st.button(label="Үргэлжлүүлэх →", disabled=disabled)):
            goToNextPage()


def choose_survey_type(category: str, total_months: int) -> str:
    # Компанийн санаачилгаар
    if category == "Компанийн санаачилгаар":
        if total_months <= 12:
            return "1 жил хүртэл"
        else:
            return "1-ээс дээш"

    # Ажилтны санаачлагаар
    if category == "Ажилтны санаачлагаар":
        if total_months <= 6:
            return "6 сар дотор гарч байгаа"
        elif total_months <= 36:
            return "7 сараас 3 жил "
        elif total_months <= 120:
            return "4-10 жил"
        else:
            return "11 болон түүнээс дээш"

    # Ажил хаяж явсан → always this type
    if category == "Ажил хаяж явсан":
        return "Мэдээлэл бүртгэх"

    # fallback
    return ""


def confirmEmployeeActions(empcode):
    from datetime import date, datetime as dt  # for tenure calculation

    def _to_date_safe(v):
        try:
            if isinstance(v, dt):
                return v.date()
            if isinstance(v, date):
                return v
            if v is None or str(v).strip() == "":
                return None
            return dt.fromisoformat(str(v).split(" ")[0]).date()
        except Exception:
            return None

    def _fmt_tenure(start_dt: date, end_dt: date) -> str:
        if not start_dt:
            return ""
        days = (end_dt - start_dt).days
        if days < 0:
            return "0 сар"
        years = int(days // 365.25)
        rem_days = days - int(years * 365.25)
        months = int(rem_days // 30.44)
        parts = []
        if years > 0:
            parts.append(f"{years} жил")
        parts.append(f"{months} сар")
        return " ".join(parts)


    ## DEBUGG
    print(empcode)


    try:
        session = get_session()
        df = session.table(f"{DATABASE_NAME}.{SCHEMA_NAME}.{EMPLOYEE_TABLE}")
        match = df.filter(
            (df["EMPCODE"] == empcode) & (df["STATUS"] == "Идэвхтэй")
        ).collect()

        if match:
            emp = match[0]

            hire_dt = _to_date_safe(emp["LASTHIREDDATE"])
            tenure_str = _fmt_tenure(hire_dt, date.today()) if hire_dt else ""

            if hire_dt:
                days = (date.today() - hire_dt).days
                total_months = max(0, int(days // 30.44))
            else:
                total_months = 0

            st.session_state.emp_confirmed = True
            st.session_state.confirmed_empcode = empcode
            st.session_state.confirmed_firstname = emp["FIRSTNAME"]
            st.session_state.emp_info = {
                "Компани": emp["COMPANYNAME"],
                "Алба хэлтэс": emp["HEADDEPNAME"],
                "Албан тушаал": emp["POSNAME"],
                "Овог": emp["LASTNAME"],
                "Нэр": emp["FIRSTNAME"],
                "Ажилласан хугацаа": tenure_str,
            }
            st.session_state.tenure_months = total_months

            category = st.session_state.get("category_selected")
            if category:
                auto_type = choose_survey_type(category, total_months)
                st.session_state.survey_type = auto_type

        else:
            st.session_state.emp_confirmed = False

    except Exception as e:
        st.error(f"❌ Snowflake холболтын алдаа: {e}")
        st.session_state.emp_confirmed = False


    ## employee confirmed
    if st.session_state.get("emp_confirmed") is True:
        st.success("✅ Амжилттай баталгаажлаа!")
        emp = st.session_state.emp_info

        st.markdown(f"""
        **Компани:** {emp['Компани']}  
        **Алба хэлтэс:** {emp['Алба хэлтэс']}  
        **Албан тушаал:** {emp['Албан тушаал']}  
        **Овог:** {emp['Овог']}  
        **Нэр:** {emp['Нэр']}  
        **Ажилласан хугацаа:** {emp.get('Ажилласан хугацаа', '')}
        """)

        auto_type = st.session_state.get("survey_type", "")
        if auto_type:
            st.info(f"📌 Таньд тохирох судалгааны төрөл: **{auto_type}**")

        if st.button("🔗 Линк үүсгэх (онлайнаар бөглөх)"):
            import uuid
            try:
                session = get_session()
                token = uuid.uuid4().hex

                survey_type = st.session_state.get("survey_type", "")
                empcode_confirmed = st.session_state.get("confirmed_empcode", "")

                session.sql(f"""
                    INSERT INTO {DATABASE_NAME}.{SCHEMA_NAME}.{LINK_TABLE}
                        (TOKEN, EMPCODE, SURVEY_TYPE)
                    VALUES
                        ('{token}', '{empcode_confirmed}', '{survey_type}')
                """).collect()

                survey_link = f"{BASE_URL}?mode=link&token={token}"
                st.success("Линк амжилттай үүслээ. Доорх линкийг ажилтанд илгээнэ үү:")
                st.code(survey_link, language="text")

            except Exception as e:
                st.error(f"❌ Линк үүсгэх үед алдаа гарлаа: {e}")

        if st.button("Үргэлжлүүлэх"):
            # (Your 'Судалгааг бөглөөгүй' logic etc. can stay if needed)
            st.session_state.page = 2
            st.rerun()

    elif st.session_state.get("emp_confirmed") is False:
        st.error("❌ Идэвхтэй ажилтан олдсонгүй. Кодоо шалгана уу.")


# ---- Link Handling ----
def init_from_link_token():
    """
    If URL has ?mode=link&token=..., we:
    - Look up EMPCODE + SURVEY_TYPE from APU_SURVEY_LINKS
    - Load employee info
    - Fill session_state
    - Jump to page 2 (intro)
    """
    # Get query params (works on Streamlit Cloud)
    params = st.query_params

    mode_list = params.get("mode", [None])
    token_list = params.get("token", [None])

    mode = mode_list[0]
    token = token_list[0]

    # Not a magic link → do nothing
    if mode != "link" or not token:
        return

    try:
        session = get_session()

        # 1) Find EMPCODE + SURVEY_TYPE from link table
        link_df = session.sql(f"""
            SELECT EMPCODE, SURVEY_TYPE
            FROM {DATABASE_NAME}.{SCHEMA_NAME}.{LINK_TABLE}
            WHERE TOKEN = '{token}'
            ORDER BY CREATED_AT DESC
            LIMIT 1
        """).to_pandas()

        if link_df.empty:
            st.error("Энэ линк хүчингүй болсон эсвэл олдсонгүй.")
            return

        empcode = link_df.iloc[0]["EMPCODE"]
        survey_type = link_df.iloc[0]["SURVEY_TYPE"]

        # 2) Load employee info from EMP table
        emp_df = session.sql(f"""
            SELECT EMPCODE, LASTNAME, FIRSTNAME, COMPANYNAME, HEADDEPNAME, POSNAME
            FROM {DATABASE_NAME}.{SCHEMA_NAME}.{EMPLOYEE_TABLE}
            WHERE EMPCODE = '{empcode}'
            LIMIT 1
        """).to_pandas()

        if emp_df.empty:
            st.error("Ажилтны мэдээлэл олдсонгүй.")
            return

        row = emp_df.iloc[0]

        # 3) Hydrate session_state so it behaves like HR-confirmed
        st.session_state.logged_in = True       # 🔑 bypass HR login
        st.session_state.emp_confirmed = True
        st.session_state.confirmed_empcode = empcode
        st.session_state.confirmed_firstname = row["FIRSTNAME"]
        st.session_state.emp_info = {
            "Компани": row["COMPANYNAME"],
            "Алба хэлтэс": row["HEADDEPNAME"],
            "Албан тушаал": row["POSNAME"],
            "Овог": row["LASTNAME"],
            "Нэр": row["FIRSTNAME"],
        }
        st.session_state.survey_type = survey_type

        # Always go to intro page for link users
        st.session_state.page = 2

    except Exception as e:
        st.error(f"❌ Линкээр нэвтрэх үед алдаа гарлаа: {e}")


# st.write("DEBUG:",
#          "logged_in =", st.session_state.get("logged_in"),
#          "page =", st.session_state.get("page"),
#          "params =", st.experimental_get_query_params())








# 🔹 NEW: try to initialize from link token (if any)
init_from_link_token()

# ---- STATE INIT ----
if "category_selected" not in st.session_state:
    st.session_state.category_selected = None
if "survey_type" not in st.session_state:
    st.session_state.survey_type = None
if "page" not in st.session_state:
    st.session_state.page = 0
if "emp_confirmed" not in st.session_state:
    st.session_state.emp_confirmed = None
if "answers" not in st.session_state:
    st.session_state.answers = {}

# ---- HANDLERS ----
def set_category(category):
    st.session_state.category_selected = category
    st.session_state.survey_type = None

def set_survey_type(survey):
    st.session_state.survey_type = survey
    st.session_state.page = 1

def confirm_employeeByCode():
    emp_code = st.session_state.empcode.strip()

    try:
        session = get_session()

        df = session.sql(f"""
            SELECT LASTNAME, FIRSTNAME, POSNAME, HEADDEPNAME, DEPNAME, COMPANYNAME
            FROM {SNOWFLAKE_DATABASE}.{SCHEMA_NAME}.{EMPLOYEE_TABLE}
            WHERE EMPCODE = '{emp_code}'
        """).to_pandas()

        if not df.empty:
            st.session_state.emp_confirmed = True
            st.session_state.emp_info = {
                "Компани": df.iloc[0]["COMPANYNAME"],
                "Алба хэлтэс": df.iloc[0]["HEADDEPNAME"],
                "Албан тушаал": df.iloc[0]["POSNAME"],
                "Овог": df.iloc[0]["LASTNAME"],
                "Нэр": df.iloc[0]["FIRSTNAME"],
            }
            st.session_state.confirmed_empcode = emp_code
        else:
            st.session_state.emp_confirmed = False

    except Exception as e:
        st.session_state.emp_confirmed = False
        st.error(f"❌ Snowflake холболтын алдаа: {e}")

def confirm_employee():
    emp_code = st.session_state.empcode.strip()
    firstname = st.session_state.firstname.strip()

    try:
        session = get_session()

        df = session.sql(f"""
            SELECT LASTNAME, FIRSTNAME, POSNAME, HEADDEPNAME, DEPNAME, COMPANYNAME
            FROM {SNOWFLAKE_DATABASE}.{SCHEMA_NAME}.{EMPLOYEE_TABLE}
            WHERE EMPCODE = '{emp_code}' AND FIRSTNAME = '{firstname}'
        """).to_pandas()

        if not df.empty:
            st.session_state.emp_confirmed = True
            st.session_state.emp_info = {
                "Компани": df.iloc[0]["COMPANYNAME"],
                "Алба хэлтэс": df.iloc[0]["HEADDEPNAME"],
                "Албан тушаал": df.iloc[0]["POSNAME"],
                "Овог": df.iloc[0]["LASTNAME"],
                "Нэр": df.iloc[0]["FIRSTNAME"],
            }
            st.session_state.confirmed_empcode = emp_code
            st.session_state.confirmed_firstname = firstname
        else:
            st.session_state.emp_confirmed = False

    except Exception as e:
        st.session_state.emp_confirmed = False
        st.error(f"❌ Snowflake холболтын алдаа: {e}")



def go_to_intro():
    st.session_state.page = 2

def begin_survey():
    st.session_state.page = 3

# ---- LOGIN PAGE ----
# def login_page():
    st.image(LOGO_URL, width=210)
    st.title("👨‍💼 Нэвтрэх 👩‍💼")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "hr" and password == "demo123":
            st.session_state.logged_in = True
            st.session_state.page = -0.5  # Go to directory
            st.rerun()
        else:
            st.error("❌ Invalid credentials. Please try again.")

def login_page():
    # Make the page take full height and remove default top padding
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 3rem;
                display: flex;
                flex-direction: row;
                justify-content: center;
                align-items: center;
                height: 100vh; /* Full viewport height */

            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Use columns to center horizontally
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2em;">
                <img src="https://i.imgur.com/DgCfZ9B.png" width="200">
            </div>
            """,
            unsafe_allow_html=True
        )

        username = st.text_input("НЭВТРЭХ НЭР", )
        password = st.text_input("НУУЦ ҮГ", type="password")

        # CSS for the login button
        st.markdown("""
            <style>
                /* Target the first Streamlit button (Login) specifically */
                div[data-testid="stButton"] button:nth-of-type(1) {
                    width: 100% !important;           /* Full width */
                    display: flex !important;
                    flex-direction: row;
                    justify-content: center;
                    background-color: #ec1c24 !important; /* Red */
                    color: white !important;          /* Text color */
                    height: 45px;
                    font-size: 18px;
                    border-radius: 10px;
                    transition: all 1s ease-in-out;
                }

                div[data-testid="stButton"] button:nth-of-type(1):hover {
                    background: linear-gradient(90deg,rgba(230, 224, 122, 0.39) 30%, rgba(236, 28, 36, 0.61) 70%, rgba(236, 28, 36, 0.68) 100%);
                }
            </style>
        """, unsafe_allow_html=True)    

        if st.button("Нэвтрэх", use_container_width=True):
            if username == "hr" and password == "demo123":
                st.session_state.logged_in = True
                st.session_state.page = -0.5
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")


# ---- DIRECTORY PAGE ----
def directory_page():

    st.image(LOGO_URL, width=200)

    col1,col2 =  st.columns([1,2])
    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em; height:60vh; display:table; ">
                    <p style="display:table-cell; vertical-align: middle;">Ажилтны ерөнхий <span style="color: #ec1c24;"> мэдээлэл </span> </p>
            </h1>
        """, unsafe_allow_html=True)

    
    
    with col2:
        st.markdown("""
            <style>
                /* Style radio group container */
                div[data-testid="stRadio"] > div {
                    display: flex;
                    flex-direction: row !important;
                    flex-wrap: nowrap;
                    padding-left: 20px;
                }

                /* Style each radio option like a button */
                div[data-testid="stRadio"] label {
                    background-color: #fff;       /* default background */
                    padding: 8px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    border: 1px solid #ccc;
                    transition: all 0.2s ease-in-out;
                    text-align: center;
                }
                        
                label[data-testid="stWidgetLabel"]{
                    border: 0px !important;
                    font-size: 2px !important;
                    color: #898989;
                    
                }

                /* Hover effect */
                div[data-testid="stRadio"] label:hover {
                    border-color: #ec1c24;
                }

              
                /* Hide default radio buttons */
                div[data-testid="stRadio"] > div > label > div:first-child {
                    display: none !important;
                }
                    
                /* Checked/selected option */
                div[data-testid="stRadio"] > div label:has(input[type="radio"]:checked){
                    background-color: #fefefe !important;
                    border-color: #ec1c24 !important;
                }
                
                div[data-testid="stLayoutWrapper"] div:not([data-testid="stRadio"]) div[data-testid="stHorizontalBlock"] {
                    align-items: end;
                }
                    

            
            </style>    
            """, unsafe_allow_html=True)
        
    # ---- SURVEY TYPE + EMPLOYEE CODE CONFIRMATION ----
        option1 = st.radio("СУДАЛГААНЫ АНГИЛАЛ", ["ГАРАХ СУДАЛГАА", "ГАРАХ ЯРИЛЦЛАГА"], index=None)
        if(option1 == "ГАРАХ СУДАЛГАА"):
            option2 = st.radio("АЖЛААС ГАРСАН ТӨРӨЛ", ["КОМПАНИЙ САНААЧЛАГААР", "АЖИЛТНЫ САНААЧЛАГААР", "АЖИЛ ХАЯЖ ЯВСАН"], index=None)
            if(option2):

                col1, col2 = st.columns([3, 1])                
                with col1:
                    emp_code = st.text_input("Ажилтны код", key="empcode")
                with col2:
                    if st.button("Баталгаажуулах", key="btn_confirm"):
                        # confirmEmployeeActions(emp_code)
                        begin_survey()
                        st.rerun()
                        
                        # if emp_code:
                        #     st.session_state.temp_empcode = emp_code
                        #     confirm_employeeByCode()
                        # else:
                        #     st.session_state.emp_confirmed = False
                        #     st.error("❌ Ажилтны кодыг шалгана уу.")

                # if st.session_state.emp_confirmed is True:
                #     st.success("✅ Амжилттай баталгаажлаа!")
                #     emp = st.session_state.emp_info

                #     # Save confirmed values permanently
                #     st.session_state.confirmed_empcode = st.session_state.temp_empcode

                #     st.markdown("### 🧾 Ажилтны мэдээлэл")
                #     st.markdown(f"""
                #         **Компани:** {emp['Компани']}  
                #         **Алба хэлтэс:** {emp['Алба хэлтэс']}  
                #         **Албан тушаал:** {emp['Албан тушаал']}  
                #         **Овог:** {emp['Овог']}  
                #         **Нэр:** {emp['Нэр']}
                #         """)

                #     if st.button("Үргэлжлүүлэх", key="btn_intro"):
                #         go_to_intro()
                #         st.rerun()

                # elif st.session_state.emp_confirmed is False and st.session_state.get("empcode"):
                #     st.error("❌ Ажилтны мэдээлэл буруу байна. Код болон нэрийг шалгана уу.")


        # if st.button("Continue"):
        #     if option:
        #         if option == "ГАРАХ СУДАЛГАА":
        #             st.session_state.page = 0
        #             st.rerun()
        #         elif option == "ГАРАХ ЯРИЛЦЛАГА":
        #             st.warning("Interview flow coming soon!")
        #     else:
        #         st.error("Та сонголт хийнэ үү.")


# ---- INIT AUTH STATE ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = -1

# ---- LOGIN/DIRECTORY ROUTING ----
if not st.session_state.logged_in:
    login_page()
    st.stop()
elif st.session_state.page == -0.5:
    directory_page()
    st.stop()


# ---- PAGE 0: CATEGORY + SURVEY TYPE (Single Page) ----
if st.session_state.page == 0:
    logo()
    st.header("Ерөнхий мэдээлэл")
    st.markdown("**Судалгааны ангилал болон төрлөө сонгоно уу.**")

    # Step 1: Category (dropdown)
    category = st.selectbox(
        "Судалгааны ангилал:",
        ["-- Сонгох --"] + list(survey_types.keys()),
        index=0 if not st.session_state.category_selected else list(survey_types.keys()).index(st.session_state.category_selected) + 1,
        key="category_select"
    )
    if category != "-- Сонгох --":
        set_category(category)

    # Step 2: Survey type (buttons) -- always shown if category selected
    if st.session_state.category_selected:
        st.markdown("**Судалгааны төрөл:**")
        types = survey_types[st.session_state.category_selected]
        cols = st.columns(len(types))
        for i, survey in enumerate(types):
            with cols[i]:
                if st.button(survey, key=f"survey_{i}"):
                    set_survey_type(survey)
                    st.rerun()

# ---- PAGE 1: EMPLOYEE CONFIRMATION ----
elif st.session_state.page == 1:
    logo()
    st.title("Ажилтны баталгаажуулалт")

    st.text_input("Ажилтны код", key="empcode")
    st.text_input("Нэр", key="firstname")

    if st.button("Баталгаажуулах", key="btn_confirm"):
        emp_code = st.session_state.get("empcode", "").strip()
        firstname = st.session_state.get("firstname", "").strip()

        if emp_code and firstname:
            st.session_state.temp_empcode = emp_code
            st.session_state.temp_firstname = firstname
            confirm_employee()
        else:
            st.session_state.emp_confirmed = False
            st.error("❌ Ажилтны код болон нэрийг бүрэн оруулна уу.")

    if st.session_state.emp_confirmed is True:
        st.success("✅ Амжилттай баталгаажлаа!")
        emp = st.session_state.emp_info

        # Save confirmed values permanently
        st.session_state.confirmed_empcode = st.session_state.temp_empcode
        st.session_state.confirmed_firstname = st.session_state.temp_firstname

        st.markdown("### 🧾 Таны мэдээлэл")
        st.markdown(f"""
            **Компани:** {emp['Компани']}  
            **Алба хэлтэс:** {emp['Алба хэлтэс']}  
            **Албан тушаал:** {emp['Албан тушаал']}  
            **Овог:** {emp['Овог']}  
            **Нэр:** {emp['Нэр']}
            """)

        if st.button("Үргэлжлүүлэх", key="btn_intro"):
            go_to_intro()
            st.rerun()

    elif st.session_state.emp_confirmed is False and st.session_state.get("empcode") and st.session_state.get("firstname"):
        st.error("❌ Ажилтны мэдээлэл буруу байна. Код болон нэрийг шалгана уу.")


# ---- SURVEY QUESTION 1 ----
elif st.session_state.page == 3:
    # ✅ Check confirmed values
    # if not st.session_state.get("confirmed_empcode") or not st.session_state.get("confirmed_firstname"):
    #     st.error("❌ Ажилтны мэдээлэл баталгаажаагүй байна. Эхний алхмыг дахин шалгана уу.")
    #     st.stop()
    
    logo()
    col1,col2 =  st.columns(2)

    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-right: 1em; font-size: 3em; height: 60vh; display: table;">
                    <p style="display:table-cell; vertical-align: middle;"> Танд ажлаас гарахад нөлөөлсөн<span style="color: #ec1c24;"> хүчин зүйл, шалтгаантай</span> хамгийн их тохирч байгаа 1-3 хариултыг сонгоно уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        
# --- Styling: make checkboxes look like buttons ---
        st.markdown("""
        <style>
            /* Hide default checkbox icons */
            div[data-testid="stCheckbox"] > label > span {
                display: none;
            }
                    
            div[data-testid="stVerticalBlock"]  {
                display: flex !important;
                flex-direction: row;
                flex-wrap: wrap !important;
            }
            
                    
            div[data-testid="stCheckbox"]  {
                margin: 0 !important;
                width: 100% !important;
            }
                        
            /* Hide native checkbox */
            div[data-testid="stCheckbox"] input {
                position: absolute;
                opacity: 0;
                pointer-events: none;
                width: 100% !important;
            }

            /* Style each label like a button */
            div[data-testid="stCheckbox"] label {
                border: 1px solid #d1d5db;
                border-radius: 20px;
                padding: 14px 20px;
                text-align: center;
                cursor: pointer;
                width: 100% !important;
                transition: all 0.15s ease-in-out;
                height: 100%;
                user-select: none;
                white-space: pre-line;  /* Respect newline in label */
            }

            /* Subtitle */
            div[data-testid="stCheckbox"] p {
                font-size: 1.2em;
                color: #4b5563;
            }

            /* Hover effect */
            div[data-testid="stCheckbox"] label:hover {
                border-color: red !important; 
            }

            div[data-testid="stCheckbox"] input[type="checkbox"]:checked + div,
            div[data-testid="stCheckbox"] input[type="checkbox"]:checked ~ div,
            div[data-testid="stCheckbox"] label:has(input[type="checkbox"]:checked) > div,
            div[data-testid="stCheckbox"] label:has(input[type="checkbox"]:checked) {
                border-color: #ec1c24;
            }

        </style>
        """, unsafe_allow_html=True)

       
        # --- OPTIONS ---
        options = [ "Удирдлагын арга барил, харилцаа муу", 
                    "Компанийн соёл таалагдаагүй", 
                    "Хамт олны уур амьсгал, харилцаа таарамжгүй", 
                    "Цалин хөлс хангалтгүй", 
                    "Гүйцэтгэлийн үнэлгээ шудрага бус", 
                    "Ажлын ачаалал их","Ажлын цагийн хуваарь таарамжгүй, хэцүү байсан",
                    "Дасан зохицуулах хөтөлбөрийн хэрэгжилт муу",
                    "Өөр хот, аймаг, улсад шилжих, амьдрах",
                    "Тэтгэвэрт гарч байгаа",
                    "Албан тушаал/мэргэжлийн хувьд өсөх, суралцах боломж байхгүй",
                    "Үндсэн мэргэжлийн дагуу ажиллах болсон",
                    "Хөдөлмөрийн нөхцөл хэвийн бус/хүнд хортой байсан",
                    "Хувийн шалтгаан/Personal Reasons",
                    "Илүү боломжийн өөр ажлын байрны санал авсан",
                    "Ажлын орчин нөхцөл муу",
                    "Ар гэрийн асуудал үүссэн",
                    "Эрүүл мэндийн байдлаас",
                    "Гадаадад улсад ажиллах/суралцах"]

        # --- Session state for selected answers ---
        st.session_state.selected = []

        # --- Render choices ---
        cols = st.columns(2)  # 2×3, change to st.columns(4) for 2×4 grid

        for i, opt in enumerate(options):

            check_for_max_choices = len(st.session_state.selected) == 3

            is_checked = opt in st.session_state.selected
            css_class = "checkbox-btn checked" if is_checked else "checkbox-btn"
            key=f"cb_{i}"

            if col2.checkbox(opt,key=key, value=is_checked, disabled=check_for_max_choices):
                if not is_checked:
                    # Trying to select
                    st.session_state.selected.append(opt)
                else:
                    # Unselect
                    st.session_state.selected.remove(opt)


    # if(len(st.session_state.selected) > 0 and len(st.session_state.selected) <= 3):

    answer_key = "Reason_for_Leaving"
    max_choices_reached = len(st.session_state.selected) > 3

    if(len(st.session_state.selected)):
        if(nextPageBtn(max_choices_reached)):
            submitAnswer(answer_key, st.session_state.selected)
    if(len(st.session_state.selected) > 3):
        st.warning("Хамгийн ихдээ 3 төрлийг сонгоно уу")


elif st.session_state.page == 4:
    
    logo()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em;">
                    <p style="display:table-cell; vertical-align: middle;"> Дасан зохицох хөтөлбөрийн хэрэгжилт эсвэл баг хамт олон, шууд удирдлага танд өдөр тутмын ажил, үүрэг даалгавруудыг хурдан ойлгоход туслах <span style="color: #ec1c24;"> хангалттай мэдээлэл, заавар</span> өгч чадсан уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <style>
                div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
                   align-items: center;
                }
                
                div[data-testid="stButton"] button {
                   height: 60vh !important;
                }
        </style>
    """, unsafe_allow_html=True)
        
        
        answer_key = "Alignment_with_Daily_Tasks"
    
        col1, col2 = st.columns(2)
        btn1 = col1.button("Хангалттай чадсан", use_container_width=True, key="11", on_click=submitAnswer(answer_key,"Хангалттай чадсан"))
        btn2 = col2.button("Огт чадаагүй", use_container_width=True, key="22", on_click=submitAnswer(answer_key, "Огт чадаагүй"))
        
        if(btn1 or btn2):
            goToNextPage()

            

elif st.session_state.page == 5:
    logo()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em;">
                    <p style="display:table-cell; vertical-align: middle;"> Ажлын байрны тодорхойлолт таны <span style="color: #ec1c24;"> өдөр тутмын </span> ажил үүрэгтэй нийцэж байсан уу??</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <style>
                div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
                   align-items: center;
                }
                
                div[data-testid="stButton"] button {
                   height: 60vh !important;
                }
        </style>
    """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        answer_key = "jaja"
        btn1 = col1.button("Тийм", use_container_width=True, key="787878", on_click=submitAnswer(answer_key,"Тийм"))
        btn2 = col2.button("Үгүй", use_container_width=True, key="999999", on_click=submitAnswer(answer_key,"Үгүй"))

        if(btn1 or btn2):
            goToNextPage()


elif st.session_state.page == 6:
    logo()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em;">
                    <p style="display:table-cell; vertical-align: middle;"> Таны шууд удирдлага санал зөвлөгөө өгч, <span style="color: #ec1c24;"> эргэх холбоотой </span>ажилладаг байсан уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <style>
                div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
                   align-items: center;
                }
                
                div[data-testid="stButton"] button {
                   height: 60vh !important;
                }
        </style>
    """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        answer_key = "jaja"
        btn1 = col1.button("Би Би гэдэг", use_container_width=True, key="112121", on_click=submitAnswer(answer_key, "Би Би гэдэг"))
        btn2 = col2.button("Бид Бид гэдэг", use_container_width=True, key="22232323", on_click=submitAnswer(answer_key,"Бид Бид гэдэг"))

        if(btn1 or btn2):
            goToNextPage()


elif st.session_state.page == 7:
    logo()
    col1,col2 =  st.columns(2)

    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em; height:60vh; display: table;">
                    <p style="display:table-cell; vertical-align: middle;"> Таны харъяалагдаж буй баг доторх <span style="color: #ec1c24;">хамтын ажиллагаа,</span> хоорондын харилцаанд хэр сэтгэл хангалуун байсан бэ?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <style>
                    
                /* Hide default radio buttons */
                div[data-testid="stRadio"] > div > label > div:first-child {
                    display: none !important;
                }
                    
              /* area that contains the text (Streamlit wraps text inside a div) */
                div[data-testid="stRadio"] label > div {
                    /* respect newline characters in the option strings */
                    white-space: pre-line;
                }

                /* Style radio group container */
                div[data-testid="stRadio"] > div {
                    gap: 10px;
                    justify-content: center;
                    align-items: center;
                }
                    /* "H1"-like first line */
                div[data-testid="stRadio"] label > div::first-line {
                    font-size: 2em;
                    font-weight: 700;
                    color: #111827;
                }

                /* Style each radio option like a button */
                div[data-testid="stRadio"] label {
                    background-color: #fff;       /* default background */
                    width: 60%;
                    padding: 8px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    border: 1px solid #ccc;
                    transition: background-color 0.2s;
                    text-align: center;
                    justify-content: center;
                }
                        
                label[data-testid="stWidgetLabel"]{
                    border: 0px !important;
                    font-size: 2px !important;
                    color: #898989;
                    
                }

                /* Hover effect */
                div[data-testid="stRadio"] label:hover {
                    border-color: #ec1c24;
                }

                /* Checked/selected option */
                div[data-testid="stRadio"] input:checked + label {
                    background-color: #FF0000 !important; /* selected color */
                    color: white !important;
                    border-color: #ec1c24 !important;
                }

                /* Hide default radio circle */
                div[data-testid="stRadio"] input[type="radio"] {
                    display: none;
                }
                        
            </style>
            """, unsafe_allow_html=True)
        
       
        options = [
           "⭐\nОгт санал нийлэхгүй байна", "⭐⭐\nCанал нийлэхгүй байна", "⭐⭐⭐\nХэлж мэдэхгүй байна", "⭐⭐⭐⭐\nБага зэрэг санал нийлж байна", "⭐⭐⭐⭐⭐\nБүрэн санал нийлж байна"
        ]

        answer_key = "Alignment_with_Daily_Tasks"

        def onRadioChange():
            submitAnswer(answer_key,st.session_state.get(answer_key))
        
        if(st.session_state.get(answer_key)):
            goToNextPage()
        # --- Create radio group ---
        choice = st.radio(
            "",
            options,
            horizontal=True,
            key="Alignment_with_Daily_Tasks",
            on_change=onRadioChange
        )

elif st.session_state.page == 8:
    logo()
    col1,col2 =  st.columns(2)

    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-right: 1em; font-size: 3em; height:60vh; display:table; ">
                    <p style="display:table-cell; vertical-align: middle;"> Танд өдөр тутмын ажлаа <span style="color: #ec1c24;">урам зоригтой </span> хийхэд ямар хүчин зүйлс нөлөөлдөг байсан бэ?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        
# --- Styling: make checkboxes look like buttons ---
        st.markdown("""
        <style>
            /* Hide default checkbox icons */
            div[data-testid="stCheckbox"] > label > span {
                display: none;
            }
                    
            
            div[data-testid="stVerticalBlock"]  {
                display: flex !important;
                flex-direction: row;
                flex-wrap: wrap !important;
            }
            
                    
            div[data-testid="stCheckbox"]  {
                margin: 0 !important;
                width: 100% !important;
            }
                        
            /* Hide native checkbox */
            div[data-testid="stCheckbox"] input {
                position: absolute;
                opacity: 0;
                pointer-events: none;
                width: 100% !important;
            }

            /* Style each label like a button */
            div[data-testid="stCheckbox"] label {
                border: 1px solid #d1d5db;
                border-radius: 20px;
                padding: 14px 20px;
                text-align: center;
                cursor: pointer;
                width: 100% !important;
                transition: all 0.15s ease-in-out;
                user-select: none;
                white-space: pre-line;  /* Respect newline in label */
            }

            /* Subtitle */
            div[data-testid="stCheckbox"] p {
                font-size: 1.2em;
                color: #4b5563;
            }

            /* Hover effect */
            div[data-testid="stCheckbox"] label:hover {
                border-color: red !important; 
            }

            div[data-testid="stCheckbox"] input[type="checkbox"]:checked + div,
            div[data-testid="stCheckbox"] input[type="checkbox"]:checked ~ div,
            div[data-testid="stCheckbox"] label:has(input[type="checkbox"]:checked) > div,
            div[data-testid="stCheckbox"] label:has(input[type="checkbox"]:checked) {
                border-color: #ec1c24;
            }

        </style>
        """, unsafe_allow_html=True)

       
        # --- OPTIONS ---
        options = [ "Цалин",
                    "Баг хамт олны дэмжлэг",
                    "Сурч хөгжих боломжоор хангагддаг байсан нь",
                    "Олон нийтийн үйл ажиллагаа",
                    "Шударга нээлттэй харилцаа",
                    "Шагнал урамшуулал",
                    "Ажлын орчин",
                    "Төсөл",
                    "Хөтөлбөрүүд + нээлттэй асуулт"
                ]

        # --- Session state for selected answers ---
        st.session_state.selected = []

        # --- Render choices ---
        cols = st.columns(2)  # 2×3, change to st.columns(4) for 2×4 grid

        for i, opt in enumerate(options):

            check_for_max_choices = len(st.session_state.selected) == 3

            is_checked = opt in st.session_state.selected
            css_class = "checkbox-btn checked" if is_checked else "checkbox-btn"
            key=f"cb_{i}"

            if col2.checkbox(opt,key=key, value=is_checked, disabled=check_for_max_choices):
                if not is_checked:
                    # Trying to select
                    st.session_state.selected.append(opt)
                else:
                    # Unselect
                    st.session_state.selected.remove(opt)


    # if(len(st.session_state.selected) > 0 and len(st.session_state.selected) <= 3):

    answer_key = "Reason_for_Leaving"
    max_choices_reached = len(st.session_state.selected) > 3

    if(len(st.session_state.selected)):
        if(nextPageBtn(max_choices_reached)):
            submitAnswer(answer_key, st.session_state.selected)
    if(len(st.session_state.selected) > 3):
        st.warning("Хамгийн ихдээ 3 төрлийг сонгоно уу")


elif st.session_state.page == 9:
    logo()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em;">
                    <p style="display:table-cell; vertical-align: middle;"> Байгууллага танд ажиллах <span style="color: #ec1c24;"> таатай нөхцөл</span>, ажил амьдралын тэнцвэртэй байдлаар ханган дэмждэг байсан уу? /Жнь: уян хатан цагийн хуваарь, ажлын байрны орчин/</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <style>
                div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
                   align-items: center;
                }
                
                div[data-testid="stButton"] button {
                   height: 60vh !important;
                }
        </style>
    """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        answer_key = "jaja"
        btn1 = col1.button("Тийм", use_container_width=True, key="112121", on_click=submitAnswer(answer_key, "Тийм"))
        btn2 = col2.button("Үгүй", use_container_width=True, key="22232323", on_click=submitAnswer(answer_key,"Үгүй"))

        if(btn1 or btn2):
            goToNextPage()


elif st.session_state.page == 10:
    logo()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em;">
                    <p style="display:table-cell; vertical-align: middle;"> Та ойрын хүрээлэлдээ "<span style="color: #ec1c24;">Дижитал Концепт</span>" -т ажилд орохыг санал болгох уу? </p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <style>
                div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
                   align-items: center;
                }
                
                div[data-testid="stButton"] button {
                   height: 60vh !important;
                }
        </style>
    """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        answer_key = "jaja"
        btn1 = col1.button("Тийм", use_container_width=True, key="112121", on_click=submitAnswer(answer_key, "Тийм"))
        btn2 = col2.button("Үгүй", use_container_width=True, key="22232323", on_click=submitAnswer(answer_key,"Үгүй"))

        if(btn1 or btn2):
            goToNextPage()

elif st.session_state.page == 7:
    logo()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em;">
                    <p style="display:table-cell; vertical-align: middle;"> Таны бодлоор ямар манлайллын хэв маяг<span style="color: #ec1c24;"> шууд удирдлагыг </span>тань хамгийн сайн илэрхийлэх вэ?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <style>
                div[data-testid="stColumn"] div[data-testid="stVerticalBlock"] {
                   align-items: center;
                }
                
                div[data-testid="stButton"] button {
                   height: 60vh !important;
                }
        </style>
    """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        answer_key = "jaja"
        btn1 = col1.button("Тийм", use_container_width=True, key="112121", on_click=submitAnswer(answer_key, "Тийм"))
        btn2 = col2.button("Үгүй", use_container_width=True, key="22232323", on_click=submitAnswer(answer_key,"Үгүй"))

        if(btn1 or btn2):
            goToNextPage()


elif st.session_state.page == 4:
    # ✅ Check confirmed values
    # if not st.session_state.get("confirmed_empcode") or not st.session_state.get("confirmed_firstname"):
    #     st.error("❌ Ажилтны мэдээлэл баталгаажаагүй байна. Эхний алхмыг дахин шалгана уу.")
    #     st.stop()
    
    logo()
    col1,col2 =  st.columns(2)

    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }

                div[data-testid="stTextInputRootElement"]{
                    height: 60vh;
                    align-items: start;
                    background: #ffff;
                    box-shadow: -1px 0px 5px 1px rgba(186,174,174,0.75);
                    border-radius: 20px;
                }
                
                div[data-testid="stTextInput"] label p{
                    background: #ffff;
                    font-size: 1em;
                }
                div[data-testid="stTextInputRootElement"] input{
                    background: #ffff;
                    font-size: 1.5em;
                    padding-top: 0.5em;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em;">
                    <p style="display:table-cell; vertical-align: middle;"> Та байгууллагын соёл, багийн уур амьсгалыг<span style="color: #ec1c24;"> өөрчлөх, сайжруулах </span> талаарх саналаа бичнэ үү?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        text_input = st.text_input(label="ТАНЫ САНАЛ", placeholder="Та өөрийн бодлоо дэлгэрэнгүй бичнэ үү")

    progress_chart()

        # --- Get selected value ---
        # st.write("You selected:", choice)
    


# ---- SURVEY QUESTION 3 ----
elif st.session_state.page == 3:
    logo()
    col1,col2 =  st.columns(2)

    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em; height:60vh; display:table; ">
                    <p style="display:table-cell; vertical-align: middle;"> Таны бодлоор <span style="color: #ec1c24;">  байгууллагын соёлоо </span> тодорхойлбол</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <style>
                    
                /* Hide default radio buttons */
                div[data-testid="stRadio"] > div > label > div:first-child {
                    display: none !important;
                }
                    
              /* area that contains the text (Streamlit wraps text inside a div) */
                div[data-testid="stRadio"] label > div {
                    /* respect newline characters in the option strings */
                    white-space: pre-line;
                }

                /* Style radio group container */
                div[data-testid="stRadio"] > div {
                    gap: 10px;
                    justify-content: center;
                    align-items: center;
                }

                /* Style each radio option like a button */
                div[data-testid="stRadio"] label {
                    background-color: #fff;       /* default background */
                    width: 100%;
                    padding: 8px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    border: 1px solid #ccc;
                    transition: background-color 0.2s;
                    text-align: left;
                    align-items: start;
                    color: #808080;
                }
                    
                /* "H1"-like first line */
                div[data-testid="stRadio"] label > div::first-line {
                    font-size: 2em;
                    font-weight: 700;
                    color: #111827;
                }
                        
                label[data-testid="stWidgetLabel"]{
                    border: 0px !important;
                    font-size: 2px !important;
                    color: #898989;
                }

                /* Hover effect */
                div[data-testid="stRadio"] label:hover {
                    border-color: #ec1c24;
                }

                /* Checked/selected option */
                div[data-testid="stRadio"] input:checked + label {
                    background-color: #FF0000 !important; /* selected color */
                    color: white !important;
                    border-color: #ec1c24 !important;
                }
                    
                /* --- Layout as grid (2 rows × 4 columns) --- */
                div[data-testid="stRadio"] > div[role="radiogroup"]{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);  /* 4 columns */
                    grid-template-rows: repeat(4, auto);     /* 2 rows */
                    gap: 20px;
                }
                        
            </style>
            """, unsafe_allow_html=True)
        
       
        options = [
           "Caring\nМанай байгууллага ажилтнууд хамтран ажиллахад таатай газар бөгөөд ажилтнууд бие биеэ дэмжиж нэг гэр бүл шиг ажилладаг.", "Purpose\nМанай байгууллага нийгэмд эерэг нөлөө үзүүлэхийн төлөө урт хугацааны зорилготой ажилладаг", "Learning\nХэлж мэдэхгүй байна", "Enjoyment\nБага зэрэг санал нийлж байна", "Result\nБүрэн санал нийлж байна", "Authority\nХэлж мэдэхгүй байна", "Safety\nБага зэрэг санал нийлж байна", "Order\nБүрэн санал нийлж байна"
        ]
        # --- Create radio group ---
        choice = st.radio(
            "",
            options,
            key="button_radio"
        )
        answer_key = "Alignment_with_Daily_Tasks"


        # --- Get selected value ---
        st.write("You selected:", choice)

    progress_chart()


    # survey_type = st.session_state.survey_type
    # if survey_type == "1 жил хүртэл":
    #     st.header("1. Ажлын байрны тодорхойлолт болон өдөр тутмын ажил үүрэг таны **хүлээлтэд** нийцсэн үү?")
    #     q1 = st.radio(
    #         "Таны үнэлгээ (1–5 од):",
    #         ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
    #         key="q1_1jil",
    #         index=None
    #     )
    #     answer_key = "Alignment_with_Daily_Tasks"

    # elif survey_type == "1-ээс дээш":
    #     st.header("1. Ажлын байрны тодорхойлолт таны өдөр тутмын ажил үүрэгтэй нийцэж байсан уу?")
    #     q1 = st.radio(
    #         "Таны үнэлгээ (1–5 од):",
    #         ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
    #         key="q1_1deesh",
    #         index=None
    #     )
    #     answer_key = "Unexpected_Responsibilities"

    # elif survey_type == "6 сар дотор гарч байгаа":
    #     st.header("1. Танд ажлаас гарахад нөлөөлсөн хүчин зүйл, шалтгааны талаар дэлгэрэнгүй хэлж өгнө үү?")
    #     q1_choices = [
    #         "🚀 Career Advancement",
    #         "💰 Compensation",
    #         "⚖️ Work-Life Balance",
    #         "🧑‍💼 Management",
    #         "😊 Job Satisfaction",
    #         "🏢 Company Culture",
    #         "📦 Relocation",
    #         "🧘 Personal Reasons",
    #         "📨 Better Opportunity, offer",
    #         "🏗️ Work Conditions"
    #     ]
    #     q1 = st.radio("Үндсэн шалтгаанууд:", q1_choices, key="q1_6sar", index=None)
    #     answer_key = "Reason_for_Leaving"

    # elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
    #     st.header("1. Танд ажлаас гарахад нөлөөлсөн хүчин зүйл, шалтгааны талаар дэлгэрэнгүй хэлж өгнө үү?")
    #     q1_choices = [
    #         "🚀 Career Advancement",
    #         "💰 Compensation",
    #         "⚖️ Work-Life Balance",
    #         "🧑‍💼 Management",
    #         "😊 Job Satisfaction",
    #         "🏢 Company Culture",
    #         "📦 Relocation",
    #         "🧘 Хувийн шалтгаан / Personal Reasons",
    #         "📨 Илүү боломжийн өөр ажлын байрны санал авсан / Better Opportunity, offer",
    #         "🏗️ Ажлын нөхцөл / Work Conditions"
    #     ]
    #     q1 = st.radio("Үндсэн шалтгаанууд:", q1_choices, key="q1_busad", index=None)
    #     answer_key = "Reason_for_Leaving"

    # # Save answer and move to next page
    # if q1 is not None and st.button("Дараагийн асуулт", key="btn_next_q1"):
    #     st.session_state.answers[answer_key] = q1
    #     st.session_state.page = 4
    #     st.rerun()



elif st.session_state.page == 4:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q2 = None
    answer_key = None

    if survey_type == "1 жил хүртэл":
        st.header("2. Дасан зохицох хөтөлбөрийн хэрэгжилт эсвэл баг хамт олон болон шууд удирдлага таньд өдөр тутмын процесс, үүрэг даалгаваруудыг хурдан ойлгоход туслах хангалттай мэдээлэл, заавар өгч чадсан уу?")
        q2_choices = [
            "Маш сайн мэдээлэл заавар өгдөг. /5/",
            "Сайн мэдээлэл, заавар өгч байсан. /4/",
            "Дунд зэрэг мэдээлэл, заавар өгсөн. /3/",
            "Муу мэдээлэл, заавар өгсөн /2/",
            "Хангалтгүй /1/"
        ]
        q2 = st.radio("Таны үнэлгээ:", q2_choices, key='Onboarding_Effectiveness', index=None)
        answer_key = "Onboarding_Effectiveness"

    elif survey_type == "1-ээс дээш":
        st.header("2. Таны бодлоор байгууллагын соёлоо тодорхойлбол:")
        q2_choices = [
            "**Caring** – Манай байгууллага ажилтнууд хамтран ажиллахад таатай газар бөгөөд ажилтнууд бие биеэ дэмжиж нэг гэр бүл шиг ажилладаг.",
            "**Purpose** – Манай байгууллага нийгэмд эерэг нөлөө үзүүлэхийн төлөө урт хугацааны зорилготой ажилладаг.",
            "**Learning** – Манай байгууллага бүтээлч, нээлттэй сэтгэлгээг дэмждэг бөгөөд ажилтнууд нь тасралтгүй суралцах хүсэл тэмүүлэлтэй байдаг.",
            "**Enjoyment** – Манай байгууллагын ажилтнууд чөлөөтэй ажиллах боломжтой ба ажилдаа дуртай, эрч хүчтэй уур амьсгалтай байдаг.",
            "**Result** – Манай байгууллагын ажилтнууд нь хамгийн сайн гүйцэтгэл, үр дүнд чиглэж ажилладаг.",
            "**Authority** – Манай байгууллага өрсөлдөөн ихтэй газар бөгөөд ажилтнууд өөрсдийн давуу талыг бий болгохыг хичээдэг.",
            "**Safety** – Манай байгууллага ажилтнууд аливаа ажлыг хийхдээ маш няхуур, аюулгүй байдлыг бодож ажилладаг бөгөөд үр дүнг урьдчилан таамаглан, харж чаддаг.",
            "**Order** – Манай байгууллага нь ажлын зохион байгуулалт өндөртэй, тодорхой дүрэм журам, тогтсон процесстой байдаг."
        ]
        q2 = st.radio("Таны сонголт:", q2_choices, key='Company_Culture', index=None)
        answer_key = "Company_Culture"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("2. Ажлын байрны тодорхойлолт болон өдөр тутмын ажил үүрэг таны **хүлээлтэд** нийцсэн үү?")
        q2 = st.radio("Таны үнэлгээ (1–5 од):", ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], key='Alignment_with_Daily_Tasks', index=None)
        answer_key = "Alignment_with_Daily_Tasks"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("2. Ажлын байрны тодорхойлолт таны өдөр тутмын ажил үүрэгтэй нийцэж байсан уу?")
        q2 = st.radio("Таны үнэлгээ (1–5 од):", ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], key='Unexpected_Responsibilities', index=None)
        answer_key = "Unexpected_Responsibilities"

    # Save and go to next page if answered
    if q2 is not None and st.button("Дараагийн асуулт", key="btn_next_q2"):
        st.session_state.answers[answer_key] = q2
        st.session_state.page = 5
        st.rerun()


# ---- PAGE 5: Q3 (Organizational Culture Description) ----
elif st.session_state.page == 5:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    if survey_type == "1 жил хүртэл":
        st.header("3. Таны бодлоор байгууллагын соёлоо тодорхойлбол:")
        q3_choices = [
            "**Caring** – Манай байгууллага ажилтнууд хамтран ажиллахад таатай газар бөгөөд ажилтнууд бие биеэ дэмжиж нэг гэр бүл шиг ажилладаг.",
            "**Purpose** – Манай байгууллага нийгэмд эерэг нөлөө үзүүлэхийн төлөө урт хугацааны зорилготой ажилладаг.",
            "**Learning** – Манай байгууллага бүтээлч, нээлттэй сэтгэлгээг дэмждэг бөгөөд ажилтнууд нь тасралтгүй суралцах хүсэл тэмүүлэлтэй байдаг.",
            "**Enjoyment** – Манай байгууллагын ажилтнууд чөлөөтэй ажиллах боломжтой ба ажилдаа дуртай, эрч хүчтэй уур амьсгалтай байдаг.",
            "**Result** – Манай байгууллагын ажилтнууд нь хамгийн сайн гүйцэтгэл, үр дүнд чиглэж ажилладаг.",
            "**Authority** – Манай байгууллага өрсөлдөөн ихтэй газар бөгөөд ажилтнууд өөрсдийн давуу талыг бий болгохыг хичээдэг.",
            "**Safety** – Манай байгууллага ажилтнууд аливаа ажлыг хийхдээ маш няхуур, аюулгүй байдлыг бодож ажилладаг бөгөөд үр дүнг урьдчилан таамаглан, харж чаддаг.",
            "**Order** – Манай байгууллага нь ажлын зохион байгуулалт өндөртэй, тодорхой дүрэм журам, тогтсон процесстой байдаг."
        ]
        q_answer = st.radio("Таны сонголт:", q3_choices, key="q3_1jil", index=None)
        answer_key = "Company_Culture"

    elif survey_type == "1-ээс дээш":
        st.header("3. Манай байгууллагын ажилтнууд хоорондоо хүндэтгэлтэй харилцаж бие биенээ дэмждэг")
        q3_choices = [
            "Бүрэн санал нийлж байна /5/ ❤️✨",
            "Бага зэрэг санал нийлж байна. /4/ 🙂🌟",
            "Хэлж мэдэхгүй байна. /3/ 😒🤷",
            "Санал нийлэхгүй байна. /2/ 😕⚠️",
            "Огт санал нийлэхгүй байна /1/ 💢🚫"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q3_choices, key="q3_1deesh", index=None)
        answer_key = "Atmosphere"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("3. Дасан зохицох хөтөлбөрийн хэрэгжилт эсвэл баг хамт олон болон шууд удирдлага таньд өдөр тутмын процесс, үүрэг даалгаваруудыг хурдан ойлгоход туслах хангалттай мэдээлэл, заавар өгч чадсан уу?")
        q3_choices = [
            "Маш сайн мэдээлэл заавар өгдөг. /5/",
            "Сайн мэдээлэл, заавар өгч байсан. /4/",
            "Дунд зэрэг мэдээлэл, заавар өгсөн. /3/",
            "Муу мэдээлэл, заавар өгсөн /2/",
            "Хангалтгүй /1/"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q3_choices, key="q3_6s", index=None)
        answer_key = "Onboarding_Effectiveness"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("3. Таны бодлоор байгууллагын соёлоо тодорхойлбол:")
        q3_choices = [
            "**Caring** – Манай байгууллага ажилтнууд хамтран ажиллахад таатай газар бөгөөд ажилтнууд бие биеэ дэмжиж нэг гэр бүл шиг ажилладаг.",
            "**Purpose** – Манай байгууллага нийгэмд эерэг нөлөө үзүүлэхийн төлөө урт хугацааны зорилготой ажилладаг.",
            "**Learning** – Манай байгууллага бүтээлч, нээлттэй сэтгэлгээг дэмждэг бөгөөд ажилтнууд нь тасралтгүй суралцах хүсэл тэмүүлэлтэй байдаг.",
            "**Enjoyment** – Манай байгууллагын ажилтнууд чөлөөтэй ажиллах боломжтой ба ажилдаа дуртай, эрч хүчтэй уур амьсгалтай байдаг.",
            "**Result** – Манай байгууллагын ажилтнууд нь хамгийн сайн гүйцэтгэл, үр дүнд чиглэж ажилладаг.",
            "**Authority** – Манай байгууллага өрсөлдөөн ихтэй газар бөгөөд ажилтнууд өөрсдийн давуу талыг бий болгохыг хичээдэг.",
            "**Safety** – Манай байгууллага ажилтнууд аливаа ажлыг хийхдээ маш няхуур, аюулгүй байдлыг бодож ажилладаг бөгөөд үр дүнг урьдчилан таамаглан, харж чаддаг.",
            "**Order** – Манай байгууллага нь ажлын зохион байгуулалт өндөртэй, тодорхой дүрэм журам, тогтсон процесстой байдаг."
        ]
        q_answer = st.radio("Таны сонголт:", q3_choices, key="q3_3s+", index=None)
        answer_key = "Company_Culture"

    # Save and go to next page
    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q5"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 6
        st.rerun()


#---- PAGE 6: Q4
elif st.session_state.page == 6:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type
    q_answer = None
    answer_key = ""


    if survey_type == "1 жил хүртэл":
        st.header("4. Манай байгууллагын ажилтнууд хоорондоо хүндэтгэлтэй харилцаж бие биенээ дэмждэг")
        q4_choices = [
            "Бүрэн санал нийлж байна /5/ ❤️✨",
            "Бага зэрэг санал нийлж байна. /4/ 🙂🌟",
            "Хэлж мэдэхгүй байна. /3/ 😒🤷",
            "Санал нийлэхгүй байна. /2/ 😕⚠️",
            "Огт санал нийлэхгүй байна /1/ 💢🚫"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q4_choices, key="q4_1jil", index=None)
        answer_key = "Atmosphere"

    elif survey_type == "1-ээс дээш":
        st.header("4. Таны шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q4_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q4_choices, key="q4_1deesh_conflict", index=None)
        answer_key = "Conflict_Resolution"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("4. Таны бодлоор байгууллагын соёлоо тодорхойлбол:")
        q4_choices = [
            "**Caring** – Манай байгууллага ажилтнууд хамтран ажиллахад таатай газар бөгөөд ажилтнууд бие биеэ дэмжиж нэг гэр бүл шиг ажилладаг.",
            "**Purpose** – Манай байгууллага нийгэмд эерэг нөлөө үзүүлэхийн төлөө урт хугацааны зорилготой ажилладаг.",
            "**Learning** – Манай байгууллага бүтээлч, нээлттэй сэтгэлгээг дэмждэг бөгөөд ажилтнууд нь тасралтгүй суралцах хүсэл тэмүүлэлтэй байдаг.",
            "**Enjoyment** – Манай байгууллагын ажилтнууд чөлөөтэй ажиллах боломжтой ба ажилдаа дуртай, эрч хүчтэй уур амьсгалтай байдаг.",
            "**Result** – Манай байгууллагын ажилтнууд нь хамгийн сайн гүйцэтгэл, үр дүнд чиглэж ажилладаг.",
            "**Authority** – Манай байгууллага өрсөлдөөн ихтэй газар бөгөөд ажилтнууд өөрсдийн давуу талыг бий болгохыг хичээдэг.",
            "**Safety** – Манай байгууллага ажилтнууд аливаа ажлыг хийхдээ маш няхуур, аюулгүй байдлыг бодож ажилладаг бөгөөд үр дүнг урьдчилан таамаглан, харж чаддаг.",
            "**Order** – Манай байгууллага нь ажлын зохион байгуулалт өндөртэй, тодорхой дүрэм журам, тогтсон процесстой байдаг."
        ]
        q_answer = st.radio("Таны сонголт:", q4_choices, key="q4_6s_culture", index=None)
        answer_key = "Company_Culture"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("4. Манай байгууллагын ажилтнууд хоорондоо хүндэтгэлтэй харилцаж бие биенээ дэмждэг")
        q4_choices = [
            "Бүрэн санал нийлж байна /5/ ❤️✨",
            "Бага зэрэг санал нийлж байна. /4/ 🙂🌟",
            "Хэлж мэдэхгүй байна. /3/ 😒🤷",
            "Санал нийлэхгүй байна. /2/ 😕⚠️",
            "Огт санал нийлэхгүй байна /1/ 💢🚫"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q4_choices, key="q4_3splus", index=None)
        answer_key = "Atmosphere"

    # Save and go to next page
    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q6"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 7
        st.rerun()


#---- PAGE 7: Q5
elif st.session_state.page == 7:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type == "1 жил хүртэл":
        st.header("5. Таны шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q5_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q5_choices, key="q5_1jil", index=None)
        answer_key = "Conflict_Resolution"

    elif survey_type == "1-ээс дээш":
        st.header("5. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажилладаг байсан уу?")
        q5_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q5_choices, key="q5_1deesh", index=None)
        answer_key = "Feedback"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("5. Манай байгууллагын ажилтнууд хоорондоо хүндэтгэлтэй харилцаж бие биенээ дэмждэг")
        q5_choices = [
            "Бүрэн санал нийлж байна /5/ ❤️✨",
            "Бага зэрэг санал нийлж байна. /4/ 🙂🌟",
            "Хэлж мэдэхгүй байна. /3/ 😒🤷",
            "Санал нийлэхгүй байна. /2/ 😕⚠️",
            "Огт санал нийлэхгүй байна /1/ 💢🚫"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q5_choices, key="q5_6s", index=None)
        answer_key = "Atmosphere"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("5. Таны шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q5_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q5_choices, key="q5_3splus", index=None)
        answer_key = "Conflict_Resolution"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q6"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 8
        st.rerun()



#---- PAGE 8: Q6
elif st.session_state.page == 8:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type == "1 жил хүртэл":
        st.header("6. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажилладаг байсан уу?")
        q6_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q6_choices, key="q6_1jil", index=None)
        answer_key = "Feedback"

    elif survey_type == "1-ээс дээш":
        st.header("6. Таны бодлоор ямар манлайллын хэв маяг таны удирдлагыг хамгийн сайн илэрхийлэх вэ?")

        q6_choices = [
            "**Visionary leadership** – Алсын хараатай удирдагч",
            "**Coaching leadership** – Тогтмол санал солилцох, зөвлөх зарчмаар хамтран ажилладаг удирдлага",
            "**Authoritarian/Boss leadership** – Багийнхаа санаа бодлыг сонсдоггүй, өөрөө бие даан шийдвэр гаргалт хийдэг, гол дүр болж ажиллах дуртай удирдлага",
            "**Transformational leadership** – Хувь хүний хөгжлийг дэмждэг удирдагч",
            "**Transactional leadership** – Шагнал, шийтгэлийн системээр удирддаг",
            "**Participative leadership** – Багийн гишүүдийн оролцоог дэмжин, хамтдаа шийдвэр гарган хамтран ажилладаг",
            "**Laissez-Faire leadership** – Хөндлөнгөөс оролцдоггүй, багийн гишүүдийг өөрсдийг нь шийдвэр гаргахад боломж олгодог"
        ]

        q_answer = st.radio("Сонголтоо хийнэ үү:", q6_choices, key="q6_1deesh", index=None)
        answer_key = "Leadership_Style"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("6. Таны шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q6_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("Таны үнэлгээ:", q6_choices, key="q6_6sae", index=None)
        answer_key = "Conflict_Resolution"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("6. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажилладаг байсан уу?")
        q6_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q6_choices, key="q6_busad", index=None)
        answer_key = "Feedback"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q6"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 9
        st.rerun()



# ---- PAGE 9: Q7 – Leadership Style ----
elif st.session_state.page == 9:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    q7_choices = [
        "**Visionary leadership** – Алсын хараатай удирдагч",
        "**Coaching leadership** – Тогтмол санал солилцох, зөвлөх зарчмаар хамтран ажилладаг удирдлага",
        "**Authoritarian/Boss leadership** – Багийнхаа санаа бодлыг сонсдоггүй, өөрөө бие даан шийдвэр гаргалт хийдэг, гол дүр болж ажиллах дуртай удирдлага",
        "**Transformational leadership** – Хувь хүний хөгжлийг дэмждэг удирдагч",
        "**Transactional leadership** – Шагнал, шийтгэлийн системээр удирддаг",
        "**Participative leadership** – Багийн гишүүдийн оролцоог дэмжин, хамтдаа шийдвэр гарган хамтран ажилладаг",
        "**Laissez-Faire leadership** – Хөндлөнгөөс оролцдоггүй, багийн гишүүдийг өөрсдийг нь шийдвэр гаргахад боломж олгодог"
    ]

    if survey_type == "1 жил хүртэл":
        st.header("7. Таны бодлоор ямар манлайллын хэв маяг таны удирдлагыг хамгийн сайн илэрхийлэх вэ?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", q7_choices, key="q7_1jil", index=None)
        answer_key = "Leadership_Style"

    elif survey_type == "1-ээс дээш":
        st.header("7. Та баг доторх хамтын ажиллагаа болон хоорондын харилцаанд хэр сэтгэл хангалуун байсан бэ?")
        q8_choices = [
            "🟩🟩🟩🟩   —  Багийн ажиллагаа гайхалтай сайн байсан",
            "🟩🟩🟩⬜   —  Сайн багийн уур амьсгал эерэг байсан",
            "🟩🟩⬜⬜   —  Дунд зэрэг. Илүү сайн байж болох л байх",
            "🟩⬜⬜⬜   —  Хамтран ажиллахад хэцүү, зөрчилдөөнтэй байсан",
            "⬜⬜⬜⬜   —  Хэлж мэдэхгүй байна"
        ]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q8_choices, key="q7_1deesh", index=None)
        answer_key = "Team_Collaboration"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("7. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажилладаг байсан уу?")
        q6_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q6_choices, key="q7_6sar", index=None)
        answer_key = "Feedback"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("7. Таны бодлоор ямар манлайллын хэв маяг таны удирдлагыг хамгийн сайн илэрхийлэх вэ?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", q7_choices, key="q7_busad", index=None)
        answer_key = "Leadership_Style"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q7"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 10
        st.rerun()

    


# ---- PAGE 10: Q8 – Team Collaboration ----
elif st.session_state.page == 10:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type == "1 жил хүртэл":
        st.header("8. Та баг доторх хамтын ажиллагаа болон хоорондын харилцаанд хэр сэтгэл хангалуун байсан бэ?")
        q8_choices = [
            "🟩🟩🟩🟩   —  Багийн ажиллагаа гайхалтай сайн байсан",
            "🟩🟩🟩⬜   —  Сайн багийн уур амьсгал эерэг байсан",
            "🟩🟩⬜⬜   —  Дунд зэрэг. Илүү сайн байж болох л байх",
            "🟩⬜⬜⬜   —  Хамтран ажиллахад хэцүү, зөрчилдөөнтэй байсан",
            "⬜⬜⬜⬜   —  Хэлж мэдэхгүй байна"
        ]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q8_choices, key="q8_1jil", index=None)
        answer_key = "Team_Collaboration"

    elif survey_type == "1-ээс дээш":
        st.header("8. Та байгууллагын соёл, багийн уур амьсгалыг өөрчлөх, сайжруулах талаарх саналаа бичнэ үү?")
        q_answer = st.text_area("Таны санал:", key="q8_1deesh")
        answer_key = "Team_Support"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("8. Таны бодлоор ямар манлайллын хэв маяг таны удирдлагыг хамгийн сайн илэрхийлэх вэ?")
        q8_choices = [
            "**Visionary leadership** – Алсын хараатай удирдагч",
            "**Coaching leadership** – Тогтмол санал солилцох, зөвлөх зарчмаар хамтран ажилладаг удирдлага",
            "**Authoritarian/Boss leadership** – Багийнхаа санаа бодлыг сонсдоггүй, өөрөө бие даан шийдвэр гаргалт хийдэг, гол дүр болж ажиллах дуртай удирдлага",
            "**Transformational leadership** – Хувь хүний хөгжлийг дэмждэг удирдагч",
            "**Transactional leadership** – Шагнал, шийтгэлийн системээр удирддаг",
            "**Participative leadership** – Багийн гишүүдийн оролцоог дэмжин, хамтдаа шийдвэр гарган хамтран ажилладаг",
            "**Laissez-Faire leadership** – Хөндлөнгөөс оролцдоггүй, багийн гишүүдийг өөрсдийг нь шийдвэр гаргахад боломж олгодог"
        ]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q8_choices, key="q8_6sar", index=None)
        answer_key = "Leadership_Style"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("8. Та баг доторх хамтын ажиллагаа болон хоорондын харилцаанд хэр сэтгэл хангалуун байсан бэ?")
        q8_choices = [
            "🟩🟩🟩🟩   —  Багийн ажиллагаа гайхалтай сайн байсан",
            "🟩🟩🟩⬜   —  Сайн багийн уур амьсгал эерэг байсан",
            "🟩🟩⬜⬜   —  Дунд зэрэг. Илүү сайн байж болох л байх",
            "🟩⬜⬜⬜   —  Хамтран ажиллахад хэцүү, зөрчилдөөнтэй байсан",
            "⬜⬜⬜⬜   —  Хэлж мэдэхгүй байна"
        ]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q8_choices, key="q8_busad", index=None)
        answer_key = "Team_Collaboration"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q8"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 11
        st.rerun()




# ---- PAGE 11: Q9 – Open text comment ----
elif st.session_state.page == 11:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type == "1 жил хүртэл":
        st.header("9. Та байгууллагын соёл, багийн уур амьсгалыг өөрчлөх, сайжруулах талаарх саналаа бичнэ үү?")
        q_answer = st.text_area("Таны санал:", key="q9_1jil")
        answer_key = "Team_Support"

    elif survey_type == "1-ээс дээш":
        st.header("9. Танд өдөр тутмын ажлаа урам зоригтой хийхэд ямар ямар хүчин зүйлс нөлөөлдөг байсан бэ?")

        q9_choices = [
            "Цалин",
            "Баг хамт олны дэмжлэг",
            "Сурч хөгжих боломжоор хангагддаг байсан нь",
            "Олон нийтийн үйл ажиллагаа",
            "Шударга, нээлттэй харилцаа",
            "Шагнал урамшуулал",
            "Ажлын орчин",
            "Төсөл, хөтөлбөрүүд",
            "Бусад (тайлбар оруулах)"
        ]

        q9_selected = st.multiselect("Сонголтууд:", q9_choices, key="q9_1deesh")
        q9_other = ""

        if "Бусад (тайлбар оруулах)" in q9_selected:
            q9_other = st.text_area("Та бусад нөлөөлсөн хүчин зүйлсийг бичнэ үү:", key="q9_other")

        # Combine selected values except 'Бусад'
        q_answer_main = ", ".join([item for item in q9_selected if item != "Бусад (тайлбар оруулах)"])
        q_answer_other = q9_other.strip() if q9_other.strip() else ""

        if st.button("Дараагийн асуулт", key="btn_next_q9"):
            st.session_state.answers["Motivation"] = q_answer_main
            st.session_state.answers["Motivation_Other"] = q_answer_other
            st.session_state.page = 12
            st.rerun()

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("9. Та баг доторх хамтын ажиллагаа болон хоорондын харилцаанд хэр сэтгэл хангалуун байсан бэ?")
        q9_choices = [
            "🟩🟩🟩🟩   —  Багийн ажиллагаа гайхалтай сайн байсан",
            "🟩🟩🟩⬜   —  Сайн багийн уур амьсгал эерэг байсан",
            "🟩🟩⬜⬜   —  Дунд зэрэг. Илүү сайн байж болох л байх",
            "🟩⬜⬜⬜   —  Хамтран ажиллахад хэцүү, зөрчилдөөнтэй байсан",
            "⬜⬜⬜⬜   —  Хэлж мэдэхгүй байна"
        ]
        q_answer = st.radio("Сонголтоо хийнэ үү:", q9_choices, key="q9_6sar", index=None)
        answer_key = "Team_Collaboration"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("9. Та байгууллагын соёл, багийн уур амьсгалыг өөрчлөх, сайжруулах талаарх саналаа бичнэ үү?")
        q_answer = st.text_area("Таны санал:", key="q9_busad")
        answer_key = "Team_Support"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q9"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 12
        st.rerun()



# ---- PAGE 12: Q10 – Motivation open text ----
elif st.session_state.page == 12:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("10. Танд өдөр тутмын ажлаа урам зоригтой хийхэд ямар ямар хүчин зүйлс нөлөөлдөг байсан бэ?")

        q10_choices = [
            "Цалин",
            "Баг хамт олны дэмжлэг",
            "Сурч хөгжих боломжоор хангагддаг байсан нь",
            "Олон нийтийн үйл ажиллагаа",
            "Шударга, нээлттэй харилцаа",
            "Шагнал урамшуулал",
            "Ажлын орчин",
            "Төсөл, хөтөлбөрүүд",
            "Бусад (тайлбар оруулах)"
        ]

        q10_selected = st.multiselect("Сонголтууд:", q10_choices, key="q10_multi")

        q10_other = ""
        if "Бусад (тайлбар оруулах)" in q10_selected:
            q10_other = st.text_area("Та бусад нөлөөлсөн хүчин зүйлсийг бичнэ үү:", key="q10_other")

        if st.button("Дараагийн асуулт", key="btn_next_q10"):
            st.session_state.answers["Motivation"] = ", ".join(
                [item for item in q10_selected if item != "Бусад (тайлбар оруулах)"]
            )
            if q10_other.strip():
                st.session_state.answers["Motivation_Other"] = q10_other.strip()
            st.session_state.page = 13
            st.rerun()

    elif survey_type == "1-ээс дээш":
        st.header("10. Таны бодлоор ажилтны оролцоо, урам зоригийг нэмэгдүүлэхийн тулд компани юу хийх ёстой вэ?")

        q10_options = [
            "Удирдлагын харилцааны соёл, хандлагыг сайжруулах",
            "Ажилтны санал санаачилгыг үнэлж дэмжих тогтолцоог бий болгох",
            "Шударга, ил тод шагнал урамшууллын системтэй байх",
            "Ажилтны ур чадвар хөгжүүлэх сургалт, боломжийг нэмэгдүүлэх",
            "Багийн дотоод уур амьсгал, хамтын ажиллагааг сайжруулах (team building)",
            "Уян хатан ажлын цаг, ажлын орчин бүрдүүлэх",
            "Ажлын ачааллыг тэнцвэржүүлэх",
            "Карьер өсөлт, албан тушаал дэвших зарчим нь тодорхой байх",
            "Удирдлагын зүгээс илүү их урам өгч, зөвлөх (коучинг) хандлагатай байх",
            "Бусад (та доорх хэсэгт тайлбарлана уу)"
        ]

        q10_selected = st.radio("Сонголтоо хийнэ үү:", q10_options, key="q10_radio", index=None)

        q10_other1 = ""
        if q10_selected == "Бусад (та доорх хэсэгт тайлбарлана уу)":
            q10_other1 = st.text_area("Бусад тайлбар:", key="q10_other1")

        if st.button("Дараагийн асуулт", key="btn_next_q10"):
            if q10_selected:
                st.session_state.answers["Engagement"] = q10_selected
                if q10_other1.strip():
                    st.session_state.answers["Engagement_Other"] = q10_other1.strip()
                st.session_state.page = 13
                st.rerun()

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("10. Та байгууллагын соёл, багийн уур амьсгалыг өөрчлөх, сайжруулах талаарх саналаа бичнэ үү?")
        q_answer = st.text_area("Таны санал:", key="q10_6sar")

        if q_answer and st.button("Дараагийн асуулт", key="btn_next_q10"):
            st.session_state.answers["Team_Support"] = q_answer
            st.session_state.page = 13
            st.rerun()



# ---- PAGE 13: Q11 – Engagement Improvement (multi + open) ----
elif st.session_state.page == 13:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("11. Таны бодлоор ажилтны оролцоо, урам зоригийг нэмэгдүүлэхийн тулд компани юу хийх ёстой вэ?")

        q11_options = [
            "Удирдлагын харилцааны соёл, хандлагыг сайжруулах",
            "Ажилтны санал санаачилгыг үнэлж дэмжих тогтолцоог бий болгох",
            "Шударга, ил тод шагнал урамшууллын системтэй байх",
            "Ажилтны ур чадвар хөгжүүлэх сургалт, боломжийг нэмэгдүүлэх",
            "Багийн дотоод уур амьсгал, хамтын ажиллагааг сайжруулах (team building)",
            "Уян хатан ажлын цаг, ажлын орчин бүрдүүлэх",
            "Ажлын ачааллыг тэнцвэржүүлэх",
            "Карьер өсөлт, албан тушаал дэвших зарчим нь тодорхой байх",
            "Удирдлагын зүгээс илүү их урам өгч, зөвлөх (коучинг) хандлагатай байх",
            "Бусад (та доорх хэсэгт тайлбарлана уу)"
        ]

        q11_selected = st.radio("Сонголтоо хийнэ үү:", q11_options, key="q11_radio", index=None)

        q11_other = ""
        if q11_selected == "Бусад (та доорх хэсэгт тайлбарлана уу)":
            q11_other = st.text_area("Бусад тайлбар:", key="q11_other")

        if st.button("Дараагийн асуулт", key="btn_next_q11"):
            if q11_selected:
                st.session_state.answers["Engagement"] = q11_selected
                if q11_other.strip():
                    st.session_state.answers["Engagement_Other"] = q11_other.strip()
                st.session_state.page = 14
                st.rerun()

    elif survey_type == "1-ээс дээш":
        st.header("11. Компани ажиллах таатай нөхцөлөөр ханган дэмжин ажиллаж байсан уу?")
        q_answer = st.select_slider("Үнэлгээ:", options=["Хангалтгүй", "Дунд зэрэг", "Сайн", "Маш сайн"], key="q11_1deesh")
        if q_answer and st.button("Дараагийн асуулт", key="btn_next_q11"):
            st.session_state.answers["Well_being"] = q_answer
            st.session_state.page = 14
            st.rerun()

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("11. Танд өдөр тутмын ажлаа урам зоригтой хийхэд ямар ямар хүчин зүйлс нөлөөлдөг байсан бэ?")

        q11_choices = [
            "Цалин",
            "Баг хамт олны дэмжлэг",
            "Сурч хөгжих боломжоор хангагддаг байсан нь",
            "Олон нийтийн үйл ажиллагаа",
            "Шударга, нээлттэй харилцаа",
            "Шагнал урамшуулал",
            "Ажлын орчин",
            "Төсөл, хөтөлбөрүүд",
            "Бусад (тайлбар оруулах)"
        ]

        q11_selected = st.multiselect("Сонголтууд:", q11_choices, key="q11_multi")

        q11_other = ""
        if "Бусад (тайлбар оруулах)" in q11_selected:
            q11_other = st.text_area("Та бусад нөлөөлсөн хүчин зүйлсийг бичнэ үү:", key="q11_other")

        if st.button("Дараагийн асуулт", key="btn_next_q11"):
            st.session_state.answers["Motivation"] = ", ".join(
                [item for item in q11_selected if item != "Бусад (тайлбар оруулах)"]
            )
            if q11_other.strip():
                st.session_state.answers["Motivation_Other"] = q11_other.strip()
            st.session_state.page = 14
            st.rerun()


# ---- PAGE 14: Q12 – Slider Satisfaction ----
elif st.session_state.page == 14:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("12. Компани ажиллах таатай нөхцөлөөр ханган дэмжин ажиллаж байсан уу?")
        q_answer = st.select_slider("Үнэлгээ:", options=["Хангалтгүй", "Дунд зэрэг", "Сайн", "Маш сайн"], key="q12_slider")
        answer_key = "Well_being"

    elif survey_type == "1-ээс дээш":
        st.header("12. Таны цалин хөлс ажлын гүйцэтгэлтэй хэр нийцэж байсан бэ?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Маш сайн нийцдэг",
            "Дундаж, илүү дээр байж болох л байх",
            "Миний гүйцэтгэлтэй нийцдэггүй"
        ], key="q12_radio", index=None)
        answer_key = "Performance_Compensation"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("12. Таны бодлоор ажилтны оролцоо, урам зоригийг нэмэгдүүлэхийн тулд компани юу хийх ёстой вэ?")

        q12_options = [
            "Удирдлагын харилцааны соёл, хандлагыг сайжруулах",
            "Ажилтны санал санаачилгыг үнэлж дэмжих тогтолцоог бий болгох",
            "Шударга, ил тод шагнал урамшууллын системтэй байх",
            "Ажилтны ур чадвар хөгжүүлэх сургалт, боломжийг нэмэгдүүлэх",
            "Багийн дотоод уур амьсгал, хамтын ажиллагааг сайжруулах (team building)",
            "Уян хатан ажлын цаг, ажлын орчин бүрдүүлэх",
            "Ажлын ачааллыг тэнцвэржүүлэх",
            "Карьер өсөлт, албан тушаал дэвших зарчим нь тодорхой байх",
            "Удирдлагын зүгээс илүү их урам өгч, зөвлөх (коучинг) хандлагатай байх",
            "Бусад (та доорх хэсэгт тайлбарлана уу)"
        ]

        q12_selected = st.radio("Сонголтоо хийнэ үү:", q12_options, key="q12_options", index=None)

        q12_other = ""
        if q12_selected == "Бусад (та доорх хэсэгт тайлбарлана уу)":
            q12_other = st.text_area("Бусад тайлбар:", key="q12_other")

        if st.button("Дараагийн асуулт", key="btn_next_q12"):
            if q12_selected:
                st.session_state.answers["Engagement"] = q12_selected
                if q12_other.strip():
                    st.session_state.answers["Engagement_Other"] = q12_other.strip()
                st.session_state.page = 15
                st.rerun()

    # Shared submission for the first 2 types
    if q_answer is not None and survey_type != "6 сар дотор гарч байгаа":
        if st.button("Дараагийн асуулт", key="btn_next_q12"):
            st.session_state.answers[answer_key] = q_answer
            st.session_state.page = 15
            st.rerun()



# ---- PAGE 15: Q13 – Salary Match ----
elif st.session_state.page == 15:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("13. Таны цалин хөлс ажлын гүйцэтгэлтэй хэр нийцэж байсан бэ?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Маш сайн нийцдэг",
            "Дундаж, илүү дээр байж болох л байх",
            "Миний гүйцэтгэлтэй нийцдэггүй"
        ], key="q13_radio", index=None)
        answer_key = "Performance_Compensation"

    elif survey_type == "1-ээс дээш":
        st.header("13. Танд компаниас олгосон тэтгэмж, хөнгөлөлтүүд нь үнэ цэнтэй, ач холбогдолтой байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Тийм, үнэ цэнтэй ач холбогдолтой 💎",
            "Сайн, гэхдээ сайжруулах шаардлагатай 👍",
            "Тийм ч ач холбогдолгүй, үр ашиггүй 🤔"
        ], key="q13_benefits", index=None)
        answer_key = "Value_of_Benefits"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("13. Компани ажиллах таатай нөхцөлөөр ханган дэмжин ажиллаж байсан уу?")
        q_answer = st.select_slider("Үнэлгээ:", options=["Хангалтгүй", "Дунд зэрэг", "Сайн", "Маш сайн"], key="q13_slider")
        answer_key = "Well_being"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q13"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 16
        st.rerun()


# ---- PAGE 16: Q14 – Value of Benefits ----
elif st.session_state.page == 16:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("14. Танд компаниас олгосон тэтгэмж, хөнгөлөлтүүд нь үнэ цэнтэй, ач холбогдолтой байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Тийм, үнэ цэнтэй ач холбогдолтой 💎",
            "Сайн, гэхдээ сайжруулах шаардлагатай 👍",
            "Тийм ч ач холбогдолгүй, үр ашиггүй 🤔"
        ], key="q14_main", index=None)
        answer_key = "Value_of_Benefits"

    elif survey_type == "1-ээс дээш":
        st.header("14. Таны ажлын гүйцэтгэлийг (KPI) үнэн зөв, шударга үнэлэн дүгнэдэг байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Шударга, үнэн зөв үнэлдэг",
            "Зарим нэг үзүүлэлт зөрүүтэй үнэлдэг",
            "Үнэлгээ миний гүйцэтгэлтэй нийцдэггүй",
            "Миний гүйцэтгэлийг хэрхэн үнэлснийг би ойлгодоггүй"
        ], key="q14_1deesh", index=None)
        answer_key = "KPI_Accuracy"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("14. Таны цалин хөлс ажлын гүйцэтгэлтэй хэр нийцэж байсан бэ?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Маш сайн нийцдэг",
            "Дундаж, илүү дээр байж болох л байх",
            "Миний гүйцэтгэлтэй нийцдэггүй"
        ], key="q14_prev", index=None)
        answer_key = "Performance_Compensation"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q14"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 17
        st.rerun()


# ---- PAGE 17: Q15 – KPI Evaluation ----
elif st.session_state.page == 17:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = "q15"

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("15. Таны ажлын гүйцэтгэлийг (KPI) үнэн зөв, шударга үнэлэн дүгнэдэг байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Шударга, үнэн зөв үнэлдэг",
            "Зарим нэг үзүүлэлт зөрүүтэй үнэлдэг",
            "Үнэлгээ миний гүйцэтгэлтэй нийцдэггүй",
            "Миний гүйцэтгэлийг хэрхэн үнэлснийг би ойлгодоггүй"
        ], key="q15_main", index=None)
        answer_key = "KPI_Accuracy"

    elif survey_type == "1-ээс дээш":
        st.header("15. Таны бодлоор компанидаа ажил, мэргэжлийн хувьд өсөж, хөгжих боломж хангалттай байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Өсөж хөгжих боломж хангалттай байдаг",
            "Хангалттай биш",
            "Өсөж хөгжих боломж байгаагүй"
        ], key="q15_1deesh", index=None)
        answer_key = "Career_Growth"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("15. Танд компаниас олгосон тэтгэмж, хөнгөлөлтүүд нь үнэ цэнтэй, ач холбогдолтой байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Тийм, үнэ цэнтэй ач холбогдолтой 💎",
            "Сайн, гэхдээ сайжруулах шаардлагатай 👍",
            "Тийм ч ач холбогдолгүй, үр ашиггүй 🤔"
        ], key="q15_6sar", index=None)
        answer_key = "Value_of_Benefits"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q15"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 18
        st.rerun()


# ---- PAGE 18 ----
elif st.session_state.page == 18:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("16. Таны бодлоор компанидаа ажил, мэргэжлийн хувьд өсөж, хөгжих боломж хангалттай байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Өсөж хөгжих боломж хангалттай байдаг",
            "Хангалттай биш",
            "Өсөж хөгжих боломж байгаагүй"
        ], key="q16_main", index=None)
        answer_key = "Career_Growth"

        if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q16_main"):
            st.session_state.answers[answer_key] = q_answer
            st.session_state.page = 19
            st.rerun()

    elif survey_type == "1-ээс дээш":
        st.header("16. Компаниас зохион байгуулдаг сургалтууд чанартай, үр дүнтэй байж таныг ажил мэргэжлийн ур чадвараа нэмэгдүүлэхэд дэмжлэг үзүүлж чадсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "🌟 Маш сайн",
            "👍 Сайн, гэхдээ сайжруулах шаардлагатай",
            "❌ Үр ашиггүй"
        ], key="q16_1deesh", index=None)
        answer_key = "Traning_Quality"

        if q_answer is not None and st.button("Дуусгах", key="btn_finish_q16_1deesh"):
            st.session_state.answers[answer_key] = q_answer
            if submit_answers():
                st.success("🎉 Судалгааг амжилттай бөглөлөө. Танд баярлалаа!")
                st.balloons()


    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("16. Таны ажлын гүйцэтгэлийг (KPI) үнэн зөв, шударга үнэлэн дүгнэдэг байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Шударга, үнэн зөв үнэлдэг",
            "Зарим нэг үзүүлэлт зөрүүтэй үнэлдэг",
            "Үнэлгээ миний гүйцэтгэлтэй нийцдэггүй",
            "Миний гүйцэтгэлийг хэрхэн үнэлснийг би ойлгодоггүй"
        ], key="q16_6sar", index=None)
        answer_key = "KPI_Accuracy"

        if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q16_6sar"):
            st.session_state.answers[answer_key] = q_answer
            st.session_state.page = 19
            st.rerun()



# ---- PAGE 19 ----
elif st.session_state.page == 19:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("17. Компаниас зохион байгуулдаг сургалтууд чанартай, үр дүнтэй байж таныг ажил мэргэжлийн ур чадвараа нэмэгдүүлэхэд дэмжлэг үзүүлж чадсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "🌟 Маш сайн",
            "👍 Сайн, гэхдээ сайжруулах шаардлагатай",
            "❌ Үр ашиггүй"
        ], key="q17_main", index=None)
        answer_key = "Traning_Quality"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("17. Таны бодлоор компанидаа ажил, мэргэжлийн хувьд өсөж, хөгжих боломж хангалттай байсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Өсөж хөгжих боломж хангалттай байдаг",
            "Хангалттай биш",
            "Өсөж хөгжих боломж байгаагүй"
        ], key="q17_6sar", index=None)
        answer_key = "Career_Growth"

    if q_answer is not None:
        st.session_state.answers[answer_key] = q_answer

        if survey_type == "1 жил хүртэл":
            if st.button("Дуусгах", key="btn_finish_q17_1jil"):
                if submit_answers():
                    st.success("🎉 Судалгааг амжилттай бөглөлөө. Танд баярлалаа!")
                    st.balloons()
        else:
            if st.button("Дараагийн асуулт", key="btn_next_q17"):
                st.session_state.page = 20
                st.rerun()




# ---- PAGE 20 ----
elif st.session_state.page == 20:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header('18. Та ойрын хүрээлэлдээ "Дижитал Концепт" -т ажилд орохыг санал болгох уу?')
        q18_choices = [
            "Санал болгоно",
            "Эргэлзэж байна",
            "Санал болгохгүй /яагаад/"
        ]
        q18 = st.radio("Сонголтоо хийнэ үү:", q18_choices, key="q18", index=None)

        q18_other = ""
        if q18 == "Санал болгохгүй /яагаад/":
            q18_other = st.text_area("Яагаад санал болгохгүй гэж үзэж байна вэ?", key="q18_other")

        if st.button("Дараагийн асуулт", key="btn_next_q18"):
            st.session_state.answers["Loyalty1"] = q18
            if q18_other.strip():
                st.session_state.answers["Loyalty1_Other"] = q18_other.strip()
            st.session_state.page = 21
            st.rerun()

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("18. Компаниас зохион байгуулдаг сургалтууд чанартай, үр дүнтэй байж таныг ажил мэргэжлийн ур чадвараа нэмэгдүүлэхэд дэмжлэг үзүүлж чадсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "🌟 Маш сайн",
            "👍 Сайн, гэхдээ сайжруулах шаардлагатай",
            "❌ Үр ашиггүй"
        ], key="q18_6sar", index=None)
        answer_key = "Traning_Quality"

        if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q18_6sar"):
            st.session_state.answers[answer_key] = q_answer
            st.session_state.page = 21
            st.rerun()


# ---- PAGE 21 ----
elif st.session_state.page == 21:
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None

    if survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("19. Ирээдүйд та компанидаа эргэн орох боломж гарвал та дахин хамтран ажиллах уу?")
        q19_choices = [
            "Санал болгоно",
            "Эргэлзэж байна",
            "Санал болгохгүй /яагаад/"
        ]
        q19 = st.radio("Сонголтоо хийнэ үү:", q19_choices, key="q19", index=None)

        q19_other = ""
        if q19 == "Санал болгохгүй /яагаад/":
            q19_other = st.text_area("Яагаад санал болгохгүй гэж үзэж байна вэ?", key="q19_other")

        if st.button("Дуусгах", key="btn_finish_q19_multi"):
            st.session_state.answers["Loyalty2"] = q19
            if q19_other.strip():
                st.session_state.answers["Loyalty2_Other"] = q19_other.strip()
            if submit_answers():
                st.success("🎉 Судалгааг амжилттай бөглөлөө. Танд баярлалаа!")
                st.balloons()

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header('19. Та ойрын хүрээлэлдээ "Дижитал Концепт" -т ажилд орохыг санал болгох уу?')
        q18_choices = [
            "Санал болгоно",
            "Эргэлзэж байна",
            "Санал болгохгүй /яагаад/"
        ]
        q18 = st.radio("Сонголтоо хийнэ үү:", q18_choices, key="q18_last", index=None)

        q18_other = ""
        if q18 == "Санал болгохгүй /яагаад/":
            q18_other = st.text_area("Яагаад санал болгохгүй гэж үзэж байна вэ?", key="q18_other_last")

        if st.button("Дараагийн асуулт", key="btn_next_q19"):
            st.session_state.answers["Loyalty1"] = q18
            if q18_other.strip():
                st.session_state.answers["Loyalty1_Other"] = q18_other.strip()
            st.session_state.page = 22
            st.rerun()



# ---- PAGE 22 ----
elif st.session_state.page == 22:
    logo()
    progress_chart()

    st.header("20. Ирээдүйд та компанидаа эргэн орох боломж гарвал та дахин хамтран ажиллах уу?")
    q20_choices = [
        "Санал болгоно",
        "Эргэлзэж байна",
        "Санал болгохгүй /яагаад/"
    ]
    q20 = st.radio("Сонголтоо хийнэ үү:", q20_choices, key="q20", index=None)

    q20_other = ""
    if q20 == "Санал болгохгүй /яагаад/":
        q20_other = st.text_area("Яагаад санал болгохгүй гэж үзэж байна вэ?", key="q20_other")

    if q20 is not None and st.button("Дуусгах", key="btn_finish_q20"):
        # ✅ Store in correct answer keys
        st.session_state.answers["Loyalty2"] = q20
        if q20_other.strip():
            st.session_state.answers["Loyalty2_Other"] = q20_other.strip()

        # ✅ Submit to Snowflake
        if submit_answers():
            st.success("🎉 Судалгааг амжилттай бөглөлөө. Танд баярлалаа!")
            st.balloons()


if(st.session_state.page):
    print(st.session_state.page, " page")

















