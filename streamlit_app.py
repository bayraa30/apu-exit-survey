import streamlit as st
from snowflake.snowpark import Session
from datetime import datetime

# ---- CONFIG ----
COMPANY_NAME = "АПУ ХХК"
SCHEMA_NAME = "APU"
EMPLOYEE_TABLE = "APU_EMP_DATA"
ANSWER_TABLE = f"{SCHEMA_NAME}_SURVEY_ANSWERS"
DATABASE_NAME = "CDNA_HR_DATA"
LOGO_URL = "https://i.imgur.com/DgCfZ9B.png"

# ---- Secure session ----
def get_session():
    return Session.builder.configs(st.secrets["connections.snowflake"]).create()

# ---- Survey type dictionary ----
survey_types = {
    "Компанийн санаачилгаар": ["1 жил хүртэл", "1-ээс дээш"],
    "Ажилтны санаачлагаар": [
        "6 сар дотор гарч байгаа", "7 сараас 3 жил ",
        "4-10 жил", "11 болон түүнээс дээш"
    ],
}

# ---- STATE INIT ----
for k, v in [
    ("category_selected", None),
    ("survey_type", None),
    ("page", -1),
    ("emp_confirmed", None),
    ("answers", {}),
    ("logged_in", False)
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ---- Page Config ----
st.set_page_config(page_title=f"{COMPANY_NAME} Судалгаа", layout="wide")

# ---- Utils ----
def logo():
    st.image(LOGO_URL, width=210)

def progress_chart():
    total_by_type = {
        "1 жил хүртэл": 17, "1-ээс дээш": 16,
        "6 сар дотор гарч байгаа": 20, "7 сараас 3 жил ": 19,
        "4-10 жил": 19, "11 болон түүнээс дээш": 19
    }
    if st.session_state.page < 3: return
    idx = st.session_state.page - 2
    total = total_by_type.get(st.session_state.survey_type, 19)
    st.markdown(f"#### Асуулт {idx} / {total}")
    st.progress(min(100, int((idx / total) * 100)))

# ---- Login Page ----
def login_page():
    logo()
    st.title("👨‍💼 Нэвтрэх 👩‍💼")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "hr" and password == "demo123":
            st.session_state.logged_in = True
            st.session_state.page = 0
            st.rerun()
        else:
            st.error("❌ Invalid credentials.")

# ---- Page 0: Choose category + survey ----
def page_0():
    logo()
    st.header("Ерөнхий мэдээлэл")
    st.markdown("**Судалгааны ангилал болон төрлөө сонгоно уу.**")
    category = st.selectbox("Судалгааны ангилал:",
        ["-- Сонгох --"] + list(survey_types.keys()), index=0)
    if category != "-- Сонгох --":
        st.session_state.category_selected = category
        for i, s_type in enumerate(survey_types[category]):
            if st.button(s_type, key=f"stype_{i}"):
                st.session_state.survey_type = s_type
                st.session_state.page = 1
                st.rerun()

# ---- Page 1: Confirm employee ----
def page_1():
    logo()
    st.title("Ажилтны баталгаажуулалт")
    empcode = st.text_input("Ажилтны код", key="empcode")
    firstname = st.text_input("Нэр", key="firstname")

    if st.button("Баталгаажуулах"):
        try:
            session = get_session()
            df = session.table(f"{DATABASE_NAME}.{SCHEMA_NAME}.{EMPLOYEE_TABLE}")
            match = df.filter(
                (df.empcode == empcode) & (df.firstname == firstname)
            ).collect()
            if match:
                emp = match[0]
                st.session_state.emp_confirmed = True
                st.session_state.confirmed_empcode = empcode
                st.session_state.confirmed_firstname = firstname
                st.session_state.emp_info = {
                    "Компани": emp["COMPANYNAME"],
                    "Алба хэлтэс": emp["HEADDEPNAME"],
                    "Албан тушаал": emp["POSNAME"],
                    "Овог": emp["LASTNAME"],
                    "Нэр": emp["FIRSTNAME"],
                }
            else:
                st.session_state.emp_confirmed = False
        except Exception as e:
            st.error(f"❌ Snowflake холболтын алдаа: {e}")

    if st.session_state.emp_confirmed is True:
        st.success("✅ Амжилттай баталгаажлаа!")
        emp = st.session_state.emp_info
        st.markdown(f"""
        **Компани:** {emp['Компани']}  
        **Алба хэлтэс:** {emp['Алба хэлтэс']}  
        **Албан тушаал:** {emp['Албан тушаал']}  
        **Овог:** {emp['Овог']}  
        **Нэр:** {emp['Нэр']}  
        """)
        if st.button("Үргэлжлүүлэх"):
            st.session_state.page = 2
            st.rerun()

    elif st.session_state.emp_confirmed is False:
        st.error("❌ Ажилтны мэдээлэл буруу байна. Код болон нэрийг шалгана уу.")

# ---- Page 2: Universal intro ----
def page_2():
    logo()
    st.title(st.session_state.survey_type)
    st.markdown("""
    Сайн байна уу!  
    Таны өгч буй үнэлгээ, санал хүсэлт нь бидний цаашдын хөгжлийг тодорхойлоход чухал үүрэгтэй тул дараах асуултад үнэн зөв, чин сэтгэлээсээ хариулна уу.
    """)
    if st.button("Асуулга эхлэх"):
        st.session_state.page = 3
        st.rerun()

# ---- Page 3+: Render Survey ----
def render_survey():
    from questions import survey_q_blocks  # ✅ Your original blocks
    survey_type = st.session_state.survey_type
    blocks = survey_q_blocks.get(survey_type, [])
    if not blocks:
        st.error("❌ No questions found for this survey type.")
        return

    logo()
    progress_chart()

    current_page = st.session_state.page - 3
    if current_page < len(blocks):
        blocks[current_page]()
    else:
        st.success("🎉 Судалгаа дууслаа!")
        if st.button("Submit", key="submit_btn"):
            submit_answers()

# ---- Submit answers ----
def submit_answers():
    try:
        session = get_session()
        a = st.session_state.answers
        emp_code = st.session_state.get("confirmed_empcode")
        first_name = st.session_state.get("confirmed_firstname")
        survey_type = st.session_state.get("survey_type")
        submitted_at = datetime.utcnow()

        columns = [
            "EMPCODE", "FIRSTNAME", "SURVEY_TYPE", "SUBMITTED_AT",
            "Reason_for_Leaving", "Alignment_with_Daily_Tasks", "Unexpected_Responsibilities",
            "Onboarding_Effectiveness", "Company_Culture", "Atmosphere", "Conflict_Resolution",
            "Feedback", "Leadership_Style", "Team_Collaboration", "Team_Support", "Motivation",
            "Motivation_Other", "Engagement", "Engagement_Other", "Well_being",
            "Performance_Compensation", "Value_of_Benefits", "KPI_Accuracy", "Career_Growth",
            "Traning_Quality", "Loyalty1", "Loyalty1_Other", "Loyalty2", "Loyalty2_Other"
        ]
        values = [emp_code, first_name, survey_type, submitted_at] + [a.get(c, "") for c in columns[4:]]

        query = f"""
            INSERT INTO {DATABASE_NAME}.{SCHEMA_NAME}.{ANSWER_TABLE}
            ({','.join(columns)})
            VALUES ({','.join([f'${i+1}' for i in range(len(values))])})
        """
        session.sql(query, values).collect()
        st.success("✅ Амжилттай хадгаллаа!")
    except Exception as e:
        st.error(f"❌ Хадгалах үед алдаа гарлаа: {e}")

# ---- Main Routing ----
if not st.session_state.logged_in:
    login_page()
elif st.session_state.page == -0.5:
    directory_page()
elif st.session_state.page == 0:
    page_0()
elif st.session_state.page == 1:
    page_1()
elif st.session_state.page == 2:
    page_2()
elif 3 <= st.session_state.page <= 22:
    render_survey()
else:
    st.error("🚨 Invalid page number.")



























