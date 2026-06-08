import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="EFFIONG AI",
    page_icon="🐆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Seamless Premium Integration Stylesheet
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600&family=Comfortaa:wght=700&display=swap');

    /* Global Obsidian Theme Base */
    .stApp {
        background-color: #0B0F17;
        color: #F0F6FC;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Clean Sidebar Architecture */
    section[data-testid="stSidebar"] {
        background-color: #121620 !important;
        border-right: 1px solid #212631;
    }
    
    /* FIX: Force Streamlit's native header background to match the application canvas */
    header[data-testid="stHeader"] {
        background-color: #0B0F17 !important;
        background: #0B0F17 !important;
    }
    
    /* Clear out header developer buttons but keep the functional navigation button */
    div[data-testid="stAppDeployButton"],
    header button[title="View app status"] {
        display: none !important;
    }
    
    footer {
        display: none !important;
    }
    
    /* Segmented Response Style Card */
    .segmented-response-box {
        background-color: #161B24;
        border-left: 4px solid #D27D2D;
        padding: 18px;
        border-radius: 6px;
        margin-top: 25px;
        margin-bottom: 10px;
        border: 1px solid #212631;
        border-left: 4px solid #D27D2D;
    }
    .segment-header {
        font-size: 0.85rem;
        color: #8B949E;
        font-weight: 600;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    
    /* Central Canvas Welcome Greeting */
    .landing-hero {
        text-align: center;
        margin-top: 15vh;
        margin-bottom: 3vh;
    }
    .landing-title {
        font-family: 'Comfortaa', cursive;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FFFFFF 30%, #D27D2D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.01em;
    }
    .landing-caption {
        font-size: 1.1rem;
        color: #8B949E;
        margin-top: 15px;
        font-weight: 400;
        letter-spacing: 0.02em;
    }
</style>
""", unsafe_allow_html=True)

from src.components.sidebar import render_effiong_sidebar
from src.components.chat_ui import render_segmented_chat

if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"
if "master_messages" not in st.session_state:
    st.session_state.master_messages = []
if "segment_threads" not in st.session_state:
    st.session_state.segment_threads = {}
if "last_spoken_trigger" not in st.session_state:
    st.session_state.last_spoken_trigger = None
if "heritage_logs" not in st.session_state:
    st.session_state.heritage_logs = [
        {"id": "NODE-001", "title": "Kingdom of Benin Bronze Casting Records", "type": "Fact Node", "status": "Verified"},
        {"id": "NODE-002", "title": "Oral Traditions of the Great Zimbabwe Architectures", "type": "Oral Track Node", "status": "Pending Verification"}
    ]

render_effiong_sidebar()
render_segmented_chat()
