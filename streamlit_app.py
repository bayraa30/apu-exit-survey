import streamlit as st
from snowflake.snowpark import Session
from datetime import datetime


# ---- CONFIG ----
COMPANY_NAME = "АПУ ХХК"
SCHEMA_NAME = "APU"
EMPLOYEE_TABLE = "APU_EMP_DATA_JULY2025"
ANSWER_TABLE = f"{SCHEMA_NAME}_SURVEY_ANSWERS"
DATABASE_NAME = "CDNA_HR_DATA"
LOGO_URL = "https://i.imgur.com/DgCfZ9B.png"
LINK_TABLE = f"{SCHEMA_NAME}_SURVEY_LINKS"  # -> APU_SURVEY_LINKS
BASE_URL = "https://apu-exit-survey-cggmobn4x6kmsmpavyuu5z.streamlit.app/"  

# ---- Secure session ----
def get_session():
    return Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# ---- Survey type dictionary ----
survey_types = {
    "Компанийн санаачилгаар": ["1 жил хүртэл", "1-ээс дээш"],
    "Ажилтны санаачлагаар": [
        "6 сар дотор гарч байгаа", "7 сараас 3 жил ",
        "4-10 жил", "11 болон түүнээс дээш"
    ],
    "Ажил хаяж явсан": ["Мэдээлэл бүртгэх"]
}
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
    params = st.experimental_get_query_params()

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


st.write("DEBUG:",
         "logged_in =", st.session_state.get("logged_in"),
         "page =", st.session_state.get("page"),
         "params =", st.experimental_get_query_params())
# 🔹 NEW: try to initialize from link token (if any)
init_from_link_token()

# ---- Login Page ----
def login_page():
    logo()
    st.title("👨‍💼 Нэвтрэх 👩‍💼")

    valid_users = st.secrets["users"]  # Securely loaded

    username = st.text_input("Нэвтрэх нэр")
    password = st.text_input("Нууц үг", type="password")

    if st.button("Нэвтрэх"):
        if username in valid_users and password == valid_users[username]:
            st.session_state.logged_in = True
            st.session_state.page = -2
            st.rerun()
        else:
            st.error("❌ Нэвтрэх нэр эсвэл нууц үг буруу байна.")

# =====================
#   TABLE VIEW PAGE
# =====================
def table_view_page():
    import pandas as pd
    logo()
    st.title("🧾 Бөглөсөн судалгааны жагсаалт (шинэ)")

    try:
        session = get_session()
        schema = SCHEMA_NAME
        db = DATABASE_NAME

        # Join latest answers with employee master (July snapshot)
        q = f"""
        WITH answers AS (
            SELECT
                COALESCE(EMPCODE, EMPCODE) AS EMP_CODE,
                SUBMITTED_AT
            FROM {db}.{schema}.APU_SURVEY_ANSWERS
            WHERE SUBMITTED_AT IS NOT NULL
        )
        SELECT
            a.EMP_CODE,
            a.SUBMITTED_AT,
            e.LASTNAME,
            e.FIRSTNAME,
            e.COMPANYNAME,
            e.DEPNAME,
            e.POSNAME
        FROM answers a
        LEFT JOIN {db}.{schema}.APU_EMP_DATA_JULY2025 e
            ON COALESCE(e.EMPCODE, e.EMPCODE) = a.EMP_CODE
        ORDER BY a.SUBMITTED_AT DESC
        """
        df = session.sql(q).to_pandas()

        # Optional tidy-up/labels
        df.rename(columns={
            "EMP_CODE": "Ажилтны код",
            "SUBMITTED_AT": "Бөглөсөн огноо",
            "LASTNAME": "Овог",
            "FIRSTNAME": "Нэр",
            "COMPANYNAME": "Компани",
            "DEPNAME": "Хэлтэс",
            "POSNAME": "Албан тушаал",
        }, inplace=True)

        # Show table
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Snowflake холболтын алдаа: {e}")

    # Continue to directory
    if st.button("Үргэлжлүүлэх → Судалгааны сонголт"):
        st.session_state.page = -0.5
        st.rerun()

# ---- DIRECTORY PAGE ----
def directory_page():
    st.image(LOGO_URL, width=210)
    st.title("Судалгааны төрлөө сонгоно уу")

    option = st.radio("Та хийх гэж буй судалгааны төрлийг сонгоно уу:", 
                      ["📋 Гарах судалгаа", "🎤 Гарах ярилцлага"], 
                      index=None)

    if st.button("Үргэлжлүүлэх"):
        if option == "📋 Гарах судалгаа":
            st.session_state.page = 0
            st.rerun()
        elif option == "🎤 Гарах ярилцлага":
            st.warning("🎤 Ярилцлагын горим удахгүй нэмэгдэх болно.")
        else:
            st.error("❌ Та судалгааны төрлөө сонгоно уу.")

# ---- TABLE VIEW ----
if not st.session_state.logged_in:
    login_page()
    st.stop()
elif st.session_state.page == -2:
    table_view_page()
    st.stop()
elif st.session_state.page == -0.5:
    directory_page()
    st.stop()

# ---- Page 0: Choose category + survey ----
def page_0():
    logo()
    st.header("Ерөнхий мэдээлэл")
    st.markdown("**Судалгааны ангиллаа сонгоно уу.**")

    category = st.selectbox(
        "Судалгааны ангилал:",
        ["-- Сонгох --"] + list(survey_types.keys()),
        index=0 if not st.session_state.category_selected
              else list(survey_types.keys()).index(st.session_state.category_selected) + 1,
        key="category_select"
    )

    if category != "-- Сонгох --":
        set_category(category)

    if st.session_state.category_selected:
        if st.button("Үргэлжлүүлэх"):
            st.session_state.page = 1  # → Employee confirmation
            st.rerun()

# ---- Page 1: Confirm employee ----
def page_1():
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

    logo()
    st.title("Ажилтны баталгаажуулалт")

    empcode = st.text_input("Ажилтны код", key="empcode")

    if st.button("Баталгаажуулах"):
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


# ---- PAGE 2: UNIVERSAL INTRO ----
def page_2():
    if not st.session_state.get("confirmed_empcode") or not st.session_state.get("confirmed_firstname"):
        st.error("❌ Ажилтны мэдээлэл баталгаажаагүй байна. Эхний алхмыг дахин шалгана уу.")
        st.stop()

    logo()
    st.markdown("Сайн байна уу!")
    st.markdown(
        "Таны өгч буй үнэлгээ, санал хүсэлт нь бидний цаашдын хөгжлийг тодорхойлоход чухал үүрэгтэй тул дараах асуултад үнэн зөв, чин сэтгэлээсээ хариулна уу."
    )

    # ✅ Define survey_type here
    survey_type = st.session_state.get("survey_type", "")

    if st.button("Асуулга эхлэх", key="btn_begin"):
        if survey_type == "Мэдээлэл бүртгэх":
            if submit_answers():
                st.session_state.page = "final_thank_you"
                st.rerun()
            else:
                st.error("❌ Хадгалах үед алдаа гарлаа.")
        else:
            st.session_state.page = 3
            st.rerun()


# ---- Submit answers ----
def submit_answers():
    emp_code = st.session_state.get("confirmed_empcode")
    survey_type = st.session_state.get("survey_type", "")
    submitted_at = datetime.utcnow()
    a = st.session_state.get("answers", {})

    if survey_type == "Мэдээлэл бүртгэх":
        survey_type = "Ажил хаяж явсан"

    columns = [
        "EMPCODE", "SURVEY_TYPE", "SUBMITTED_AT",
        "Reason_for_Leaving", "Alignment_with_Daily_Tasks", "Unexpected_Responsibilities",
        "Onboarding_Effectiveness", "Company_Culture", "Atmosphere", "Conflict_Resolution",
        "Feedback", "Leadership_Style", "Team_Collaboration", "Team_Support",
        "Motivation", "Motivation_Other", "Engagement", "Engagement_Other", "Well_being",
        "Performance_Compensation", "Value_of_Benefits", "KPI_Accuracy", "Career_Growth",
        "Traning_Quality", "Loyalty1", "Loyalty1_Other", "Loyalty2", "Loyalty2_Other"
    ]

    values = [
        emp_code, survey_type, submitted_at,
        a.get("Reason_for_Leaving"), a.get("Alignment_with_Daily_Tasks"),
        a.get("Unexpected_Responsibilities"), a.get("Onboarding_Effectiveness"),
        a.get("Company_Culture"), a.get("Atmosphere"), a.get("Conflict_Resolution"),
        a.get("Feedback"), a.get("Leadership_Style"), a.get("Team_Collaboration"),
        a.get("Team_Support"), a.get("Motivation"), a.get("Motivation_Other"),
        a.get("Engagement"), a.get("Engagement_Other"), a.get("Well_being"),
        a.get("Performance_Compensation"), a.get("Value_of_Benefits"), a.get("KPI_Accuracy"),
        a.get("Career_Growth"), a.get("Traning_Quality"), a.get("Loyalty1"),
        a.get("Loyalty1_Other"), a.get("Loyalty2"), a.get("Loyalty2_Other")
    ]

    try:
        session = get_session()

        escaped_values = [
            f"'{str(v).replace('\'', '\'\'')}'" if v not in [None, ""] else "NULL"
            for v in values
        ]

        insert_query = f"""
        INSERT INTO {SCHEMA_NAME}_SURVEY_ANSWERS ({', '.join(columns)})
        VALUES ({', '.join(escaped_values)})
        """
        session.sql(insert_query).collect()

        update_query = f"""
        UPDATE {DATABASE_NAME}.{SCHEMA_NAME}.{EMPLOYEE_TABLE}
        SET STATUS = 'Ажлаас гарсан'
        WHERE EMPCODE = '{emp_code}' AND STATUS = 'Идэвхтэй'
        """
        session.sql(update_query).collect()

        return True

    except Exception as e:
        st.error(f"❌ Хадгалах үед алдаа гарлаа: {e}")
        return False



# ---- PAGE 3: FIRST QUESTION (per survey type) ----
def page_3():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    if survey_type == "1 жил хүртэл":
        st.header("1) Таны өдөр тутмын ажил үүрэг таны хүлээлтэд нийцсэн үү?")
        q1 = st.radio(
            label="(**5 од нь хамгийн өндөр, 1 од нь хамгийн бага үнэлгээ** болно.)",
            options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            key="q1_1jil",
            index=None
        )
        answer_key = "Alignment_with_Daily_Tasks"

    elif survey_type == "1-ээс дээш":
        st.header("1) Ажлын байрны тодорхойлолтод заасан гүйцэтгэх үүргүүд таны өдөр тутмын ажилтай нийцэж байсан уу?")
        q1 = st.radio(
            label="(**5 од нь хамгийн өндөр, 1 од нь хамгийн бага үнэлгээ** болно.)",
            options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            key="q1_1deesh",
            index=None
        )
        answer_key = "Unexpected_Responsibilities"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("1) Танд ажлаас гарахад нөлөөлсөн хүчин зүйл, шалтгаантай хамгийн их тохирч байгаа 1-3 хариултыг сонгоно уу.")
        q1 = st.multiselect(
            "(1-3 хариулт сонгоно уу:)",
            [
                "🧑‍💼 Удирдлагын арга барил, харилцаа муу",
                "🏢 Компанийн соёл таалагдаагүй",
                "👥 Хамт олны уур амьсгал, харилцаа таарамжгүй",
                "💰 Цалин хөлс хангалтгүй",
                "⚖️ Гүйцэтгэлийн үнэлгээ шударга бус",
                "📈 Ажлын ачаалал их",
                "⏰ Ажлын цагийн хуваарь таарамжгүй, хэцүү байсан",
                "📋 Дасан зохицуулах хөтөлбөрийн хэрэгжилт муу",
                "📦 Өөр хот, аймаг, улсад шилжих, амьдрах",
                "🎓 Тэтгэвэрт гарч байгаа",
                "🚀 Албан тушаал/мэргэжлийн хувьд өсөх, суралцах боломжгүй",
                "🎯 Үндсэн мэргэжлийн дагуу ажиллах болсон",
                "🏗️ Хөдөлмөрийн нөхцөл хэвийн бус/хүнд хортой байсан",
                "🧘 Хувийн шалтгаан / Personal Reasons",
                "📨 Илүү боломжийн өөр ажлын байрны санал авсан",
                "🏚️ Ажлын орчин нөхцөл муу",
                "🏠 Ар гэрийн асуудал үүссэн",
                "🩺 Эрүүл мэндийн байдлаас",
                "🌍 Гадаадад улсад ажиллах/суралцах"
            ],
            key="q1_6sar"
        )
        answer_key = "Reason_for_Leaving"
        if q1:
            st.session_state.answers[answer_key] = ", ".join(q1)

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("1) Танд ажлаас гарахад нөлөөлсөн хүчин зүйл, шалтгаантай хамгийн их тохирч байгаа 1-3 хариултыг сонгоно уу.")
        q1 = st.multiselect(
            "(1-3 хариулт сонгоно уу:)",
            [
                "🧑‍💼 Удирдлагын арга барил, харилцаа муу",
                "🏢 Компанийн соёл таалагдаагүй",
                "👥 Хамт олны уур амьсгал, харилцаа таарамжгүй",
                "💰 Цалин хөлс хангалтгүй",
                "⚖️ Гүйцэтгэлийн үнэлгээ шударга бус",
                "📈 Ажлын ачаалал их",
                "⏰ Ажлын цагийн хуваарь таарамжгүй, хэцүү байсан",
                "📋 Дасан зохицуулах хөтөлбөрийн хэрэгжилт муу",
                "📦 Өөр хот, аймаг, улсад шилжих, амьдрах",
                "🎓 Тэтгэвэрт гарч байгаа",
                "🚀 Албан тушаал/мэргэжлийн хувьд өсөх, суралцах боломжгүй",
                "🎯 Үндсэн мэргэжлийн дагуу ажиллах болсон",
                "🏗️ Хөдөлмөрийн нөхцөл хэвийн бус/хүнд хортой байсан",
                "🧘 Хувийн шалтгаан / Personal Reasons",
                "📨 Илүү боломжийн өөр ажлын байрны санал авсан",
                "🏚️ Ажлын орчин нөхцөл муу",
                "🏠 Ар гэрийн асуудал үүссэн",
                "🩺 Эрүүл мэндийн байдлаас",
                "🌍 Гадаадад улсад ажиллах/суралцах"
            ],
            key="q1_busad"
        )
        answer_key = "Reason_for_Leaving"
        if q1:
            st.session_state.answers[answer_key] = ", ".join(q1)

    # Save answer and move to next page
    if q1 is not None and st.button("Дараагийн асуулт", key="btn_next_q1"):
        st.session_state.answers[answer_key] = q1
        st.session_state.page = 4
        st.rerun()

# ---- PAGE 4: Q2 (Sample, duplicate/expand as needed) ----
def page_4():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q2 = None
    answer_key = None

    if survey_type == "1 жил хүртэл":
        st.header("2. Дасан зохицох хөтөлбөрийн хэрэгжилт эсвэл баг хамт олон болон шууд удирдлага **ТАНЬД** өдөр тутмын процесс, үүрэг даалгаваруудыг хурдан ойлгоход туслах хангалттай мэдээлэл, заавар өгч чадсан уу?")
        q2 = st.radio(
            label="(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)",
            options=[
                "Маш сайн мэдээлэл заавар өгдөг. /5/",
                "Сайн мэдээлэл, заавар өгч байсан. /4/",
                "Дунд зэрэг мэдээлэл, заавар өгсөн. /3/",
                "Муу мэдээлэл, заавар өгсөн /2/",
                "Хангалтгүй /1/"

            ],
            key="Onboarding_Effectiveness",
            index=None
        )
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
        q2 = st.radio("(Таны сонголт:)", q2_choices, key='Company_Culture', index=None)
        answer_key = "Company_Culture"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("2) Таны өдөр тутмын ажил үүрэг таны хүлээлтэд нийцсэн үү?")
        q2 = st.radio(
            label="(**5 од нь хамгийн өндөр, 1 од нь хамгийн бага үнэлгээ** болно.)",
            options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            key='Alignment_with_Daily_Tasks',
            index=None
        )
        answer_key = "Alignment_with_Daily_Tasks"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("2) Ажлын байрны тодорхойлолтод заасан гүйцэтгэх үүргүүд таны өдөр тутмын ажилтай нийцэж байсан уу?")
        q2 = st.radio(
            label="(**5 од нь хамгийн өндөр, 1 од нь хамгийн бага үнэлгээ** болно.)",
            options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            key='Unexpected_Responsibilities',
            index=None
        )
        answer_key = "Unexpected_Responsibilities"

    # Save and go to next page if answered
    if q2 is not None and st.button("Дараагийн асуулт", key="btn_next_q2"):
        st.session_state.answers[answer_key] = q2
        st.session_state.page = 5
        st.rerun()


# ---- PAGE 5: Q3 (Organizational Culture Description) ----
def page_5():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None  # <-- Prevents UnboundLocalError

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
        q_answer = st.radio("(Таны сонголт:)", q3_choices, key="q3_1jil", index=None)
        answer_key = "Company_Culture"

    elif survey_type == "1-ээс дээш":
        st.header("3) Манай байгууллагын ажилтнууд хоорондоо хүндэтгэлтэй харилцаж, бие биенээ дэмждэг.")
        q3_choices = [
            "Бүрэн санал нийлж байна /5/ ❤️✨",
            "Бага зэрэг санал нийлж байна /4/ 🙂🌟",
            "Хэлж мэдэхгүй байна /3/ 😒🤷",
            "Санал нийлэхгүй байна /2/ 😕⚠️",
            "Огт санал нийлэхгүй байна /1/ 💢🚫"
        ]
        q3 = st.radio(
            label="(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)",
            options=q3_choices,
            key="q3_1deesh",
            index=None
        )
        q_answer = q3
        answer_key = "Atmosphere"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("3) Дасан зохицох хөтөлбөрийн хэрэгжилт эсвэл баг хамт олон болон шууд удирдлага **ТАНЬД** өдөр тутмын процесс, үүрэг даалгаваруудыг хурдан ойлгоход туслах хангалттай мэдээлэл, заавар өгч чадсан уу?")
        q3_choices = [
            "Маш сайн мэдээлэл заавар өгдөг. /5/",
            "Сайн мэдээлэл, заавар өгч байсан. /4/",
            "Дунд зэрэг мэдээлэл, заавар өгсөн. /3/",
            "Муу мэдээлэл, заавар өгсөн /2/",
            "Хангалтгүй /1/"
        ]
        q3 = st.radio(
            label="(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)",
            options=q3_choices,
            key="q3_6sar",
            index=None
        )
        q_answer = q3
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
        q_answer = st.radio("(Таны сонголт:)", q3_choices, key="q3_3s+", index=None)
        answer_key = "Company_Culture"

    # ✅ Save and go to next page
    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q5"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 6
        st.rerun()



#---- PAGE 6: Q4
def page_6():
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
        q_answer = st.radio("(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)", q4_choices, key="q4_1jil", index=None)
        answer_key = "Atmosphere"

    elif survey_type == "1-ээс дээш":
        st.header("4. Миний шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q4_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)", q4_choices, key="q4_1deesh_conflict", index=None)
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
        q_answer = st.radio("(Таны сонголт:)", q4_choices, key="q4_6s_culture", index=None)
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
        q_answer = st.radio("(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)", q4_choices, key="q4_3splus", index=None)
        answer_key = "Atmosphere"

    # Save and go to next page
    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q6"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 7
        st.rerun()


#---- PAGE 7: Q5
def page_7():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type == "1 жил хүртэл":
        st.header("5. Миний шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q5_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)", q5_choices, key="q5_1jil", index=None)
        answer_key = "Conflict_Resolution"

    elif survey_type == "1-ээс дээш":
        st.header("5. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажиллаж чаддаг.")
        q5_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q5_choices, key="q5_1deesh", index=None)
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
        q_answer = st.radio("(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)", q5_choices, key="q5_6s", index=None)
        answer_key = "Atmosphere"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("5. Миний шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q5_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)", q5_choices, key="q5_3splus", index=None)
        answer_key = "Conflict_Resolution"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q6"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 8
        st.rerun()



#---- PAGE 8: Q6
def page_8():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type == "1 жил хүртэл":
        st.header("6. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажиллаж чаддаг.")
        q6_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q6_choices, key="q6_1jil", index=None)
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

        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q6_choices, key="q6_1deesh", index=None)
        answer_key = "Leadership_Style"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("6. Миний шууд удирддага баг доторх зөрчилдөөнийг шийдвэрлэж чаддаг.")
        q6_choices = [
            "Бүрэн санал нийлж байна /5/",
            "Бага зэрэг санал нийлж байна. /4/",
            "Хэлж мэдэхгүй байна. /3/",
            "Санал нийлэхгүй байна. /2/",
            "Огт санал нийлэхгүй байна /1/"
        ]
        q_answer = st.radio("(**5 нь хамгийн өндөр, 1 нь хамгийн бага үнэлгээ** болно.)", q6_choices, key="q6_6sae", index=None)
        answer_key = "Conflict_Resolution"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("6. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажиллаж чаддаг.")
        q6_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q6_choices, key="q6_busad", index=None)
        answer_key = "Feedback"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q6"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 9
        st.rerun()



# ---- PAGE 9: Q7 – Leadership Style ----
def page_9():
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
        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q7_choices, key="q7_1jil", index=None)
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
        q_answer = st.radio("(🟩 нь сайн, ⬜ нь муу үнэлгээг илэрхийлнэ.)", q8_choices, key="q7_1deesh", index=None)
        answer_key = "Team_Collaboration"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("7. Таны шууд удирдлага үр дүнтэй санал зөвлөгөө өгч, эргэх холбоотой ажиллаж чаддаг.")
        q6_choices = ["Тийм 💬", "Үгүй 🔄"]
        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q6_choices, key="q7_6sar", index=None)
        answer_key = "Feedback"

    elif survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("7. Таны бодлоор ямар манлайллын хэв маяг таны удирдлагыг хамгийн сайн илэрхийлэх вэ?")
        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q7_choices, key="q7_busad", index=None)
        answer_key = "Leadership_Style"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q7"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 10
        st.rerun()

    


# ---- PAGE 10: Q8 – Team Collaboration ----
def page_10():
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
        q_answer = st.radio("(🟩 нь сайн, ⬜ нь муу үнэлгээг илэрхийлнэ.)", q8_choices, key="q8_1jil", index=None)
        answer_key = "Team_Collaboration"

    elif survey_type == "1-ээс дээш":
        st.header("8. Та байгууллагын соёл, багийн уур амьсгалыг өөрчлөх, сайжруулах талаарх саналаа бичнэ үү?")
        q_answer = st.text_area("(Таны санал:)", key="q8_1deesh")
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
        q_answer = st.radio("(Сонголтоо хийнэ үү:)", q8_choices, key="q8_6sar", index=None)
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
        q_answer = st.radio("(🟩 нь сайн, ⬜ нь муу үнэлгээг илэрхийлнэ.)", q8_choices, key="q8_busad", index=None)
        answer_key = "Team_Collaboration"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q8"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 11
        st.rerun()




# ---- PAGE 11: Q9 – Open text comment ----
def page_11():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type == "1 жил хүртэл":
        st.header("9. Та байгууллагын соёл, багийн уур амьсгалыг өөрчлөх, сайжруулах талаарх саналаа бичнэ үү?")
        q_answer = st.text_area("(Таны санал:)", key="q9_1jil")
        answer_key = "Team_Support"

    elif survey_type == "1-ээс дээш":
        st.header("9. Танд өдөр тутмын ажлаа урам зоригтой хийхэд ямар ямар хүчин зүйлс нөлөөлдөг байсан бэ?")
        st.markdown("(1-3 хариулт сонгоно уу.)")  # ✅ Add your instruction here

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

        selected = []
        cols = st.columns(2)
        for i, choice in enumerate(q9_choices):
            if cols[i % 2].checkbox(choice, key=f"q9_cb_{i}"):
                selected.append(choice)

        q9_other = ""
        if "Бусад (тайлбар оруулах)" in selected:
            q9_other = st.text_area("Та бусад нөлөөлсөн хүчин зүйлсийг бичнэ үү:", key="q9_other")

        q_answer_main = ", ".join([item for item in selected if item != "Бусад (тайлбар оруулах)"])
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
        q_answer = st.radio("(🟩 нь сайн, ⬜ нь муу үнэлгээг илэрхийлнэ.)", q9_choices, key="q9_6sar", index=None)
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
def page_12():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("10. Танд өдөр тутмын ажлаа урам зоригтой хийхэд ямар ямар хүчин зүйлс нөлөөлдөг байсан бэ?")
        st.markdown("(1-3 хариулт сонгоно уу.)")  # ✅ Add instruction here if needed

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

        selected = []
        cols = st.columns(2)
        for i, choice in enumerate(q10_choices):
            if cols[i % 2].checkbox(choice, key=f"q10_cb_{i}"):
                selected.append(choice)

        q10_other = ""
        if "Бусад (тайлбар оруулах)" in selected:
            q10_other = st.text_area("Та бусад нөлөөлсөн хүчин зүйлсийг бичнэ үү:", key="q10_other")

        motivation_main = ", ".join([item for item in selected if item != "Бусад (тайлбар оруулах)"])
        motivation_other = q10_other.strip() if q10_other.strip() else ""

        if st.button("Дараагийн асуулт", key="btn_next_q10"):
            st.session_state.answers["Motivation"] = motivation_main
            st.session_state.answers["Motivation_Other"] = motivation_other
            st.session_state.page = 13
            st.rerun()


    elif survey_type == "1-ээс дээш":
        st.header("10. Таны бодлоор ажилтны оролцоо, урам зоригийг нэмэгдүүлэхийн тулд компани ямар арга хэмжээ авбал илүү үр дүнтэй вэ?")
        st.markdown("(Хамгийн чухал гэж бодсон 1–3 хариулт сонгоно уу.)")

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

        selected_engagements = []
        cols = st.columns(2)
        for i, opt in enumerate(q10_options):
            if cols[i % 2].checkbox(opt, key=f"q10_engage_cb_{i}"):
                selected_engagements.append(opt)

        q10_other1 = ""
        if "Бусад (та доорх хэсэгт тайлбарлана уу)" in selected_engagements:
            q10_other1 = st.text_area("Бусад тайлбар:", key="q10_other1")

        if st.button("Дараагийн асуулт", key="btn_next_q10"):
            st.session_state.answers["Engagement"] = ", ".join(
                [item for item in selected_engagements if item != "Бусад (та доорх хэсэгт тайлбарлана уу)"]
            )
            if q10_other1.strip():
                st.session_state.answers["Engagement_Other"] = q10_other1.strip()
            st.session_state.page = 13
            st.rerun()


    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("10. Та байгууллагын соёл, багийн уур амьсгалыг өөрчлөх, сайжруулах талаарх саналаа бичнэ үү?")
        q_answer = st.text_area("(Таны санал:)", key="q10_6sar")

        if q_answer and st.button("Дараагийн асуулт", key="btn_next_q10"):
            st.session_state.answers["Team_Support"] = q_answer
            st.session_state.page = 13
            st.rerun()



# ---- PAGE 13: Q11 – Engagement Improvement (multi + open) ----
def page_13():
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

        q11_selected = st.multiselect(
            "Хамгийн чухал гэж бодсон 1-3 хүртэлх хариултыг сонгоно уу:",
            q11_options,
            key="q11_multiselect"
        )

        q11_other = ""
        if "Бусад (та доорх хэсэгт тайлбарлана уу)" in q11_selected:
            q11_other = st.text_area("Бусад тайлбар:", key="q11_other")

        if st.button("Дараагийн асуулт", key="btn_next_q11"):
            st.session_state.answers["Engagement"] = ", ".join(
                [item for item in q11_selected if item != "Бусад (та доорх хэсэгт тайлбарлана уу)"]
            )
            if q11_other.strip():
                st.session_state.answers["Engagement_Other"] = q11_other.strip()
            st.session_state.page = 14
            st.rerun()

    elif survey_type == "1-ээс дээш":
        st.header("11. Компани ажиллах таатай нөхцөлөөр  дэмжин ажиллаж байсан уу? /Жнь:/уян хатан цагийн хуваарь, ажлын орчин")

        q11_options = ["Хангалтгүй", "Дунд зэрэг", "Сайн", "Маш сайн"]
        q_answer = st.select_slider(
            "Үнэлгээ:",
            options=q11_options,
            value=None,
            key="q11_1deesh",
            label_visibility="visible"
        )

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

        q11_selected = st.multiselect("(1-3 хариулт сонгоно уу.)", q11_choices, key="q11_multi")

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
def page_14():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("12. Компани ажиллах таатай нөхцөлөөр  дэмжин ажиллаж байсан уу? /Жнь:/уян хатан цагийн хуваарь, ажлын орчин")

        q12_options = ["Хангалтгүй", "Дунд зэрэг", "Сайн", "Маш сайн"]
        q_answer = st.select_slider(
            "Үнэлгээ:",
            options=q12_options,
            value=None,
            key="q12_slider",
            label_visibility="visible"
        )

    elif survey_type == "1-ээс дээш":
        st.header("12. Таны цалин хөлс ажлын гүйцэтгэлтэй хэр нийцэж байсан бэ?")
        q_answer = st.radio(
            "Сонголтоо хийнэ үү:",
            [
                "Маш сайн нийцдэг",
                "Дундаж, илүү дээр байж болох л байх",
                "Миний гүйцэтгэлтэй нийцдэггүй"
            ],
            key="q12_radio",
            index=None
        )
        answer_key = "Performance_Compensation"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("12. Таны бодлоор ажилтны оролцоо, урам зоригийг нэмэгдүүлэхийн тулд компани юу хийх ёстой вэ?")
        st.markdown("(1-3 хариултыг сонгоно уу.)")

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

        selected_options = []
        for option in q12_options:
            if st.checkbox(option, key=f"q12_chk_{option}"):
                selected_options.append(option)

        q12_other = ""
        if "Бусад (та доорх хэсэгт тайлбарлана уу)" in selected_options:
            q12_other = st.text_area("Бусад тайлбар:", key="q12_other")

        if st.button("Дараагийн асуулт", key="btn_next_q12"):
            st.session_state.answers["Engagement"] = ", ".join(
                [item for item in selected_options if item != "Бусад (та доорх хэсэгт тайлбарлана уу)"]
            )
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
def page_15():
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
        st.header("13. Компаниас олгодог байсан хөнгөлөлт, тэтгэмжүүд (эрүүл мэндийн даатгал, цалинтай чөлөө, тэтгэмж гэх мэт) нь үнэ цэнтэй, ач холбогдолтой байж чадсан уу?")
        q_answer = st.radio("Сонголтоо хийнэ үү:", [
            "Тийм, үнэ цэнтэй ач холбогдолтой 💎",
            "Сайн, гэхдээ сайжруулах шаардлагатай 👍",
            "Тийм ч ач холбогдолгүй, үр ашиггүй 🤔"
        ], key="q13_benefits", index=None)
        answer_key = "Value_of_Benefits"

    elif survey_type == "6 сар дотор гарч байгаа":
        st.header("13. Компани ажиллах таатай нөхцөлөөр  дэмжин ажиллаж байсан уу? /Жнь:/уян хатан цагийн хуваарь, ажлын орчин")
        q_answer = st.select_slider("Үнэлгээ:", options=["Хангалтгүй", "Дунд зэрэг", "Сайн", "Маш сайн"], key="q13_slider")
        answer_key = "Well_being"

    if q_answer is not None and st.button("Дараагийн асуулт", key="btn_next_q13"):
        st.session_state.answers[answer_key] = q_answer
        st.session_state.page = 16
        st.rerun()


# ---- PAGE 16: Q14 – Value of Benefits ----
def page_16():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None
    answer_key = ""

    if survey_type in ["1 жил хүртэл", "7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("14. Компаниас олгодог байсан хөнгөлөлт, тэтгэмжүүд (эрүүл мэндийн даатгал, цалинтай чөлөө, тэтгэмж гэх мэт) нь үнэ цэнтэй, ач холбогдолтой байж чадсан уу?")
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
def page_17():
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
        st.header("15. Компаниас олгодог байсан хөнгөлөлт, тэтгэмжүүд (эрүүл мэндийн даатгал, цалинтай чөлөө, тэтгэмж гэх мэт) нь үнэ цэнтэй, ач холбогдолтой байж чадсан уу?")
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
def page_18():
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
                st.session_state.page = "final_thank_you"  # Thank you page
                st.rerun()



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
def page_19():
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
                    st.session_state.page = "final_thank_you"  # Thank you page
                    st.rerun()
        else:
            if st.button("Дараагийн асуулт", key="btn_next_q17"):
                st.session_state.page = 20
                st.rerun()




# ---- PAGE 20 ----
def page_20():
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
def page_21():
    logo()
    progress_chart()
    survey_type = st.session_state.survey_type

    q_answer = None

    if survey_type in ["7 сараас 3 жил ", "4-10 жил", "11 болон түүнээс дээш"]:
        st.header("19. Ирээдүйд та компанидаа эргэн орох боломж гарвал та дахин хамтран ажиллах уу?")
        q19_choices = [
            "Тийм",
            "Эргэлзэж байна",
            "Үгүй /яагаад/"
        ]
        q19 = st.radio("Сонголтоо хийнэ үү:", q19_choices, key="q19", index=None)

        q19_other = ""
        if q19 == "Үгүй /яагаад/":
            q19_other = st.text_area("Яагаад үгүй гэж үзэж байна вэ?", key="q19_other")

        if st.button("Дуусгах", key="btn_finish_q19_multi"):
            st.session_state.answers["Loyalty2"] = q19
            if q19_other.strip():
                st.session_state.answers["Loyalty2_Other"] = q19_other.strip()
            if submit_answers():
                st.session_state.page = "final_thank_you"  # jump to thank you page
                st.rerun()


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
def page_22():
    logo()
    progress_chart()

    st.header("20. Ирээдүйд та компанидаа эргэн орох боломж гарвал та дахин хамтран ажиллах уу?")
    q20_choices = [
        "Тийм",
        "Эргэлзэж байна",
        "Үгүй /яагаад/"
    ]
    q20 = st.radio("Сонголтоо хийнэ үү:", q20_choices, key="q20", index=None)

    q20_other = ""
    if q20 == "Үгүй /яагаад/":
        q20_other = st.text_area("Яагаад үгүй гэж үзэж байна вэ?", key="q20_other")

    if q20 is not None and st.button("Дуусгах", key="btn_finish_q20"):
        # ✅ Store in correct answer keys
        st.session_state.answers["Loyalty2"] = q20
        if q20_other.strip():
            st.session_state.answers["Loyalty2_Other"] = q20_other.strip()

        # ✅ Submit to Snowflake
        if submit_answers():
            st.session_state.page = "final_thank_you"  # go to thank you page
            st.rerun()

# ---Thankyou
def final_thank_you():
    logo()
    st.balloons()
    st.title("Судалгааг амжилттай бөглөлөө. Танд баярлалаа!🎉")
    st.write("Таны мэдээлэл амжилттай бүртгэгдлээ.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Цэс рүү буцах", key="btn_back_to_directory"):
            st.session_state.page = -2
            st.rerun()
    with col2:
        if st.button("🚪 Гарах", key="btn_logout"):
            st.session_state.clear()
            st.rerun()
#   HANDLERS
# =====================
def set_category(category):
    st.session_state.category_selected = category
    st.session_state.survey_type = None

def set_survey_type(survey):
    st.session_state.survey_type = survey
    st.session_state.page = 1

def go_to_intro():
    st.session_state.page = 2

def begin_survey():
    st.session_state.page = 3
# =====================
#   SINGLE ROUTER
# =====================
def route():
    # Make sure defaults exist
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = -1

    # If user comes via link, init_from_link_token() has already
    # run ABOVE this and may have changed logged_in/page.

    if not st.session_state.logged_in:
        login_page()
        return

    page = st.session_state.page
    # Optional debug:
    # st.write("ROUTE PAGE =", page)

    if page == -0.75:
        table_view_page()
    elif page in (-0.5, -2):
        directory_page()
    elif page == 0:
        page_0()
    elif page == 1:
        page_1()
    elif page == 2:
        page_2()
    elif page == 3:
        page_3()
    elif page == 4:
        page_4()
    elif page == 5:
        page_5()
    elif page == 6:
        page_6()
    elif page == 7:
        page_7()
    elif page == 8:
        page_8()
    elif page == 9:
        page_9()
    elif page == 10:
        page_10()
    elif page == 11:
        page_11()
    elif page == 12:
        page_12()
    elif page == 13:
        page_13()
    elif page == 14:
        page_14()
    elif page == 15:
        page_15()
    elif page == 16:
        page_16()
    elif page == 17:
        page_17()
    elif page == 18:
        page_18()
    elif page == 19:
        page_19()
    elif page == 20:
        page_20()
    elif page == 21:
        page_21()
    elif page == 22:
        page_22()
    elif page == "final_thank_you":
        final_thank_you()
    else:
        # Fallback
        directory_page()


# 🔚 This should be the ONLY top-level call at the bottom
route()








































