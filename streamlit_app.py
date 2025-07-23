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
                if s_type == "Баталгаажуулах":
                    st.session_state.page = 1  # Go to employee confirmation only
                else:
                    st.session_state.survey_type = s_type
                    st.session_state.page = 1
                st.rerun()


# ---- Page 1: Confirm employee ----
def page_1():
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
                st.session_state.emp_confirmed = True
                st.session_state.confirmed_empcode = empcode
                st.session_state.confirmed_firstname = emp["FIRSTNAME"]
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
        """)

        if st.button("Үргэлжлүүлэх"):
            if st.session_state.get("survey_category") == "Судалгааг бөглөөгүй":
                try:
                    session = get_session()
                    session.sql(f"""
                        INSERT INTO {DATABASE_NAME}.{SCHEMA_NAME}.{ANSWER_TABLE} 
                        (EMPCODE, FIRSTNAME, SURVEY_TYPE)
                        VALUES ('{empcode}', '{emp['Нэр']}', 'Судалгааг бөглөөгүй')
                    """).collect()

                    st.session_state.page = "final_thank_you"
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Хадгалах үед алдаа гарлаа: {e}")
            else:
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
    first_name = st.session_state.get("confirmed_firstname")
    survey_type = st.session_state.get("survey_type", "")
    submitted_at = datetime.utcnow()
    a = st.session_state.get("answers", {})

    # ✅ Remap survey_type to show 'Ажил хаяж явсан' in DB
    if survey_type == "Мэдээлэл бүртгэх":
        survey_type = "Ажил хаяж явсан"

    columns = [
        "EMPCODE", "FIRSTNAME", "SURVEY_TYPE", "SUBMITTED_AT",
        "Reason_for_Leaving", "Alignment_with_Daily_Tasks", "Unexpected_Responsibilities",
        "Onboarding_Effectiveness", "Company_Culture", "Atmosphere", "Conflict_Resolution",
        "Feedback", "Leadership_Style", "Team_Collaboration", "Team_Support",
        "Motivation", "Motivation_Other", "Engagement", "Engagement_Other", "Well_being",
        "Performance_Compensation", "Value_of_Benefits", "KPI_Accuracy", "Career_Growth",
        "Traning_Quality", "Loyalty1", "Loyalty1_Other", "Loyalty2", "Loyalty2_Other"
    ]

    values = [
        emp_code, first_name, survey_type, submitted_at,
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

        # ✅ Update employee status
        update_query = f"""
        UPDATE {DATABASE_NAME}.{SCHEMA_NAME}.{EMPLOYEE_TABLE}
        SET STATUS = 'Ажлаас гарсан'
        WHERE EMPCODE = '{emp_code}' AND FIRSTNAME = '{first_name}' AND STATUS = 'Идэвхтэй'
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

# ---- Main Routing ----
if not st.session_state.logged_in:
    login_page()
elif st.session_state.page == -2:
    directory_page()
elif st.session_state.page == 0:
    page_0()
elif st.session_state.page == 1:
    page_1()
elif st.session_state.page == 2:
    page_2()
elif st.session_state.page == 3:
    page_3()
elif st.session_state.page == 4:
    page_4()
elif st.session_state.page == 5:
    page_5()
elif st.session_state.page == 6:
    page_6()
elif st.session_state.page == 7:
    page_7()
elif st.session_state.page == 8:
    page_8()
elif st.session_state.page == 9:
    page_9()
elif st.session_state.page == 10:
    page_10()
elif st.session_state.page == 11:
    page_11()
elif st.session_state.page == 12:
    page_12()
elif st.session_state.page == 13:
    page_13()
elif st.session_state.page == 14:
    page_14()
elif st.session_state.page == 15:
    page_15()
elif st.session_state.page == 16:
    page_16()
elif st.session_state.page == 17:
    page_17()
elif st.session_state.page == 18:
    page_18()
elif st.session_state.page == 19:
    page_19()
elif st.session_state.page == 20:
    page_20()
elif st.session_state.page == 21:
    page_21()
elif st.session_state.page == 22:
    page_22()
elif st.session_state.page == "final_thank_you":
    final_thank_you()




























