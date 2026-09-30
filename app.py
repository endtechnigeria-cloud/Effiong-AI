
import os
import sys
import warnings
import json
import time
import re
import requests
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# --- WINDOWS SELECTOR EVENT LOOP & WARNING FIX ---
if sys.platform == 'win32':
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    os.environ["PYTHONWARNINGS"] = "ignore"
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Append root directory and src directory to Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
SERVICES_DIR = os.path.join(SRC_DIR, "services")

for directory in [ROOT_DIR, SRC_DIR, SERVICES_DIR]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

# --- Bring Streamlit secrets into os.environ once, so every module (even non-Streamlit-aware
#     ones used by main.py/tests) can read provider keys the same way. Never raises.
try:
    from src import config as _config
    _config.load_secrets_into_env()
    from src.services.agent_scheduler import start_background_learning
    start_background_learning()
except Exception as _startup_exc:  # startup wiring must never block the page from loading
    print(f"[Effiong AI] startup wiring warning: {_startup_exc}")

try:
    from src.services.brain_router import (
        execute_sovereign_intelligence_cycle,
        compile_pdf_bytes,
        compile_word_bytes
    )
except ModuleNotFoundError:
    try:
        from services.brain_router import (
            execute_sovereign_intelligence_cycle,
            compile_pdf_bytes,
            compile_word_bytes
        )
    except ModuleNotFoundError:
        from brain_router import (
            execute_sovereign_intelligence_cycle,
            compile_pdf_bytes,
            compile_word_bytes
        )

# --- PERSISTENT CHAT STORAGE UTILITY (SAFE ATOMIC WRITE) ---
HISTORY_FILE = Path("chat_history.json")

def load_chat_history():
    """Loads past conversation history from local storage."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []
    return []

def save_chat_history(messages):
    """Saves current conversation state to local storage safely using atomic write."""
    try:
        temp_file = Path("chat_history.json.tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        temp_file.replace(HISTORY_FILE)
    except OSError as e:
        print(f"Permission or OS error saving chat history: {e}")
    except Exception as e:
        print(f"Unexpected error saving chat history: {e}")

st.set_page_config(
    page_title="EFFIONG AI - Sovereign Wisdom Engine",
    page_icon="🐆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Direct multi-level DOM Listener Bridge
components.html("""
<script>
(function() {
    const pWin = window.parent || window;
    const pDoc = pWin.document;

    if (pWin.__effiongSidebarGestureInitialized) return;
    pWin.__effiongSidebarGestureInitialized = true;

    function closeSidebar() {
        const sidebar = pDoc.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;

        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
        if (!isExpanded) return;

        const collapseBtn = pDoc.querySelector('button[data-testid="stSidebarCollapseButton"]') ||
                         sidebar.querySelector('button[aria-label*="Close" i]') ||
                         sidebar.querySelector('button[aria-label*="Collapse" i]');
        if (collapseBtn) collapseBtn.click();
    }

    // Attach capture-phase click & pointer handlers across window AND document
    ['click', 'pointerdown', 'mousedown'].forEach(eventType => {
        pDoc.addEventListener(eventType, function(e) {
            const sidebar = pDoc.querySelector('section[data-testid="stSidebar"]');
            if (!sidebar || sidebar.getAttribute('aria-expanded') !== 'true') return;

            const collapseBtn = pDoc.querySelector('button[data-testid="stSidebarCollapseButton"]');

            // Check if click originated outside sidebar element
            if (!sidebar.contains(e.target) && (!collapseBtn || !collapseBtn.contains(e.target))) {
                closeSidebar();
            }
        }, true);
    });

    // Mobile Swipe Fallback
    let startX = 0, startY = 0;
    pDoc.addEventListener('touchstart', e => {
        if (e.touches && e.touches.length > 0) {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }
    }, { passive: true });

    pDoc.addEventListener('touchend', e => {
        if (!e.changedTouches || e.changedTouches.length === 0) return;
        const deltaX = startX - e.changedTouches[0].clientX;
        const deltaY = Math.abs(startY - e.changedTouches[0].clientY);
        if (deltaX > 50 && deltaY < 100) {
            closeSidebar();
        }
    }, { passive: true });
})();
</script>
""", height=0, width=0)

# Dark Luxury Tech Visual Styling Layer & Fixed Responsive Layout Controls
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600&family=Comfortaa:wght=700&display=swap');

    .stApp {
        background-color: #0B0F17;
        color: #F0F6FC;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #121620 !important;
        border-right: 1px solid #212631;
    }
    header[data-testid="stHeader"] {
        background-color: #0B0F17 !important;
    }
    footer { display: none !important; }
    
    .brand-container {
        text-align: center;
        margin-top: 2vh;
        margin-bottom: 3vh;
        width: 100%;
    }
    .brand-title {
        font-family: 'Comfortaa', cursive;
        font-size: 2.8rem;
        background: linear-gradient(135deg, #FFFFFF 40%, #D27D2D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 auto 5px auto;
        display: inline-block;
    }
    .brand-subtitle {
        font-size: 1.05rem;
        color: #8B949E;
        max-width: 750px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* NOTE: an app-wide "never wrap, never stack" rule used to live here. It forced EVERY
       st.columns() layout in the app (sidebar Heritage/History tabs, PDF/Word download buttons,
       report/archive buttons, etc.) into a single non-shrinking row, which is exactly what breaks
       "doesn't fit on a minimized screen": those rows had nowhere to go but overflow. Streamlit's
       own columns already stack vertically below its built-in breakpoint, so we removed the
       app-wide override and instead scope the "stay in one row" behavior to just the chat bottom
       bar below, where a single row is actually what we want. */

    /* Fix sticky position for bottom bar container containing chat input and icon buttons */
    div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) {
        position: fixed !important;
        bottom: 0px !important;
        left: 0px !important;
        right: 0px !important;
        background-color: #0B0F17 !important;
        padding: 0.0rem 2rem 1.2rem 2rem !important;
        z-index: 9999 !important;
        border-top: 1px solid #212631 !important;
    }

    /* Force button columns to stay inline on horizontal flex layout */
    div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-end !important;
        gap: 0.4rem !important;
    }

    /* Let every column in the bottom bar shrink below its content size if it has to... */
    div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        min-width: 0 !important;
    }
    /* ...but pin the attach / dictate / voice icon columns (1st, 3rd, 4th) to a fixed small width... */
    div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(1),
    div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(3),
    div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(4) {
        flex: 0 0 auto !important;
        width: 44px !important;
    }
    /* ...and let the chat-input column (2nd) absorb whatever width is left over */
    div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) {
        flex: 1 1 auto !important;
        width: auto !important;
    }

    /* Target dictate and voice buttons specifically to style their active state and size */
    .st-key-btn_dictate button, .st-key-btn_voice button {
        height: 48px !important;
        margin-bottom: 2px !important;
        border: 1px solid #212631 !important;
        background-color: #161B24 !important;
    }

    /* Add bottom padding to chat scroll area to prevent text cutoff under fixed bar */
    .main .block-container {
        padding-bottom: 110px !important;
    }

    /* Enable desktop click-outside backdrop target */
.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) [data-testid="stMain"],
.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) .main {
    cursor: pointer !important;
}

/* Universal Visual Backdrop overlay for open sidebar */
.stApp:has(section[data-testid="stSidebar"][aria-expanded="true"])::before {
    content: "" !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    background: rgba(0, 0, 0, 0.35) !important;
    backdrop-filter: blur(2px) !important;
    -webkit-backdrop-filter: blur(2px) !important;
    z-index: 9998 !important;
    pointer-events: none !important;
}

    /* Keep Streamlit's own sidebar show/hide control (the "hamburger" arrow that appears once the
       sidebar is collapsed) visible and clickable above our dark theme and fixed-position overlays.
       Different Streamlit versions use slightly different test ids for this button, so we cover both. */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 1000000 !important;
        opacity: 1 !important;
        visibility: visible !important;
        background-color: #121620 !important;
        border: 1px solid #212631 !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
    }
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] svg {
        fill: #F0F6FC !important;
        color: #F0F6FC !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] svg,
    header[data-testid="stHeader"] svg {
        fill: #F0F6FC !important;
        color: #F0F6FC !important;
    }

    @media (max-width: 768px) {
        .brand-title {
            font-size: 2rem !important;
        }
        .brand-subtitle {
            font-size: 0.85rem !important;
        }

        /* Bottom bar needs tighter padding on narrow screens or the icon buttons get pushed
           past the edge of the viewport */
        div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) {
            padding: 0.0rem 0.6rem 0.9rem 0.6rem !important;
        }
        div[data-testid="stVerticalBlock"] > div:has(div.effiong-bottom-bar-anchor) div[data-testid="stHorizontalBlock"] {
            gap: 0.3rem !important;
        }

        /* Elevate Sidebar as a floating drawer on mobile */
        section[data-testid="stSidebar"][aria-expanded="true"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            width: 85vw !important;
            max-width: 320px !important;
            z-index: 99999 !important;
            box-shadow: 10px 0px 30px rgba(0, 0, 0, 0.8) !important;
            transition: all 0.3s ease-in-out !important;
        }

        /* Floating Close Button */
        section[data-testid="stSidebar"][aria-expanded="true"] button[data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"][aria-expanded="true"] button[aria-label*="Close" i],
        section[data-testid="stSidebar"][aria-expanded="true"] button[aria-label*="Collapse" i] {
            position: fixed !important;
            top: 10px !important;
            right: 15px !important;
            z-index: 100000 !important;
            background-color: #212631 !important;
            border-radius: 50% !important;
            width: 40px !important;
            height: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        .main .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

try:
    from src.components.sidebar import render_effiong_sidebar
    from src.components.chat_ui import render_segmented_chat
except ModuleNotFoundError:
    try:
        from components.sidebar import render_effiong_sidebar
        from components.chat_ui import render_segmented_chat
    except ModuleNotFoundError:
        render_effiong_sidebar = None
        render_segmented_chat = None

# Active state vectors
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

if "master_messages" not in st.session_state:
    st.session_state.master_messages = []

if st.session_state.current_view == "history":
    st.session_state.master_messages = load_chat_history()

if "last_generated_image" not in st.session_state:
    st.session_state.last_generated_image = None
if "last_image_prompt" not in st.session_state:
    st.session_state.last_image_prompt = None

if "dictated_draft" not in st.session_state:
    st.session_state.dictated_draft = ""

# Track processed audio ID to prevent infinite reruns
if "last_processed_audio_id" not in st.session_state:
    st.session_state.last_processed_audio_id = None

if render_effiong_sidebar:
    render_effiong_sidebar()

if st.session_state.current_view in ["chat", "history"]:
    
    st.markdown("""
    <div class="brand-container">
        <div class="brand-title">🐆Effiong AI</div>
        <div class="brand-subtitle">The World's Preeminent Future-Discerning, Truth-Seeking, and Historical Preservation Platform</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Render segmented chat interface containing native chat input, dictate, and voice triggers
    if render_segmented_chat:
        render_segmented_chat()
    else:
        st.error("Unable to load chat UI component (`src/components/chat_ui.py`). Check module routes.")
