import streamlit as st
from snowflake.snowpark import Session
from app_setup import apply_custom_font
import streamlit.components.v1 as components


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
# BASE_URL = "http://localhost:8501/"  
INTERVIEW_TABLE = f"{SCHEMA_NAME}_INTERVIEW_ANSWERS"


# ---- Answer storing ----
from datetime import datetime

# CSS animation
st.markdown("""
<style>
.stHorizontalBlock, .stElementContainer,.stMarkdown {
    animation: fadeIn 1s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0;}
    to   { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)




def submit_answers():
    emp_code = st.session_state.get("confirmed_empcode")
    first_name = st.session_state.get("confirmed_firstname")
    survey_type = st.session_state.get("survey_type", "")
    schema = SCHEMA_NAME
    table = f"{schema}_SURVEY_ANSWERS"
    submitted_at = datetime.utcnow()
    a = st.session_state.answers

    values = [
        emp_code,
        survey_type,
        submitted_at,
        a.get("Reason_for_Leaving", ""),
        a.get("Onboarding_Effectiveness", ""),
        a.get("Unexpected_Responsibilities", ""),
        a.get("Feedback", ""),
        a.get("Leadership_Style", ""),
        a.get("Team_Collaboration_Satisfaction", ""),
        a.get("Motivation_In_Daily_Work", ""),
        a.get("Work_Life_Balance", ""),
        a.get("Value_Of_Benefits", ""),
        a.get("Accuracy_Of_KPI_Evaluation", ""),
        a.get("Career_Growth_Opportunities", ""),
        a.get("Quality_Of_Training_Programs", ""),
        a.get("Loyalty", ""),
    ]

    try:
        session = get_session()

        escaped_values = ["'{}'".format(str(v).replace("'", "''")) if v is not None else "''" for v in values]

        insert_query = f"""
            INSERT INTO {table} (
                EMPCODE, 
                SURVEY_TYPE, 
                SUBMITTED_AT,
                Reason_for_Leaving,
                Onboarding_Effectiveness,
                Unexpected_Responsibilities,
                Feedback,
                Leadership_Style,
                Team_Collaboration_Satisfaction,
                Motivation_In_Daily_Work,
                Work_Life_Balance,
                Value_Of_Benefits,
                Accuracy_Of_KPI_Evaluation,
                Career_Growth_Opportunities,
                Quality_Of_Training_Programs,
                Loyalty
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
    "КОМПАНИЙН САНААЧИЛГААР": ["1 жил хүртэл", "1-ээс дээш"],
    "АЖИЛТНЫ САНААЧИЛГААР": [
        "6 сар дотор гарч байгаа", "7 сараас 3 жил ",
        "4-10 жил", "11 болон түүнээс дээш"
    ],
}

# ---- Total questions number dictionary by survey type & employment duration ----
total_questions_number_dict = {
    "КОМПАНИЙН САНААЧИЛГААР": {"1 жил хүртэл" : {"start_idx": 2,"skip_idx": 0, "total_questions": 11}, "1-ээс дээш": {"start_idx": 3,"skip_idx": 0, "total_questions": 10}},
    "АЖИЛТНЫ САНААЧИЛГААР": {"1 жил хүртэл" : {"start_idx": 1,"skip_idx": 0,"total_questions": 13}, "1-ээс дээш": {"start_idx": 1, "skip_idx": 2, "total_questions": 12}}
}


def choose_survey_type(category: str, total_months: int) -> str:
    # КОМПАНИЙН САНААЧИЛГААР
    if category == "КОМПАНИЙН САНААЧИЛГААР":
        if total_months <= 12:
            return "1 жил хүртэл"
        else:
            return "1-ээс дээш"
    if category == "АЖИЛТНЫ САНААЧИЛГААР":
        if total_months <= 12:
            return "1 жил хүртэл"
        else:
            return "1-ээс дээш"

    # Ажил хаяж явсан → always this type
    if category == "Ажил хаяж явсан":
        return "Мэдээлэл бүртгэх"

    # fallback
    return ""

def choose_survey_type_for_db(category: str, total_months: int) -> str:
    # Компанийн санаачилгаар
    if category == "КОМПАНИЙН САНААЧИЛГААР":
        if total_months <= 12:
            return "1 жил хүртэл"
        else:
            return "1-ээс дээш"

    # Ажилтны санаачлагаар
    if category == "АЖИЛТНЫ САНААЧИЛГААР":
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
def header():
    col1, col2 = st.columns(2)

    st.markdown("""
    <style>
            div[data-testid="stHorizontalBlock"] {
                align-items: center;
            }
    </style>
""", unsafe_allow_html=True)
    with col1:
        st.image(LOGO_URL, width=210)
    with col2:
        if("emp_code" in st.session_state and st.session_state.emp_code):
            st.markdown("""
                <style>
                .btn-like {
                    justify-self: end;
                    padding: 12px 20px;
                    border: 1px solid #d1d5db;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 1.2em;
                }
                </style>""", unsafe_allow_html=True)
            

            st.markdown(f"""
                <div class="btn-like">{st.session_state.emp_code}</div>
                """, unsafe_allow_html=True)

def progress_chart():
    print(st.session_state.survey_type, '       session state')
    st.markdown("""
            <style>
            div[data-testid="stProgress"] {
                position: relative;
                top: clamp(4rem, 5rem, 6rem);   
            }
            </style>""", unsafe_allow_html=True)
    
    total_questions_order = st.session_state.total_questions_order

    if(total_questions_order != {}):
        total_questions_number = total_questions_order.get("total_questions", 12)


    if st.session_state.page < 3:
        return  # Skip showing progress before Q1 starts

    current_page = st.session_state.page
    question_index = max(1, current_page - 3)  # Never below 1
    progress = min(100, max(0, int((question_index / total_questions_number) * 100)))  # Clamp between 0–100
    
    st.progress(progress)

def goToNextPage():
    curr_page = st.session_state.page
    total_questions_order= st.session_state.total_questions_order

    start_idx = total_questions_order.get("start_idx", 0)
    skip_idx = total_questions_order.get("skip_idx", 0)
    total_questions = total_questions_order.get("total_questions", 0)
    last_page_idx = start_idx + total_questions + 1
    if(skip_idx != 0 ): 
        last_page_idx+=1
    
    if(curr_page < last_page_idx):
        next_page = curr_page + 1
        if(next_page == skip_idx + 2):
            st.session_state.page = next_page + 1
        else:
            st.session_state.page = next_page 
    else: 
        st.session_state.page = "survey_end"
    st.rerun()

def goToNextPageForRadio():
    curr_page = st.session_state.page
    total_questions_order= st.session_state.total_questions_order

    start_idx = total_questions_order.get("start_idx", 0)
    skip_idx = total_questions_order.get("skip_idx", 0)
    total_questions = total_questions_order.get("total_questions", 0)
    last_page_idx = start_idx + total_questions + 1
    if(skip_idx != 0 ): 
        last_page_idx+=1
    
    if(curr_page < last_page_idx):
        next_page = curr_page + 1
        if(next_page == skip_idx + 2):
            st.session_state.page = next_page + 1
        else:
            st.session_state.page = next_page 
    else: 
        st.session_state.page = "survey_end"
    # st.rerun()

def nextPageBtn(disabled, answer_key, answer):
    col1,col2 = st.columns([5,1])
    st.markdown("""
        <style>
               div[data-testid="stButton"] button{
                    justify-self: end;
                    align-self: end;
                    padding:  clamp(0.1rem, 0.6rem, 1rem) clamp(0.25rem, 1rem, 1.5rem) ;
                    color: #fff;
                    background-color: #ec1c24 !important;  
                    border-radius: 20px; 
                }

               div[data-testid="stButton"] button p{
                    font-size: clamp(0.1rem, 0.8rem, 1rem);
                } 
        </style>

    """,unsafe_allow_html=True)
    with col2:
        if(st.button(label="Үргэлжлүүлэх →", disabled=disabled)):
            if(answer_key and answer):
                submitAnswer(answer_key, answer)    
                goToNextPage()



def begin_survey():
    total_questions_order = st.session_state.total_questions_order
    start_idx = total_questions_order.get("start_idx",1) 
    st.session_state.page = start_idx + 2 #survey Q1 starts from page 3 


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

    with st.spinner("Loading"):
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
                total_duration_in_str = categorize_employment_duration(total_months)
                
                
                # make exception
                if category == "АЖИЛ ХАЯЖ ЯВСАН":
                    st.session_state.survey_type = 'АЖИЛ ХАЯЖ ЯВСАН'
                    if submit_answers():
                        st.success("Амжилттай хадгаллаа")
                        # st.rerun()
                        return
                
                total_questions_order = total_questions_number_dict[category][total_duration_in_str]
                st.session_state.total_questions_order = total_questions_order

                if category:
                    
                    auto_type = choose_survey_type_for_db(category, total_months)
                    st.session_state.survey_type = auto_type
                    print(auto_type, ' setting survey type')
                    print(st.session_state.survey_type, ' setting survey type')

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

        if("create_link" not in st.session_state):
            st.session_state.create_link = False
        if("survey_link" not in st.session_state):
            st.session_state.survey_link = ""
            
        def onCreateLink():
            import uuid
            try:
                # session = get_session()
                token = uuid.uuid4().hex

                survey_type = st.session_state.get("survey_type", "")
                empcode_confirmed = st.session_state.get("confirmed_empcode", "")
                total_questions_order = st.session_state.get("total_questions_order", {})

                session.sql(f"""
                    INSERT INTO {DATABASE_NAME}.{SCHEMA_NAME}.{LINK_TABLE}
                        (TOKEN, EMPCODE, SURVEY_TYPE)
                    VALUES
                        ('{token}', '{empcode_confirmed}', '{survey_type}')
                """).collect()

                survey_link = f"{BASE_URL}?mode=link&token={token}&start_idx={total_questions_order['start_idx']}&skip_idx={total_questions_order['skip_idx']}&total_questions={total_questions_order['total_questions']}"
                st.session_state.survey_link = survey_link
                st.session_state.create_link = True

            except Exception as e:
                st.error(f"❌ Линк үүсгэх үед алдаа гарлаа: {e}")

        def onContinue():
            st.session_state.emp_code = empcode
            begin_survey()


        if auto_type:
            st.info(f"📌 Таньд тохирох судалгааны төрөл: **{auto_type}**")

        st.button("🔗 Линк үүсгэх (онлайнаар бөглөх)", key="create_survey_link_btn",on_click=lambda: onCreateLink())
        st.button("Үргэлжлүүлэх", key="begin_survey_btn", on_click=lambda: onContinue())

        if(st.session_state.create_link == True and st.session_state.survey_link != ""):
            st.success("Линк амжилттай үүслээ. Доорх линкийг ажилтанд илгээнэ үү:")
            st.code(st.session_state.survey_link, language="text")

        
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

    mode = params.get("mode", None)
    token = params.get("token", None)

    start_idx = int(params.get("start_idx", 0))
    skip_idx = int(params.get("skip_idx",0))
    total_questions = int(params.get("total_questions", 0))


    # if employee confirmed return
    if "emp_confirmed" in st.session_state and st.session_state.emp_confirmed:
        return
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
        st.session_state.emp_firstname = row["FIRSTNAME"]
        st.session_state.emp_code = empcode

        st.session_state.total_questions_order = {'start_idx': start_idx, 'total_questions':total_questions, 'skip_idx':skip_idx}

        if(st.session_state.total_questions_order):
        # Always go to intro page for link users
            begin_survey()
    except Exception as e:
        st.error(f"❌ Линкээр нэвтрэх үед алдаа гарлаа: {e}")


# 🔹 NEW: try to initialize from link token (if any)
init_from_link_token()

# ---- STATE INIT ----
if "category_selected" not in st.session_state:
    st.session_state.category_selected = None
if "survey_type" not in st.session_state:
    st.session_state.survey_type = None
if "total_questions_order" not in st.session_state:
    st.session_state.total_questions_order = {}
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


def go_to_intro():
    st.session_state.page = 2

# ---- LOGIN PAGE ----
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
        valid_users = st.secrets["users"]  # Securely loaded


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

        if st.button("Нэвтрэх", width="stretch"):
            if username in valid_users and password == valid_users[username]:
                st.session_state.logged_in = True
                st.session_state.page = -1
                st.rerun()
            else:
                st.error("❌ Нэвтрэх нэр эсвэл нууц үг буруу байна.")


def table_view_page():
    import pandas as pd
    logo()
    st.title("Бөглөсөн судалгааны жагсаалт")

    with st.spinner("Loading"):
        try:
            session = get_session()
            schema = SCHEMA_NAME
            db = DATABASE_NAME

            # Join survey answers with employee master and check interview status
            q = f"""
            WITH answers AS (
                SELECT
                    EMPCODE,
                    SUBMITTED_AT
                FROM {db}.{schema}.APU_SURVEY_ANSWERS
                WHERE SUBMITTED_AT IS NOT NULL
            ),
            interviews AS (
                SELECT DISTINCT
                    EMP_CODE
                FROM {db}.{schema}.{INTERVIEW_TABLE}
            )
            SELECT
                a.EMPCODE                         AS EMP_CODE,
                a.SUBMITTED_AT                    AS SUBMITTED_AT,
                '✅'                               AS SURVEY_DONE,         -- always yes, from survey table
                CASE 
                    WHEN i.EMP_CODE IS NOT NULL THEN '✅'
                    ELSE '❌'
                END                                AS INTERVIEW_DONE,
                e.LASTNAME,
                e.FIRSTNAME,
                e.COMPANYNAME,
                e.DEPNAME,
                e.POSNAME
            FROM answers a
            LEFT JOIN interviews i
                ON i.EMP_CODE = a.EMPCODE
            LEFT JOIN {db}.{schema}.APU_EMP_DATA_JULY2025 e
                ON e.EMPCODE = a.EMPCODE
            ORDER BY a.SUBMITTED_AT DESC
            """
            df = session.sql(q).to_pandas()

            # Rename columns to Mongolian labels
            df.rename(columns={
                "EMP_CODE": "Ажилтны код",
                "SUBMITTED_AT": "Бөглөсөн огноо",
                "SURVEY_DONE": "Судалгаа бөглөсөн",
                "INTERVIEW_DONE": "Ярилцлага өгсөн",
                "LASTNAME": "Овог",
                "FIRSTNAME": "Нэр",
                "COMPANYNAME": "Компани",
                "DEPNAME": "Хэлтэс",
                "POSNAME": "Албан тушаал",
            }, inplace=True)

            if not df.empty:
                # ⏱ Only show date part for submitted_at
                df["Бөглөсөн огноо"] = pd.to_datetime(df["Бөглөсөн огноо"]).dt.date

            # Show table
            st.dataframe(df, width="stretch")

        except Exception as e:
            st.error(f"❌ Snowflake холболтын алдаа: {e}")

        # Continue to directory
        if st.button("Үргэлжлүүлэх → Судалгааны сонголт"):
            st.session_state.page = -0.5
            st.rerun()


def interview_table_page():
    import pandas as pd
    st.title("🎤 Гарах ярилцлагад оролцох ажилтнаа сонгоно уу")

    with st.spinner("Loading"):
        try:
            session = get_session()
            schema = SCHEMA_NAME
            db = DATABASE_NAME
            interview_tbl = INTERVIEW_TABLE

            q = f"""
            WITH survey AS (
                SELECT
                    EMPCODE    AS EMP_CODE,
                    SUBMITTED_AT
                FROM {db}.{schema}.APU_SURVEY_ANSWERS
                WHERE SUBMITTED_AT IS NOT NULL
            ),
            interviewed AS (
                SELECT DISTINCT EMP_CODE
                FROM {db}.{schema}.{interview_tbl}
            )
            SELECT
                s.EMP_CODE,
                s.SUBMITTED_AT,
                e.LASTNAME,
                e.FIRSTNAME,
                e.COMPANYNAME,
                e.DEPNAME,
                e.POSNAME
            FROM survey s
            LEFT JOIN interviewed i
                ON i.EMP_CODE = s.EMP_CODE
            LEFT JOIN {db}.{schema}.APU_EMP_DATA_JULY2025 e
                ON e.EMPCODE = s.EMP_CODE
            WHERE i.EMP_CODE IS NULL
            ORDER BY s.SUBMITTED_AT DESC
            """

            df = session.sql(q).to_pandas()

            # SUBMITTED_AT → date only
            if "SUBMITTED_AT" in df.columns:
                df["SUBMITTED_AT"] = pd.to_datetime(df["SUBMITTED_AT"]).dt.date

            df.rename(columns={
                "EMP_CODE": "Ажилтны код",
                "SUBMITTED_AT": "Бөглөсөн огноо",
                "LASTNAME": "Овог",
                "FIRSTNAME": "Нэр",
                "COMPANYNAME": "Компани",
                "DEPNAME": "Хэлтэс",
                "POSNAME": "Албан тушаал",
            }, inplace=True)

            if df.empty:
                st.info("Ярилцлагад оруулаагүй судалгаатай ажилтан алга байна.")
                if st.button("Буцах цэс рүү"):
                    st.session_state.page = -0.5
                    st.rerun()
                return

            # base columns
            base_cols = [
                "Ажилтны код", "Овог", "Нэр",
                "Компани", "Хэлтэс", "Албан тушаал", "Бөглөсөн огноо"
            ]
            df_display = df[base_cols].copy()

            # add selection column
            df_display["Сонгох"] = False

            # 👉 reorder so Сонгох + Бөглөсөн огноо are in front
            ordered_cols = [
                "Сонгох",
                "Бөглөсөн огноо",
                "Ажилтны код",
                "Овог",
                "Нэр",
                "Компани",
                "Хэлтэс",
                "Албан тушаал",
            ]
            df_display = df_display[ordered_cols]

            edited = st.data_editor(
                df_display,
                key="interview_table_editor",
                width="stretch",
                num_rows="fixed"
            )

        except Exception as e:
            st.error(f"❌ Snowflake холболтын алдаа: {e}")
            return

        if st.button("Үргэлжлүүлэх → Ярилцлагын танилцуулга"):
            selected = edited[edited["Сонгох"] == True]

            if selected.empty:
                st.warning("Та ярилцлага хийх нэг ажилтныг сонгоно уу.")
                return
            if len(selected) > 1:
                st.warning("Нэг ажилтан сонгоно уу.")
                return

            row = selected.iloc[0]
            st.session_state.selected_emp_code = row["Ажилтны код"]
            st.session_state.selected_emp_lastname = row["Овог"]
            st.session_state.selected_emp_firstname = row["Нэр"]

            st.session_state.page = "interview_0"
            st.rerun()
# ---- DIRECTORY PAGE ----
def directory_page():

    st.image(LOGO_URL, width=200)

    col1,col2 =  st.columns(2)
    with col1:

        st.markdown("""
            <h1 style="text-align: left; margin-left: 0; font-size: 3em; height:60vh; display:table; ">
                    <p style="display:table-cell; vertical-align: middle;">Ажилтны ерөнхий <span style="color: #ec1c24;"> мэдээлэл </span> </p>
            </h1>
        """, unsafe_allow_html=True)

    
    
    with col2:
        st.markdown("""
            <style>
                div[data-testid="stElementContainer"] {
                    width: auto;    
                }
                /* Style radio group container */
                div[data-testid="stRadio"] > div {
                    display: flex;
                    flex-direction: row !important;
                    flex-wrap: nowrap;
                }
                
                div[data-testid="stRadio"] > div > label {
                    flex: 1;
                }
                
                div[data-testid="stRadio"] > div > label p{
                    word-break: normal;
                }

                /* Style each radio option like a button */
                div[data-testid="stRadio"] label {
                    background-color: #fff;       /* default background */
                    padding: 20px 20px;
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
        option1 = st.radio("СУДАЛГААНЫ АНГИЛАЛ", ["ГАРАХ СУДАЛГАА", "ГАРАХ ЯРИЛЦЛАГА"], index=None, key="survey_or_interview")
        if(option1 == "ГАРАХ СУДАЛГАА"):
            option2 = st.radio("АЖЛААС ГАРСАН ТӨРӨЛ", ["КОМПАНИЙН САНААЧИЛГААР", "АЖИЛТНЫ САНААЧИЛГААР", "АЖИЛ ХАЯЖ ЯВСАН"], index=None, key='category_selected')
            if(option2):
                col1, col2 = st.columns([3, 1])                
                with col1:
                    emp_code = st.text_input("Ажилтны код", key="empcode")
                with col2:
                    if st.button("Баталгаажуулах", key="btn_confirm"):
                        st.session_state.employee_confirm_btn_clicked=True
                    
                if(st.session_state.employee_confirm_btn_clicked == True):
                    confirmEmployeeActions(emp_code)


        elif option1 == "ГАРАХ ЯРИЛЦЛАГА": 
            interview_table_page()
# --- 🔵 EXIT INTERVIEW FUNCTIONS (ADD BEFORE ROUTING) ---
def show_survey_answers_page(empcode: str):
    """Clean, readable survey answer viewer for HR (opens in new tab)."""
    import pandas as pd

    header()
    st.title("📄 Судалгааны хариу (унших горим)")

    if not empcode:
        st.error("Ажилтны код дутуу байна.")
        return

    try:
        session = get_session()
        db = DATABASE_NAME
        schema = SCHEMA_NAME

        q = f"""
        SELECT *
        FROM {db}.{schema}.APU_SURVEY_ANSWERS
        WHERE EMPCODE = '{empcode}'
        ORDER BY SUBMITTED_AT DESC
        LIMIT 1
        """
        df = session.sql(q).to_pandas()

        if df.empty:
            st.warning(f"Энэ ажилтны ({empcode}) судалгааны хариу олдсонгүй.")
            return

        row = df.iloc[0]

        # ---- Top info section ----
        st.markdown("### 👤 Ажилтны мэдээлэл")
        st.write(f"**Ажилтны код:** {row.get('EMPCODE', '')}")
        
        if "SURVEY_TYPE" in row:
            st.write(f"**Судалгааны төрөл:** {row.get('SURVEY_TYPE', '')}")

        if "SUBMITTED_AT" in row:
            try:
                submitted = pd.to_datetime(row["SUBMITTED_AT"])
                st.write(f"**Илгээсэн огноо:** {submitted.date()}")
            except:
                st.write(f"**Илгээсэн огноо:** {row.get('SUBMITTED_AT', '')}")

        st.markdown("---")
        st.markdown("### 📝 Судалгааны дэлгэрэнгүй хариу")

        # Columns you do NOT want to show
        hide_cols = {
            "EMPCODE", "SURVEY_TYPE", "SUBMITTED_AT", 
            "FIRSTNAME", "LASTNAME"  # if included
        }

        # Show everything else
        show_cols = [c for c in row.index if c not in hide_cols]

        for col in show_cols:
            val = row[col]

            # Convert NULL/None to —
            if val in [None, "", "null", "NULL"]:
                val = "—"

            # Render as section per question
            st.markdown(f"**{col.replace('_', ' ')}**")
            st.write(val)
            st.markdown("---")

    except Exception as e:
        st.error(f"❌ Судалгааны хариу унших үед алдаа гарлаа: {e}")
# ---Thankyou
def final_thank_you():
    header()

    st.markdown(
        """
        <style>
            div[data-testid="stVerticalBlock"]:has(h1)   {
                        justify-content:center;
                        align-items: center;
            }

        </style>
        """
          , unsafe_allow_html=True  
    )


    st.balloons()
    st.title("Судалгааг амжилттай бөглөлөө. Танд баярлалаа!🎉")
    st.write("Ажилтны мэдээлэл амжилттай бүртгэгдлээ.")


    params = st.query_params

    mode = params.get("mode", None)
    token = params.get("token", None)

    # Not a magic link → do nothing
    if mode != "link" or not token:
        if st.button("📁 Цэс рүү буцах", key="btn_back_to_directory", width=200):
            st.session_state.page = -1
            st.rerun()

        if st.button("🚪 Гарах", key="btn_logout", width=200):
                st.session_state.clear()
                st.rerun()

def submit_interview_answers():
    """Insert interview answers into Snowflake using INT_Q1..INT_Q7 keys."""
    try:
        session = get_session()
        db = DATABASE_NAME
        schema = SCHEMA_NAME
        table = INTERVIEW_TABLE

        emp_code = st.session_state.get("selected_emp_code")
        if not emp_code:
            st.error("Ажилтны код олдсонгүй. Хүснэгтээс ажилтан сонгосон эсэхээ шалгана уу.")
            return False

        submitted_at = datetime.utcnow()

        # Read directly from Streamlit state
        q1 = st.session_state.get("INT_Q1")
        q2 = st.session_state.get("INT_Q2")
        q3 = st.session_state.get("INT_Q3")
        q4 = st.session_state.get("INT_Q4")
        q5 = st.session_state.get("INT_Q5")
        q6 = st.session_state.get("INT_Q6")
        q7 = st.session_state.get("INT_Q7")

        # Required validation
        if q7 is None or str(q7).strip() == "":
            st.warning("7-р асуултад /ажлаас гарах шийдвэрт нөлөөлсөн 3 хүчин зүйл/ заавал хариулна уу.")
            return False

        # Prepare values list
        values = [emp_code, submitted_at, q1, q2, q3, q4, q5, q6, q7]

        # Escape quotes
        escaped_values = []
        for v in values:
            if v not in [None, ""]:
                escaped = str(v).replace("'", "''")
                escaped_values.append(f"'{escaped}'")
            else:
                escaped_values.append("NULL")

        insert_sql = f"""
            INSERT INTO {db}.{schema}.{table} (
                EMP_CODE,
                SUBMITTED_AT,
                MEANINGFUL_WORK,
                RECOGNITION_APPRECIATION,
                CAREER_DEVELOPMENT,
                SUPPORTIVE_LEADERSHIP,
                WORK_LIFE_BALANCE,
                EMPLOYEE_WELLBEING,
                LEAVING_DECISION_TOP3
            )
            VALUES ({','.join(escaped_values)})
        """

        session.sql(insert_sql).collect()

        st.session_state.interview_submitted = True
        st.session_state.interview_submitted_at = submitted_at
        return True

    except Exception as e:
        st.error(f"❌ Ярилцлагын хариу хадгалах үед алдаа гарлаа: {e}")
        return False

def interview_intro():
    st.title("🎤 Гарах ярилцлага – Танилцуулга")

    emp_code = st.session_state.get("selected_emp_code", "")
    lname = st.session_state.get("selected_emp_lastname", "")
    fname = st.session_state.get("selected_emp_firstname", "")

    if emp_code:
        st.markdown(f"**Сонгосон ажилтан:** {emp_code} – {lname} {fname}")

    st.write(
        "Доорх ярилцлагын асуултууд нь ажилтны гарах шийдвэрийн шалтгаан, "
        "тулгамдсан асуудал, сайжруулах боломжийг тодруулах зорилготой."
    )

    col1, col2 = st.columns(2)

    # --- LEFT COLUMN: view survey answers button ---
    with col1:
        if emp_code:
            view_url = f"{BASE_URL}?mode=view_survey&empcode={emp_code}"

            st.markdown(
                f'''
                <a href="{view_url}" target="_blank">
                    <button style="
                        background-color:#f0f2f6;
                        padding:10px 18px;
                        border-radius:8px;
                        border:1px solid #ccc;
                        font-size:16px;
                        cursor:pointer;">
                        📄 Судалгааны хариуг харах
                    </button>
                </a>
                ''',
                unsafe_allow_html=True
            )

    # --- RIGHT COLUMN: start interview ---
    with col2:
        if st.button("🗣 Ярилцлага эхлэх", key="btn_start_interview"):
            st.session_state.page = "interview_form"
            st.rerun()



def interview_form():
    """All 7 interview questions on one page."""
    header()
    st.title("🎤 Гарах ярилцлага – Асуултууд")
    st.write("Доорх 7 асуултад хариулж ярилцлагыг бүрэн бөглөнө үү.")

    star_options = ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"]

    # Q1
    st.subheader("1. Ажиллаж байх хугацаанд байгууллага таны мэдлэг, ур чадварыг бүрэн гаргаж чадсан уу?")
    st.radio("Таны хариулт", star_options, index=None, key="INT_Q1")

    # Q2
    st.subheader("2. Таны ажлын гүйцэтгэлд нийцсэн урамшуулал, албан тушаал дэвших боломжийг компани нээлттэй олгодог байсан уу?")
    st.radio("Таны хариулт", star_options, index=None, key="INT_Q2")

    # Q3
    st.subheader("3. Байгууллагад албан тушаал дэвших үйл явц ойлгомжтой, ил тод, нээлттэй байсан уу?")
    st.radio("Таны хариулт", star_options, index=None, key="INT_Q3")

    # Q4
    st.subheader("4. Таны шууд удирдлагын манлайллын хэв маяг гүйцэтгэл, урам зориг, тогтвор суурьшилтай ажиллахад тань нөлөөлсөн үү?")
    st.radio(
        "Таны хариулт",
        [
            "Нөлөөлсөн /эерэг талаар/",
            "Нөлөөлсөн /сөрөг талаар/",
            "Нөлөөлөөгүй"
        ],
        index=None,
        key="INT_Q4"
    )

    # Q5
    st.subheader("5. Байгууллагын ажил, амьдралын тэнцвэртэй байдлыг дэмжсэн бодлого, журам нь бодитой хэрэгждэг байсан уу?")
    st.radio("Таны хариулт", star_options, index=None, key="INT_Q5")

    # Q6
    st.subheader("6. Таны ажлын байрны орчин сэтгэлзүйн хувьд аюулгүй мэдрэмж төрүүлдэг байсан уу?")
    st.radio("Таны хариулт", star_options, index=None, key="INT_Q6")

    # Q7
    st.subheader("7. Таны ажлаас гарах шийдвэрт нөлөөлсөн 3 хүчин зүйлийг нэрлэнэ үү.")
    st.text_area("Таны хариулт", key="INT_Q7")

    # Submit button
    if st.button("✅ Ярилцлага дуусгах", key="btn_finish_interview"):
        ok = submit_interview_answers()
        if ok:
            st.session_state.page = "interview_end"
            st.rerun()



# END PAGE --------------------------------------------------------------
def interview_end():
    emp_code = st.session_state.get("selected_emp_code", "")
    lname = st.session_state.get("selected_emp_lastname", "")
    fname = st.session_state.get("selected_emp_firstname", "")
    submitted_at = st.session_state.get("interview_submitted_at", None)

    st.success("🎉 Ярилцлага амжилттай дууслаа, баярлалаа!")
    st.write(f"👤 Ажилтан: {emp_code} - {lname} {fname}")
    if submitted_at:
        st.write(f"🕒 Илгээсэн огноо (UTC): {submitted_at}")

    if st.button("Буцах цэс рүү"):
        st.session_state.page = -1  # directory
        st.rerun()


# ---- INIT AUTH STATE ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "employee_confirm_btn_clicked" not in st.session_state:
    st.session_state.employee_confirm_btn_clicked = False
if "page" not in st.session_state:
    st.session_state.page = -1

# ---- LOGIN/DIRECTORY ROUTING ----
if not st.session_state.logged_in:
    login_page()
    st.stop()
elif st.session_state.page == -0.5:
    directory_page()
    st.stop()
elif st.session_state.page == -1:
    table_view_page()
    st.stop()


# ---- PAGE 0: CATEGORY + SURVEY TYPE (Single Page) ----
if st.session_state.page == 0:
    header()
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


# ---- SURVEY QUESTION 1 ----
elif st.session_state.page == 3:
    # ✅ Check confirmed values
    # if not st.session_state.get("confirmed_empcode") or not st.session_state.get("confirmed_firstname"):
    #     st.error("❌ Ажилтны мэдээлэл баталгаажаагүй байна. Эхний алхмыг дахин шалгана уу.")
    #     st.stop()
    
    header()
    col1,col2 =  st.columns(2)
    with st.spinner("loading"):
        st.markdown("""
            <style>
                    div[data-testid="stHorizontalBlock"] {
                        align-items: center;
                    }
            </style>
        """, unsafe_allow_html=True)


        with col1:

            st.markdown("""
                <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3;  padding: 1rem;">
                        <p> Танд ажлаас гарахад нөлөөлсөн<span style="color: #ec1c24;"> хүчин зүйл, шалтгаантай</span> хамгийн их тохирч байгаа 1-3 хариултыг сонгоно уу?</p>
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
                    padding: clamp(0.1rem, 0.5rem, 1.5rem) clamp(0.2rem, 0.6rem, 1.5rem);
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
                    font-size: clamp(0.25rem, 0.8vw, 1rem);
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
                        "Цалин хөлс хангалтгүй", 
                        "Хамт олны уур амьсгал, харилцаа таарамжгүй", 
                        "Гүйцэтгэлийн үнэлгээ шудрага бус", 
                        "Ажлын ачаалал их","Ажлын цагийн хуваарь таарамжгүй, хэцүү байсан",
                        "Дасан зохицуулах хөтөлбөрийн хэрэгжилт муу",
                        "Өөр хот, аймаг, улсад шилжих, амьдрах",
                        "Тэтгэвэрт гарч байгаа",
                        "Үндсэн мэргэжлийн дагуу ажиллах болсон",
                        "Албан тушаал/мэргэжлийн хувьд өсөх, суралцах боломж байхгүй",
                        "Эрүүл мэндийн байдлаас",
                        "Хөдөлмөрийн нөхцөл хэвийн бус/хүнд хортой байсан",
                        "Хувийн шалтгаан/Personal Reasons",
                        "Илүү боломжийн өөр ажлын байрны санал авсан",
                        "Ажлын орчин нөхцөл муу",
                        "Ар гэрийн асуудал үүссэн",
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
        escaped_answer = "; ".join(st.session_state.selected)

        if(len(st.session_state.selected)):
            nextPageBtn(max_choices_reached, answer_key, escaped_answer)
                
        if(len(st.session_state.selected) > 3):
            st.warning("Хамгийн ихдээ 3 төрлийг сонгоно уу")
        
        progress_chart()


elif st.session_state.page == 4:

    header()
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
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3; padding: 1rem;">
                    <p> Дасан зохицох хөтөлбөрийн хэрэгжилт эсвэл баг хамт олон, шууд удирдлага танд өдөр тутмын ажил, үүрэг даалгавруудыг хурдан ойлгоход туслах <span style="color: #ec1c24;"> хангалттай мэдээлэл, заавар</span> өгч чадсан уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:

        import base64
        from pathlib import Path

        def load_base64(path):
            img_bytes = Path(path).read_bytes()
            return base64.b64encode(img_bytes).decode()
        
        emoji1 = load_base64("static/images/Image (15).png")
        emoji2 = load_base64("static/images/Image (16).png")


        c1, c2 = st.columns(2)
        
        st.markdown("""
        <style>
            div[data-testid="stButton"] button {
                display: none !important;
            }
                    
        /* Mobile layout */
        @media (max-width: 900px) {
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

        with c1:
             # --- Hidden Streamlit trigger ---
            # --- Custom HTML Button with Image + Text ---
            components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border: 1px solid #ccc;
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 1rem;
                    width: 100%;
                    max-width: 420px;
                    height: 400px;
                ">
                    <img src="data:image/png;base64,{emoji1}" width="clamp(60px, 15vw, 130px)" height="200">
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem)">Хангалттай чадсан</span>
                </button>

                <script>
                    document.getElementById("imgBtn").onclick = () => {{
                        const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
                        if (btn) btn.click();
                    }};
                </script>

            """, height=450)

        
        with c2:
            # --- Custom HTML Button with Image + Text ---
            components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    border: 1px solid #ccc;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    max-width: 420px;
                    height: 400px;   

                ">
                    <img src="data:image/png;base64,{emoji2}" width="auto" height="200">
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem);">Огт чадаагүй</span>
                </button>   

                <script>    
                    document.getElementById("imgBtn").onclick = () => {{
                        const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                        if (btn) btn[1].click();
                    }};
                </script>

            """, height=450)    
            
        
        answer_key = "Onboarding_Effectiveness"

        button1 = st.button("trigger1", key="trigger1", on_click=lambda: submitAnswer(answer_key,"Хангалттай чадсан"))
        button2 = st.button("trigger2", key="trigger2", on_click=lambda: submitAnswer(answer_key, "Огт чадаагүй"))
        
        if(button1 or button2):
            goToNextPage()

    progress_chart()

elif st.session_state.page == 5:
    header()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
                    <style>
                        div[data-testid="stButton"] button {
                            display: none !important;
                        }
                                
                    /* Mobile layout */
                    @media (max-width: 900px) {
                        div[data-testid="stHorizontalBlock"] {
                            flex-direction: column !important;
                        }
                    }
                    </style>
                """, unsafe_allow_html=True)

    with col1:

        st.markdown("""
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3;">
                    <p> Ажлын байрны тодорхойлолт таны <span style="color: #ec1c24;"> өдөр тутмын </span> ажил үүрэгтэй нийцэж байсан уу??</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        import base64
        from pathlib import Path

        def load_base64(path):
            img_bytes = Path(path).read_bytes()
            return base64.b64encode(img_bytes).decode()
        
        emoji1 = load_base64("static/images/Image (28).png")
        emoji2 = load_base64("static/images/Image (11).png")


        c1, c2 = st.columns(2)
        
        

        with c1:
             # --- Hidden Streamlit trigger ---
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                    <button id="imgBtn" style=" 
                        background: #fff;
                        padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                        border: 1px solid #ccc;
                        border-radius: 15px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        gap: 1rem;
                        width: 100%;
                        max-width: 420px;
                        height: 25rem;   
                    ">
                        <img src="data:image/png;base64,{emoji1}" width="clamp(60px, 15vw, 130px)" height="200">
                        <span style="font-size: clamp(1.2rem, 2vw, 2rem)">Тийм</span>
                    </button>

                    <script>
                        document.getElementById("imgBtn").onclick = () => {{
                            const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
                            if (btn) btn.click();
                        }};
                    </script>

                """, height=450)

        
        with c2:
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                    <button id="imgBtn" style=" 
                        background: #fff;
                        border: 1px solid #ccc;
                        padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                        border-radius: 15px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        width: 100%;
                        max-width: 420px;
                        height: 25rem;   

                    ">
                        <img src="data:image/png;base64,{emoji2}" width="auto" height="200">
                        <span style="font-size: clamp(1.2rem, 2vw, 2rem);">Үгүй</span>
                    </button>   

                    <script>    
                        document.getElementById("imgBtn").onclick = () => {{
                            const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                            if (btn) btn[1].click();
                        }};
                    </script>

                """, height=450)    
            
        
        answer_key = "Unexpected_Responsibilities"

        button1 = st.button("trigger1", key="trigger1", on_click=lambda: submitAnswer(answer_key,"Тийм"))
        button2 = st.button("trigger2", key="trigger2", on_click=lambda: submitAnswer(answer_key, "Үгүй"))
        
        if(button1 or button2):
            goToNextPage()

    progress_chart()

elif st.session_state.page == 6:
    header()
    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
        </style>
    """, unsafe_allow_html=True)


    with col1:

        st.markdown("""
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3;">
                    <p> Таны шууд удирдлага санал зөвлөгөө өгч, <span style="color: #ec1c24;"> эргэх холбоотой </span>ажилладаг байсан уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        with st.spinner("loading"):
            import base64
            from pathlib import Path

            def load_base64(path):
                img_bytes = Path(path).read_bytes()
                return base64.b64encode(img_bytes).decode()
            
            emoji1 = load_base64("static/images/Image (25).png")
            emoji2 = load_base64("static/images/Image (16).png")


            c1, c2 = st.columns(2)
            
            st.markdown("""
                        <style>
                            div[data-testid="stButton"] button {
                                display: none !important;
                            }
                                    
                        /* Mobile layout */
                        @media (max-width: 900px) {
                            div[data-testid="stHorizontalBlock"] {
                                flex-direction: column !important;
                            }
                        }
                        </style>
                    """, unsafe_allow_html=True)

            with c1:
                # --- Hidden Streamlit trigger ---
                # --- Custom HTML Button with Image + Text ---
                with st.spinner("loading"):
                    components.html(f"""
                        <button id="imgBtn" style=" 
                            background: #fff;
                            padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                            border: 1px solid #ccc;
                            border-radius: 15px;
                            cursor: pointer;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            gap: 1rem;
                            width: 100%;
                            max-width: 420px;
                            height: 25rem;   
                        ">
                            <img src="data:image/png;base64,{emoji1}" width="clamp(60px, 15vw, 130px)" height="200">
                            <span style="font-size: clamp(1.2rem, 2vw, 2rem)">Тийм</span>
                        </button>

                        <script>
                            document.getElementById("imgBtn").onclick = () => {{
                                const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
                                if (btn) btn.click();
                            }};
                        </script>

                    """, height=450)

                
            with c2:
                # --- Custom HTML Button with Image + Text ---
                with st.spinner("loading"):
                    components.html(f"""
                    <button id="imgBtn" style=" 
                        background: #fff;
                        border: 1px solid #ccc;
                        padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                        border-radius: 15px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        width: 100%;
                        max-width: 420px;
                        height: 25rem;   

                    ">
                        <img src="data:image/png;base64,{emoji2}" width="auto" height="200">
                        <span style="font-size: clamp(1.2rem, 2vw, 2rem);">Үгүй</span>
                    </button>   

                    <script>    
                        document.getElementById("imgBtn").onclick = () => {{
                            const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                            if (btn) btn[1].click();
                        }};
                    </script>

                """, height=450)    
                
            
            answer_key = "Feedback"

            button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Тийм"))
            button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Үгүй"))
            
            if(button1 or button2):
                goToNextPage()
                
    progress_chart()

elif st.session_state.page == 7:
    header()
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
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3;">
                    <p>Таны шууд удирдлага ихэвчлэн аль зан төлвийг гаргадаг вэ?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        import base64
        from pathlib import Path

        def load_base64(path):
            img_bytes = Path(path).read_bytes()
            return base64.b64encode(img_bytes).decode()
        
        emoji1 = load_base64("static/images/Image (19).png")
        emoji2 = load_base64("static/images/Image (22).png")


        c1, c2 = st.columns(2)
        
        st.markdown("""
        <style>
            div[data-testid="stButton"] button {
                display: none !important;
            }
                    
            button#imgBtn span:hover{
                border-color: #ec1c24;
            }
                    
        /* Mobile layout */
        @media (max-width: 900px) {
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)


        with c1:
             # --- Hidden Streamlit trigger ---
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border: 1px solid #ccc;
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 1rem;
                    width: 100%;
                    max-width: 420px;
                    height: 25rem;   
                ">
                    <img src="data:image/png;base64,{emoji1}" width="clamp(60px, 15vw, 130px)" height="200">
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem)">Би Би гэдэг</span>
                </button>

                <script>
                    document.getElementById("imgBtn").onclick = () => {{
                        const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
                        if (btn) btn.click();
                    }};
                </script>

            """, height=450)

        
        with c2:
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    border: 1px solid #ccc;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    max-width: 420px;
                    height: 25rem;   

                ">
                    <img src="data:image/png;base64,{emoji2}" width="auto" height="200">
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem);">Бид Бид гэдэг</span>
                </button>   

                <script>    
                    document.getElementById("imgBtn").onclick = () => {{
                        const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                        if (btn) btn[1].click();
                    }};
                </script>

            """, height=450)    
            
        
        answer_key = "Leadership_Style"

        button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Би Би гэдэг"))
        button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Бид Бид гэдэг"))
        
        if(button1 or button2):
            goToNextPage()
    progress_chart()


elif st.session_state.page == 8:
    header()
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
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3;">
                    <p> Таны харъяалагдаж буй баг доторх <span style="color: #ec1c24;">хамтын ажиллагаа,</span> хоорондын харилцаанд хэр сэтгэл хангалуун байсан бэ?</p>
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
                    font-size: clamp(0.5rem, 1.5rem, 2rem);
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
           "⭐\nОгт сэтгэл ханамжгүй", "⭐⭐\nСэтгэл ханамжгүй", "⭐⭐⭐\nДундаж", "⭐⭐⭐⭐\nСэтгэл хангалуун", "⭐⭐⭐⭐⭐\nМаш сэтгэл хангалуун"
        ]

        answer_key = "Team_Collaboration_Satisfaction"

        def onRadioChange():
            submitAnswer(answer_key,st.session_state.get(answer_key))
            goToNextPageForRadio()
        
        # --- Create radio group ---
        choice = st.radio(
            "",
            options,
            horizontal=True,
            key="Team_Collaboration_Satisfaction",
            index=None,  
            on_change=onRadioChange
        )
    progress_chart()

elif st.session_state.page == 9:
    header()
    col1,col2 =  st.columns(2)


    with col1:

        st.markdown("""
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3; display:table; height: 50vh;">
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
                font-size: clamp(0.5rem, 1vw, 1rem);
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
                    "баг хамт олны дэмжлэг",
                    "сурч хөгжих боломжоор хангагддаг байсан нь",
                    "олон нийтийн үйл ажиллагаа",
                    "шударга нээлттэй харилцаа",
                    "шагнал урамшуулал",
                    "ажлын орчин",
                    "төсөл",
                    "хөтөлбөрүүд",
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

    answer_key = "Motivation_In_Daily_Work"
    max_choices_reached = len(st.session_state.selected) > 3
    escaped_answer = "; ".join(st.session_state.selected)

    if(len(st.session_state.selected)):
        nextPageBtn(max_choices_reached, answer_key, escaped_answer)
    if(len(st.session_state.selected) > 3):
        st.warning("Хамгийн ихдээ 3 төрлийг сонгоно уу")
    progress_chart()

elif st.session_state.page == 10:
    header()
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
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3;">
                    <p> Байгууллага танд ажиллах <span style="color: #ec1c24;"> таатай нөхцөл</span>, ажил амьдралын тэнцвэртэй байдлаар ханган дэмждэг байсан уу? /Жнь: уян хатан цагийн хуваарь, ажлын байрны орчин/</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        import base64
        from pathlib import Path

        def load_base64(path):
            img_bytes = Path(path).read_bytes()
            return base64.b64encode(img_bytes).decode()
        
        emoji1 = load_base64("static/images/Image (28).png")
        emoji2 = load_base64("static/images/Image (2).png")


        c1, c2 = st.columns(2)
        

        st.markdown("""
        <style>
            div[data-testid="stButton"] button {
                display: none !important;
            }
                    
        /* Mobile layout */
        @media (max-width: 900px) {
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

        with c1:
             # --- Hidden Streamlit trigger ---
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border: 1px solid #ccc;
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 1rem;
                    width: 100%;
                    max-width: 420px;
                    height: 25rem;  
                ">
                    <img src="data:image/png;base64,{emoji1}" width="clamp(60px, 15vw, 130px)" height="200">
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem)">Тийм</span>
                </button>

                <script>
                    document.getElementById("imgBtn").onclick = () => {{
                        const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
                        if (btn) btn.click();
                    }};
                </script>

            """, height=450)

        with c2:
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    border: 1px solid #ccc;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    max-width: 420px;
                    height: 25rem;   

                ">
                    <img src="data:image/png;base64,{emoji2}" width="auto" height="200">
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem);">Үгүй</span>
                </button>   

                <script>    
                    document.getElementById("imgBtn").onclick = () => {{
                        const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                        if (btn) btn[1].click();
                    }};
                </script>

            """, height=450)    
            
        
        answer_key = "Work_Life_Balance"

        button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Тийм"))
        button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Үгүй"))
        
        if( button1 or button2):
            goToNextPage()

    progress_chart()

elif st.session_state.page == 11:
    header()
    col1,col2 =  st.columns(2)

    st.markdown("""
        <style>
                div[data-testid="stHorizontalBlock"] {
                    align-items: center;
                }
        </style>
    """, unsafe_allow_html=True)
    
    # st.session_state.page = 10
    # st.rerun()

    with col1:

        st.markdown("""
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3; display: table; height: 55vh;">
                    <p style="display:table-cell; vertical-align: middle;"> Танд компаниас олгосон тэтгэмж, хөнгөлөлтүүд (эрүүл мэндийн даатгал, цалинтай чөлөө, тэтгэмж гэх мэт) нь үнэ цэнтэй, ач холбогдолтой байсан уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        # st.markdown("""
        #     <style>
                    
        #         /* Hide default radio buttons */
        #         div[data-testid="stRadio"] > div > label > div:first-child {
        #             display: none !important;
        #         }
                    
        #       /* area that contains the text (Streamlit wraps text inside a div) */
        #         div[data-testid="stRadio"] label > div {
        #             /* respect newline characters in the option strings */
        #             white-space: pre-line;
        #         }

        #         /* Style radio group container */
        #         div[data-testid="stRadio"] > div {
        #             gap: 10px;
        #             justify-content: center;
        #             align-items: center;
        #         }
        #             /* "H1"-like first line */
        #         div[data-testid="stRadio"] label > div::first-line {
        #             font-size: 2em;
        #             font-weight: 700;
        #             color: #111827;
        #         }

        #         /* Style each radio option like a button */
        #         div[data-testid="stRadio"] label {
        #             background-color: #fff;       /* default background */
        #             width: 60%;
        #             padding: 8px 16px;
        #             border-radius: 8px;
        #             cursor: pointer;
        #             border: 1px solid #ccc;
        #             transition: background-color 0.2s;
        #             text-align: center;
        #             justify-content: center;
        #         }
                        
        #         label[data-testid="stWidgetLabel"]{
        #             border: 0px !important;
        #             font-size: 2px !important;
        #             color: #898989;
                    
        #         }

        #         /* Hover effect */
        #         div[data-testid="stRadio"] label:hover {
        #             border-color: #ec1c24;
        #         }

        #         /* Checked/selected option */
        #         div[data-testid="stRadio"] input:checked + label {
        #             background-color: #FF0000 !important; /* selected color */
        #             color: white !important;
        #             border-color: #ec1c24 !important;
        #         }

        #         /* Hide default radio circle */
        #         div[data-testid="stRadio"] input[type="radio"] {
        #             display: none;
        #         }
                        
        #     </style>
        #     """, unsafe_allow_html=True)
        

        # #emoji1 😃
        # #emoji2 😉
        # #emoji3 😐
        # #emoji4 🙁

        # options = [
        #    "😃\nТийм, үнэ цэнтэй ач холбогдолтой", "😐\nСайн, гэхдээ сайжруулах шаардлагатай", "🙁\nАч холбогдолгүй, үр ашиггүй"
        # ]

        # answer_key = "Value_Of_Benefits"

        # def onRadioChange():
        #     submitAnswer(answer_key,st.session_state.get(answer_key))
        #     goToNextPageForRadio()
        
        
        # # --- Create radio group ---
        # choice = st.radio(
        #     "",
        #     options,
        #     horizontal=True,
        #     index=None,
        #     key="Value_Of_Benefits",
        #     on_change=onRadioChange
        # )

        import base64
        from pathlib import Path

        def load_base64(path):
            img_bytes = Path(path).read_bytes()
            return base64.b64encode(img_bytes).decode()
        
        emoji1 = load_base64("static/images/Image (34).png")
        emoji2 = load_base64("static/images/Image (30).png")
        emoji3 = load_base64("static/images/Image (38).png")


        c1, c2, c3 = st.columns(3)

        st.markdown("""
        <style>
            div[data-testid="stButton"] button {
                display: none !important;
            }
                    
        /* Mobile layout */
        @media (max-width: 900px) {
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
        

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
                    font-size: clamp(0.5rem, 1.5rem, 2rem);
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
            "⭐⭐⭐\nТийм, үнэ цэнтэй ач холбогдолтой", "⭐⭐\n Сайн, гэхдээ сайжруулах шаардлагатай ", "⭐\nАч холбогдолгүй, үр ашиггүй",
        ]

        answer_key = "Team_Collaboration_Satisfaction"

        def onRadioChange():
            submitAnswer(answer_key,st.session_state.get(answer_key))
            goToNextPageForRadio()
        
        # --- Create radio group ---
        choice = st.radio(
            "",
            options,
            horizontal=True,
            key="Team_Collaboration_Satisfaction",
            index=None,  
            on_change=onRadioChange
        )


        # with c1:
        #      # --- Hidden Streamlit trigger ---
        #     # --- Custom HTML Button with Image + Text ---
        #     components.html(f"""
        #         <button id="imgBtn" style=" 
        #             background: #fff;
        #             padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
        #             border: 1px solid #ccc;
        #             border-radius: 15px;
        #             cursor: pointer;
        #             display: flex;
        #             flex-direction: column;
        #             align-items: center;
        #             justify-content: center;
        #             gap: 1rem;
        #             width: 100%;
        #             max-width: 420px;
        #             height: 25rem;
        #         ">
        #             <span style="font-size: clamp(0.5rem, 1, 2rem)">Тийм, үнэ цэнтэй ач холбогдолтой</span>
        #         </button>

        #         <script>
        #             document.getElementById("imgBtn").onclick = () => {{
        #                 const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
        #                 if (btn) btn.click();
        #             }};
        #         </script>

        #     """, height=450)
        # with c2:
        #     # --- Custom HTML Button with Image + Text ---
        #     components.html(f"""
        #         <button id="imgBtn" style=" 
        #             background: #fff;
        #             border: 1px solid #ccc;
        #             padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
        #             border-radius: 15px;
        #             cursor: pointer;
        #             display: flex;
        #             flex-direction: column;
        #             align-items: center;
        #             justify-content: center;
        #             width: 100%;
        #             max-width: 420px;
        #             height: 25rem;   

        #         ">
        #             <span style="font-size: clamp(0.5rem, 1, 2rem);">Сайн, гэхдээ сайжруулах шаардлагатай</span>
        #         </button>   

        #         <script>    
        #             document.getElementById("imgBtn").onclick = () => {{
        #                 const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
        #                 if (btn) btn[1].click();
        #             }};
        #         </script>

        #     """, height=450)    
        # with c3:
        #     # --- Custom HTML Button with Image + Text ---
        #     components.html(f"""
        #         <button id="imgBtn" style=" 
        #             background: #fff;
        #             border: 1px solid #ccc;
        #             padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
        #             border-radius: 15px;
        #             cursor: pointer;
        #             display: flex;
        #             flex-direction: column;
        #             align-items: center;
        #             justify-content: center;
        #             width: 100%;
        #             max-width: 420px;
        #             height: 25rem;   

        #         ">
        #             <span style="font-size: clamp(0.5rem, 1, 2rem);">Ач холбогдолгүй,<br> Үр ашиггүй</span>
        #         </button>   

        #         <script>    
        #             document.getElementById("imgBtn").onclick = () => {{
        #                 const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
        #                 if (btn) btn[1].click();
        #             }};
        #         </script>

        #     """, height=450)    
        

        
        # answer_key = "Value_Of_Benefits"

        # button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Тийм, үнэ цэнтэй ач холбогдолтой"))
        # button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Сайн, гэхдээ сайжруулах шаардлагатай"))
        # button3 = st.button("trigger2", key="r{answer_key}3", on_click=lambda: submitAnswer(answer_key, "Ач холбогдолгүй, үр ашиггүй"))
        
        # if( button1 or button2 or button3):
        #     goToNextPage()

    progress_chart()


elif st.session_state.page == 12:
    header()
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
                    
            <h1 style="text-align: left; margin-left: 0; font-size: clamp(1rem, 1.5rem, 2rem); height: 55vh; display:table; ">
                <p style="display:table-cell; vertical-align: middle;">Таны ажлын гүйцэтгэлийг (<span style="color: #ec1c24;">KPI, LTI</span>) үнэн зөв, шударга үнэлэн дүгнэдэг байсан уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
    
            c1, c2, c3 = st.columns(3)

            st.markdown("""
            <style>
                div[data-testid="stButton"] button {
                    display: none !important;
                }
                        
            /* Mobile layout */
            @media (max-width: 900px) {
                div[data-testid="stHorizontalBlock"] {
                    flex-direction: column !important;
                }
            }
            </style>
        """, unsafe_allow_html=True)
            

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
                        font-size: clamp(0.5rem, 1.5rem, 2rem);
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
                "⭐⭐⭐⭐\nШударга, үнэн зөв үнэлдэг", "⭐⭐⭐\n Зарим нэг үзүүлэлт зөрүүтэй үнэлдэг ", "⭐⭐\nҮнэлгээ миний гүйцэтгэлтэй нийцдэггүй ","⭐\nМиний гүйцэтгэлийг хэрхэн үнэлснийг би ойлгодоггүй"
            ]

            answer_key = "Accuracy_Of_KPI_Evaluation"

            def onRadioChange():
                submitAnswer(answer_key,st.session_state.get(answer_key))
                goToNextPageForRadio()
            
            # --- Create radio group ---
            choice = st.radio(
                "",
                options,
                horizontal=True,
                key="Accuracy_Of_KPI_Evaluation",
                index=None,  
                on_change=onRadioChange
            )
       

     
    
     
    #     import base64
    #     from pathlib import Path

    #     def load_base64(path):
    #         img_bytes = Path(path).read_bytes()
    #         return base64.b64encode(img_bytes).decode()
        
    #     emoji1 = load_base64("static/images/Image (39).png")
    #     emoji2 = load_base64("static/images/Image (21).png")
    #     emoji3 = load_base64("static/images/Image (22).png")
    #     emoji4 = load_base64("static/images/Image (35).png")


    #     c1, c2, c3, c4 = st.columns(4)
        



    #     st.markdown("""
    #     <style>
    #         div[data-testid="stButton"] button {
    #             display: none !important;
    #         }
                    
    #     /* Mobile layout */
    #     @media (max-width: 900px) {
    #         div[data-testid="stHorizontalBlock"] {
    #             flex-direction: column !important;
    #         }
    #     }
    #     </style>
    # """, unsafe_allow_html=True)



    #     with c1:
    #          # --- Hidden Streamlit trigger ---
    #         # --- Custom HTML Button with Image + Text ---
    #         components.html(f"""
    #             <button id="imgBtn" style=" 
    #                 background: #fff;
    #                 padding: clamp(4rem, 6rem, 8rem) clamp(1rem, 1rem, 4rem);
    #                 border: 1px solid #ccc;
    #                 border-radius: 15px;
    #                 cursor: pointer;
    #                 display: flex;
    #                 flex-direction: column;
    #                 align-items: center;
    #                 justify-content: center;
    #                 width: 100%;
    #                 max-width: 420px;
    #                 height: 25rem;   
    #             ">
    #                 </br>
    #                 <span style="font-size: clamp(1rem, 1rem, 2.5rem)">Шударга,<br> үнэн зөв үнэлдэг</span>
    #             </button>

    #             <script>
    #                 document.getElementById("imgBtn").onclick = () => {{
    #                     const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
    #                     if (btn) btn.click();
    #                 }};
    #             </script>

    #         """, height=450)

    #     with c2:
    #         # --- Custom HTML Button with Image + Text ---
    #         components.html(f"""
    #             <button id="imgBtn" style=" 
    #                 background: #fff;
    #                 border: 1px solid #ccc;
    #                 padding: clamp(4rem, 6rem, 8rem) clamp(1rem, 1rem, 4rem);
    #                 border-radius: 15px;
    #                 cursor: pointer;
    #                 display: flex;
    #                 flex-direction: column;
    #                 align-items: center;
    #                 justify-content: center;
    #                 width: 100%;
    #                 max-width: 420px;   
    #                 height: 25rem;

    #             ">
    #                 </br>
    #                 <span style="font-size: clamp(1rem, 1rem, 2.5rem);">Зарим нэг үзүүлэлт зөрүүтэй үнэлдэг</span>
    #             </button>   

    #             <script>    
    #                 document.getElementById("imgBtn").onclick = () => {{
    #                     const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
    #                     if (btn) btn[1].click();
    #                 }};
    #             </script>

    #         """, height=450)    
    #     with c3:
    #         # --- Custom HTML Button with Image + Text ---
    #         components.html(f"""
    #             <button id="imgBtn" style=" 
    #                 background: #fff;
    #                 border: 1px solid #ccc;
    #                 padding: clamp(4rem, 6rem, 8rem) clamp(1rem, 1rem, 4rem);
    #                 border-radius: 15px;
    #                 cursor: pointer;
    #                 display: flex;
    #                 flex-direction: column;
    #                 align-items: center;
    #                 justify-content: center;
    #                 width: 100%;
    #                 max-width: 420px;
    #                 height: 25rem;   

    #             ">
    #                 </br>
    #                 <span style="font-size: clamp(1rem, 1rem, 2.5rem);">Үнэлгээ миний гүйцэтгэлтэй нийцдэггүй</span>
    #             </button>   

    #             <script>    
    #                 document.getElementById("imgBtn").onclick = () => {{
    #                     const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
    #                     if (btn) btn[1].click();
    #                 }};
    #             </script>

    #         """, height=450)    
        
    #     with c4:
    #         # --- Custom HTML Button with Image + Text ---
    #         components.html(f"""
    #             <button id="imgBtn" style=" 
    #                 background: #fff;
    #                 border: 1px solid #ccc;
    #                 padding: clamp(4rem, 6rem, 8rem) clamp(1rem, 1rem, 4rem);
    #                 border-radius: 15px;
    #                 cursor: pointer;
    #                 display: flex;
    #                 flex-direction: column;
    #                 align-items: center;
    #                 justify-content: center;
    #                 width: 100%;
    #                 max-width: 420px;  
    #                 height: 25rem; 

    #             ">
    #                 </br>
    #                 <span style="font-size: clamp(1rem, 1rem, 2.5rem);">Миний гүйцэтгэлийг хэрхэн үнэлснийг би ойлгодоггүй</span>
    #             </button>   

    #             <script>    
    #                 document.getElementById("imgBtn").onclick = () => {{
    #                     const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
    #                     if (btn) btn[1].click();
    #                 }};
    #             </script>

    #         """, height=450)    
        

        

    #     button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Шударга, үнэн зөв үнэлдэг"))
    #     button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Зарим нэг үзүүлэлт зөрүүтэй үнэлдэг"))
    #     button3 = st.button("trigger3", key="r{answer_key}3", on_click=lambda: submitAnswer(answer_key, "Үнэлгээ миний гүйцэтгэлтэй нийцдэггүй"))
    #     button4 = st.button("trigger4", key="r{answer_key}4", on_click=lambda: submitAnswer(answer_key, "Миний гүйцэтгэлийг хэрхэн үнэлснийг би ойлгодоггүй"))
        
    #     if( button1 or button2 or button3 or button4):
    #         goToNextPage()


    progress_chart()


elif st.session_state.page == 13:
    header()
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
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3; height: 55vh; display:table; ">
                <p style="display:table-cell; vertical-align: middle;">Таны бодлоор компанидаа ажил, мэргэжлийн хувьд <span style="color: #ec1c24;">өсөж, хөгжих</span> боломж хангалттай байсан уу?</p>
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
                    font-size: clamp(0.5rem, 1.5rem, 2rem);
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
            "⭐⭐⭐\nӨсөж хөгжих боломж хангалттай байдаг", "⭐⭐\nХангалттай биш", "⭐\nӨсөж хөгжих боломж байдаггүй",
        ]

        answer_key = "Career_Growth_Opportunities"

        def onRadioChange():
            submitAnswer(answer_key,st.session_state.get(answer_key))
            goToNextPageForRadio()
        
        # --- Create radio group ---
        choice = st.radio(
            "",
            options,
            horizontal=True,
            key="Career_Growth_Opportunities",
            index=None,  
            on_change=onRadioChange
        )

    #     import base64
    #     from pathlib import Path

    #     def load_base64(path):
    #         img_bytes = Path(path).read_bytes()
    #         return base64.b64encode(img_bytes).decode()
        
    #     emoji1 = load_base64("static/images/Image (28).png")
    #     emoji2 = load_base64("static/images/Image (24).png")
    #     emoji3 = load_base64("static/images/Image (25).png")


    #     c1, c2, c3 = st.columns(3)
        

    #     st.markdown("""
    #     <style>
    #         div[data-testid="stButton"] button {
    #             display: none !important;
    #         }
                    
    #     /* Mobile layout */
    #     @media (max-width: 900px) {
    #         div[data-testid="stHorizontalBlock"] {
    #             flex-direction: column !important;
    #         }
    #     }
    #     </style>
    # """, unsafe_allow_html=True)


    #     with c1:
    #          # --- Hidden Streamlit trigger ---
    #         # --- Custom HTML Button with Image + Text ---
    #         components.html(f"""
    #             <button id="imgBtn" style=" 
    #                 background: #fff;
    #                 padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
    #                 border: 1px solid #ccc;
    #                 border-radius: 15px;
    #                 cursor: pointer;
    #                 display: flex;
    #                 flex-direction: column;
    #                 align-items: center;
    #                 justify-content: center;
    #                 gap: 1rem;
    #                 width: 100%;
    #                 max-width: 420px;  
    #                 height: 25rem;

    #             ">
    #                 <span style="font-size: clamp(0.1rem, 0.5, 2rem)">Өсөж хөгжих боломж хангалттай байдаг</span>
    #             </button>

    #             <script>
    #                 document.getElementById("imgBtn").onclick = () => {{
    #                     const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
    #                     if (btn) btn.click();
    #                 }};
    #             </script>

    #         """, height=450)

            
    #     with c2:
    #         # --- Custom HTML Button with Image + Text ---
    #         components.html(f"""
    #             <button id="imgBtn" style=" 
    #                 background: #fff;
    #                 border: 1px solid #ccc;
    #                 padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
    #                 border-radius: 15px;
    #                 cursor: pointer;
    #                 display: flex;
    #                 flex-direction: column;
    #                 align-items: center;
    #                 justify-content: center;
    #                 width: 100%;
    #                 max-width: 420px;   
    #                 height: 25rem;
    #             ">
    #                 <span style="font-size: clamp(0.1rem, 0.5, 2rem);">Хангалттай биш</span>
    #             </button>   

    #             <script>    
    #                 document.getElementById("imgBtn").onclick = () => {{
    #                     const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
    #                     if (btn) btn[1].click();
    #                 }};
    #             </script>

    #         """, height=450)    
    #     with c3:
    #         # --- Custom HTML Button with Image + Text ---
    #         components.html(f"""
    #             <button id="imgBtn" style=" 
    #                 background: #fff;
    #                 border: 1px solid #ccc;
    #                 padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
    #                 border-radius: 15px;
    #                 cursor: pointer;
    #                 display: flex;
    #                 flex-direction: column;
    #                 align-items: center;
    #                 justify-content: center;
    #                 width: 100%;
    #                 max-width: 420px; 
    #                 height: 25rem;
    #             ">
    #                 <span style="font-size: clamp(0.1rem, 0.5, 2rem);">Өсөж хөгжих боломж байдаггүй</span>
    #             </button>   

    #             <script>    
    #                 document.getElementById("imgBtn").onclick = () => {{
    #                     const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
    #                     if (btn) btn[1].click();
    #                 }};
    #             </script>

    #         """, height=450)    
        

        
    #     answer_key = "Career_Growth_Opportunities"

    #     button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Өсөж хөгжих боломж хангалттай байдаг"))
    #     button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Хангалттай биш"))
    #     button3 = st.button("trigger2", key="r{answer_key}3", on_click=lambda: submitAnswer(answer_key, "Өсөж хөгжих боломж байдаггүй"))
        
    #     if( button1 or button2 or button3):
    #         goToNextPage()


    progress_chart()

elif st.session_state.page == 14:
    header()
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
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3; height: 40vh; display:table;">
                <p style="display:table-cell; vertical-align: middle;">Компаниас зохион байгуулдаг <span style="color: #ec1c24;"> сургалтууд </span> чанартай үр дүнтэй байж таныг ажил мэргэжлийн ур чадвараа нэмэгдүүлэхэд дэмжлэг үзүүлж чадсан уу?</p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        with st.spinner("loading"):
            import base64
            from pathlib import Path

            def load_base64(path):
                img_bytes = Path(path).read_bytes()
                return base64.b64encode(img_bytes).decode()
            
            emoji1 = load_base64("static/images/Image (15).png")
            emoji2 = load_base64("static/images/Image (5).png")
            emoji3 = load_base64("static/images/Image (9).png")


            c1, c2, c3 = st.columns(3)
            

            st.markdown("""
                    <style>
                        div[data-testid="stButton"] button {
                            display: none !important;
                        }
                                
                    /* Mobile layout */
                    @media (max-width: 900px) {
                        div[data-testid="stHorizontalBlock"] {
                            flex-direction: column !important;
                        }
                    }
                    </style>
                """, unsafe_allow_html=True)


            with c1:
                # --- Hidden Streamlit trigger ---
                # --- Custom HTML Button with Image + Text ---
                with st.spinner("loading"):
                    components.html(f"""
                    <button id="imgBtn" style=" 
                        background: #fff;
                        padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                        border: 1px solid #ccc;
                        border-radius: 15px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: space-between;
                        gap: 1rem;
                        width: 100%;
                        max-width: 420px;  
                        height: 25rem;

                    ">
                        <img src="data:image/png;base64,{emoji1}" width="clamp(60px, 15vw, 130px)" height="150">
                        <br/>                    
                        <span style="font-size: clamp(0.1rem, 0.5, 2rem)">Маш сайн</span>
                    </button>

                    <script>
                        document.getElementById("imgBtn").onclick = () => {{
                            const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
                            if (btn) btn.click();
                        }};
                    </script>

                """, height=450)

            
            with c2:
                # --- Custom HTML Button with Image + Text ---
                with st.spinner("loading"):
                    components.html(f"""
                    <button id="imgBtn" style=" 
                        background: #fff;
                        border: 1px solid #ccc;
                        padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                        border-radius: 15px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: space-between;
                        width: 100%;
                        max-width: 420px;   
                        height: 25rem;
                    ">
                        <img src="data:image/png;base64,{emoji2}" width="auto" height="150">
                        <br/>
                        <br/>
                        <br/>
                        <span style="font-size: clamp(0.1rem, 0.5, 2rem);">Сайн, гэхдээ сайжруулах шаардлагатай</span>
                    </button>   

                    <script>    
                        document.getElementById("imgBtn").onclick = () => {{
                            const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                            if (btn) btn[1].click();
                        }};
                    </script>

                """, height=450)    
            with c3:
                # --- Custom HTML Button with Image + Text ---
                with st.spinner("loading"):
                    components.html(f"""
                    <button id="imgBtn" style=" 
                        background: #fff;
                        border: 1px solid #ccc;
                        padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                        border-radius: 15px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: space-between;
                        width: 100%;
                        max-width: 420px; 
                        height: 25rem;
                    ">
                        <img src="data:image/png;base64,{emoji3}" width="auto" height="150">
                        <br/>
                        <br/> 
                        <br/> 
                        <span style="font-size: clamp(0.1rem, 0.5, 2rem);">Үр дүнгүй</span>
                    </button>   

                    <script>    
                        document.getElementById("imgBtn").onclick = () => {{
                            const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                            if (btn) btn[1].click();
                        }};
                    </script>

                """, height=450)    
            

            
            answer_key = "Quality_Of_Training_Programs"

            button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Маш сайн"))
            button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Сайн, гэхдээ сайжруулах шаардлагатай"))
            button3 = st.button("trigger2", key="r{answer_key}3", on_click=lambda: submitAnswer(answer_key, "Үр дүнгүй"))
            
            if( button1 or button2 or button3):
                goToNextPage()
        
    progress_chart()

        
elif st.session_state.page == 15:
    header()
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
            <h1 style="font-size: clamp(1rem, 1.5rem, 2rem); line-height: 1.3; height: 55vh; display:table; ">
                <p style="display:table-cell; vertical-align: middle;"> Та ойрын хүрээлэлдээ "<span style="color: #ec1c24;">АПУ ХХК</span>" -т ажилд орохыг санал болгох уу? </p>
            </h1>
        """, unsafe_allow_html=True)
    with col2:
        import base64
        from pathlib import Path

        def load_base64(path):
            img_bytes = Path(path).read_bytes()
            return base64.b64encode(img_bytes).decode()
        
        emoji1 = load_base64("static/images/Image (25).png")
        emoji2 = load_base64("static/images/Image (16).png")


        c1, c2 = st.columns(2)
        
        st.markdown("""
                <style>
                    div[data-testid="stButton"] button {
                        display: none !important;
                    }
                            
                /* Mobile layout */
                @media (max-width: 900px) {
                    div[data-testid="stHorizontalBlock"] {
                        flex-direction: column !important;
                    }
                }
                </style>
            """, unsafe_allow_html=True)

        with c1:
             # --- Hidden Streamlit trigger ---
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border: 1px solid #ccc;
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 1rem;
                    width: 100%;
                    max-width: 420px;
                    height: 25rem;
                ">
                    <img src="data:image/png;base64,{emoji1}" width="clamp(60px, 15vw, 130px)" height="180">
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem)">Тийм</span>
                </button>

                <script>
                    document.getElementById("imgBtn").onclick = () => {{
                        const btn = parent.document.querySelector('button[data-testid="stBaseButton-secondary"][kind="secondary"]:first-of-type');
                        if (btn) btn.click();
                    }};
                </script>

                """, height=450)

        
        with c2:
            # --- Custom HTML Button with Image + Text ---
            with st.spinner("loading"):
                components.html(f"""
                <button id="imgBtn" style=" 
                    background: #fff;
                    border: 1px solid #ccc;
                    padding: clamp(6rem, 2vw, 8rem) clamp(3rem, 2vw, 4rem);
                    border-radius: 15px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    max-width: 420px;   
                    height: 25rem;
                ">
                    <img src="data:image/png;base64,{emoji2}" width="auto" height="180">
                    <br/>
                    <span style="font-size: clamp(1.2rem, 2vw, 2rem);">Үгүй</span>
                </button>   

                <script>    
                    document.getElementById("imgBtn").onclick = () => {{
                       const btn = parent.document.querySelectorAll('button[data-testid="stBaseButton-secondary"][kind="secondary"]');
                        if (btn) btn[1].click();
                    }};
                </script>

                """, height=450)    
            
        
        answer_key = "Loyalty"

        button1 = st.button("trigger1", key="r{answer_key}1", on_click=lambda: submitAnswer(answer_key,"Тийм"))
        button2 = st.button("trigger2", key="r{answer_key}2", on_click=lambda: submitAnswer(answer_key, "Үгүй"))
        
        if( button1 or button2):
            goToNextPage()


    progress_chart()

elif st.session_state.page == "survey_end":
    with st.spinner("Submitting answers"):
        if submit_answers():
            final_thank_you()


elif st.session_state.page == "interview_0":
    interview_intro()

elif st.session_state.page == "interview_form":
    interview_form()

elif st.session_state.page == "interview_end":
    interview_end()


# progress_chart















