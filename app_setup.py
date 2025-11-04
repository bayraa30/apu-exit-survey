# app_setup.py
import streamlit as st
import base64


def apply_custom_font():
    # 1️⃣ Read and base64-encode your font file
    with open("fonts/CeraPro-Medium.ttf", "rb") as f:
        font_data = f.read()
        font_base64 = base64.b64encode(font_data).decode()

    # 2️⃣ Inject the CSS using <style> and @font-face
    st.markdown(f"""
        <style>
            @font-face {{
                font-family: 'CeraPro-Medium';
                src: url(data:font/ttf;base64,{font_base64}) format('truetype');
            }}

            html, body, [class*="css"] {{
                font-family: 'CeraPro-Medium', sans-serif !important;
            }}
        </style>
    """, unsafe_allow_html=True)
