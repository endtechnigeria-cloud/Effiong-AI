import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="EFFIONG AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Premium Custom CSS Injection for Styling and Segmented Responses
st.markdown("""
<style>
    /* Premium dark high-contrast dashboard look */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #30363D;
    }
    /* Segmented/Threaded chat response boxes */
    .segmented-response-box {
        background-color: #1F242C;
        border-left: 4px solid #FF9800; /* Vibrant African Bronze/Orange Accent */
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .segment-header {
        font-size: 0.85rem;
        color: #8B949E;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    /* Matrix disclaimer styling */
    .disclaimer-box {
        font-size: 0.85rem;
        background-color: #211818;
        border: 1px solid #F44336;
        color: #FFCDD2;
        padding: 10px;
        border-radius: 4px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Dynamic Imports from our local src folder structures
from src.components.sidebar import render_effiong_sidebar
from src.components.chat_ui import render_segmented_chat

# Initialize vital session state structures
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat" # or "heritage"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "heritage_logs" not in st.session_state:
    st.session_state.heritage_logs = [
        {"id": "NODE-001", "title": "Kingdom of Benin Bronze Casting Records", "type": "Fact Node", "status": "Verified"},
        {"id": "NODE-002", "title": "Oral Traditions of the Great Zimbabwe Architectures", "type": "Oral Track Node", "status": "Pending Verification"}
    ]

# 4. Render Layout Sections
# Render Sidebar Component
render_effiong_sidebar()

# Main Header
st.title("🌍 EFFIONG AI")
st.caption("The World's Preeminent Future-Discerning, Truth-Seeking, and Historical Preservation Platform")
st.write("---")

# Render Active Workspace Page
render_segmented_chat()
