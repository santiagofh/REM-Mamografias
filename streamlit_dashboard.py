from pathlib import Path

import streamlit as st

from dashboard_mamografia_pages import get_navigation_pages


BASE_DIR = Path(__file__).resolve().parent


st.set_page_config(
    page_title="Dashboard Cobertura Mamografía 2025",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #F6FAFD 0%, #FFFFFF 14%, #FFFFFF 100%);
    }
    .stApp h1, .stApp h2, .stApp h3 {
        color: #006FB3;
        font-weight: 700;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .info-card {
        background: linear-gradient(135deg, #F3F8FC 0%, #E6F0F8 100%);
        border: 1px solid #C8DDED;
        border-radius: 8px;
        padding: 1.15rem 1.2rem;
        box-shadow: 0 10px 28px rgba(31, 78, 121, 0.08);
    }
    .info-card-title {
        color: #1F4E79;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.65rem;
    }
    .provisional-badge {
        display: inline-block;
        margin: 0.15rem 0 0.6rem 0;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: #FFF3CD;
        border: 1px solid #F2C94C;
        color: #7A4D00;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .soft-note {
        color: #315B7D;
        font-size: 0.95rem;
        line-height: 1.45;
    }
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #D9E6F2;
        border-radius: 8px;
        padding: 0.85rem 0.95rem;
        box-shadow: 0 8px 20px rgba(31, 78, 121, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_path = BASE_DIR / "assets" / "seremi_sidebar_logo.svg"
icon_path = BASE_DIR / "assets" / "seremi_sidebar_icon.svg"
if logo_path.exists() and icon_path.exists():
    st.logo(str(logo_path), size="large", icon_image=str(icon_path))

navigation = st.navigation(get_navigation_pages(), position="sidebar", expanded=True)
navigation.run()
