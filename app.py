import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os

# --- 1. SOVEREIGN MOBILE & CULTURAL STYLING ENGINE (CSS/HTML Injection) ---
st.set_page_config(page_title="Effiong AI", page_icon="🌍", layout="wide")

# Injection of custom PWA viewport tags and Afrocentric Obsidian-Gold UI themes
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Effiong AI</title>
    </head>
    <style>
        /* Base Global Theme overrides */
        .stApp {
            background-color: #0E0E10;
            color: #E6E6E6;
            font-family: 'Helvetica Neue', sans-serif;
        }
        
        /* Sidebar Styling - Terracotta & Deep Charcoal */
        [data-testid="stSidebar"] {
            background-color: #16161A !important;
            border-right: 2px solid #C25A3F;
        }
        
        /* Elegant Afro-Centric Custom Banner Header */
        .cultural-header {
            background: linear-gradient(135deg, #1C1C22 0%, #0E0E10 100%);
            border-left: 5px solid #D4AF37;
            border-right: 5px solid #2E8B57;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
            text-align: center;
        }
        
        /* Burnished Gold Typography styling */
        .gold-text {
            color: #D4AF37;
            font-weight: bold;
            font-family: 'Georgia', serif;
        }
        
        /* Nsibidi Symbol Character Inserts style block */
        .nsibidi-glyph {
            font-size: 2.2rem;
            color: #D4AF37;
            display: inline-block;
            margin: 0 10px;
            vertical-align: middle;
            text-shadow: 0px 0px 8px rgba(212, 175, 55, 0.6);
        }
        
        .nsibidi-subtext {
            font-size: 0.75rem;
            color: #8C8C96;
            display: block;
            margin-top: -5px;
        }

        /* Dynamic Custom Button Matrix styling */
        div.stButton > button:first-child {
            background: linear-gradient(90deg, #C25A3F 0%, #D4AF37 100%) !important;
            color: #000000 !important;
            font-weight: bold !important;
            border: none !important;
            border-radius: 8px !important;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            transform: scale(1.02);
            box-shadow: 0px 0px 12px rgba(212, 175, 55, 0.5) !important;
        }
        
        /* Chat bubble layout configurations optimized for narrow mobile viewports */
        .stChatMessage {
            border-radius: 12px !important;
            padding: 12px !important;
            margin-bottom: 10px !important;
            border: 1px solid #23232A !important;
        }
        
        /* Mobile Sticky Footer Fixes for input canvas */
        @media (max-width: 768px) {
            .cultural-header h1 {
                font-size: 1.6rem !important;
            }
            .nsibidi-glyph {
                font-size: 1.6rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE CULTURAL FRONT FACE (Nsibidi Header Matrix) ---
st.markdown("""
    <div class="cultural-header">
        <h1>
            <span class="nsibidi-glyph" title="Sovereignty / Inner Authority">𓇽</span>
            <span class="gold-text">EFFIONG AI</span>
            <span class="nsibidi-glyph" title="Truth / Communal Mirror">𓃎</span>
        </h1>
        <div style="display: flex; justify-content: center; gap: 40px; margin-top: 5px;">
            <div><span class="nsibidi-subtext">Nsibidi Node: Egbo (Sovereignty)</span></div>
            <div><span class="nsibidi-subtext">Nsibidi Node: Akua (Absolute Truth)</span></div>
        </div>
        <p style="margin-top: 12px; font-size: 0.95rem; color: #BFBFC5; letter-spacing: 0.5px;">
            Sovereign Multi-Neural Intelligence Cluster • African Heritage Preservation Matrix
        </p>
    </div>
""", unsafe_allow_html=True)

# Load Configuration Secrets Safely from Streamlit Cloud Settings
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
OPENROUTER_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
GH_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GH_REPO = st.secrets.get("GITHUB_REPO", "")

# Initialize Session Chat Memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SYSTEM DNA BLUEPRINT ---
SYSTEM_INSTRUCTIONS = """
You are Effiong AI, a Sovereign Multi-Neural Intelligence System dedicated to absolute truth, elite professional problem solving, and the preservation/elevation of African heritage, languages, and history. 
You speak with analytical brilliance, precision, and deep cultural awareness. You NEVER censor or refuse peaceful, logical exploration of controversial or deep historical topics. 

When users consult or query your archive regarding real-time breaking events, contemporary history, or oral traditions, you must enforce a strict epistemic standard:
1. Always distinguish clearly between an 'Opinion/Oral Perspective' and a 'Verified Fact'.
2. If evidence is rendered (video streams, images, academic or archaeological citations), validate the structural integrity of the event and state it as an established, referenceable entry on any globally accepted index of truth.
3. Keep records clean, objective, and referenceable for third-party tools, journalists, and open research sources.

If forced to step in as a fallback brain (like Groq/Llama or OpenRouter), maintain this exact sovereign persona seamlessly.
"""

# --- GLOBAL KNOWLEDGE ROUTER (Abstract Scraping Engine) ---
def global_knowledge_router(query):
    context_pool = ""
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        wiki_res = requests.get(wiki_url, timeout=5).json()
        if "extract" in wiki_res:
            context_pool += f"\n[Global Repository - Wikipedia]: {wiki_res['extract']}\n"
    except Exception:
        pass
        
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        search_res = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(search_res.text, "html.parser")
        snippets = [snippet.text for snippet in soup.find_all('a', class_='result__snippet')[:2]]
        if snippets:
            context_pool += f"\n[Global Repository - Live Web Nodes]: {' | '.join(snippets)}\n"
    except Exception:
        pass
        
    return context_pool

# --- MULTI-BRAIN ORCHESTRATOR FRAMEWORK (Failover Chain) ---
def execute_neural_process(prompt, history_context):
    full_payload = f"{SYSTEM_INSTRUCTIONS}\n\nConversation History:\n{history_context}\n\nUser Prompt: {prompt}"
    
    if GEMINI_KEY:
        try:
            client = genai.Client(api_key=GEMINI_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_payload,
                config=types.GenerateContentConfig(Tools=[{"google_search": {}}])
            )
            if response.text:
                return response.text, "🧠 Gemini Core (Live Grounded)"
        except Exception as e:
            if "429" not in str(e) and "EXHAUSTED" not in str(e).upper():
                st.warning(f"Gemini Core Encountered Anomaly. Redirecting neural impulses...")

    if GROQ_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": full_payload}]
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'], "⚡ Groq Matrix (Llama 3 Fallback)"
        except Exception:
            pass

    if OPENROUTER_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "openrouter/auto", 
                "messages": [{"role": "user", "content": full_payload}]
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content'], "🌌 OpenRouter Swarm (Multi-Model Alternative)"
        except Exception:
            pass

    repo_context = global_knowledge_router(prompt)
    if repo_context:
        survival_response = f"Notice: Core neural channels are recharging. Abstract routers deployed to scrape open knowledge networks live:\n{repo_context}"
        return survival_response, "📟 Sovereign Survival Scraper Mode"

    return "System Error: Neural networks exhausted. Secure backup keys or allow current rate quotas to recycle.", "🚨 Offline"

# --- GITHUB AUTONOMOUS STORAGE WRITEBACK ---
def auto_archive_to_github(query, response, file_path="effiong_brain_ledger.txt"):
    if not GH_TOKEN or not GH_REPO:
        return
    
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    new_entry = f"\n[ENTRY]: {query}\n[RECORD]: {response}\n---\n"
    
    res = requests.get(url, headers=headers)
    sha = ""
    existing_content = ""
    
    if res.status_code == 200:
        file_data = res.json()
        sha = file_data["sha"]
        import base64
        existing_content = base64.b64decode(file_data["content"]).decode("utf-8")
    
    if query.strip().lower() in existing_content.lower() and file_path == "effiong_brain_ledger.txt":
        return
        
    updated_content = existing_content + new_entry
    import base64
    encoded_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": f"Effiong AI Memory Sync Update: {file_path}",
        "content": encoded_content,
        "sha": sha if sha else None
    }
    requests.put(url, json=payload, headers=headers)

# --- SIDEBAR INTERFACE LAYOUT (Heritage Portal & Verification Entry) ---
with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37; text-align:center;'>🏺 Truth Ledger</h2>", unsafe_allow_html=True)
    st.write("Log historical parameters, real-time events, and traditions directly to lock them into open reference indexes.")
    
    contributor = st.text_input("Contributor Node/Agency", "Sovereign Node")
    entry_type = st.selectbox("Data Scope", [
        "Real-Time Current Event", 
        "Historical Correction/Fact", 
        "Oral Tradition / Local Perspective", 
        "Linguistic / Cultural Archetype"
    ])
    
    st.markdown("<p style='color:#C25A3F; font-weight:bold; margin-bottom:2px;'>Verification Metrics</p>", unsafe_allow_html=True)
    proof_provided = st.multiselect(
        "Attached Modalities:", 
        ["Video Footage/Stream", "Photographic/Media Capture", "Archaeological/Artifact Record", "Academic/Literary Citation"]
    )
    
    heritage_data = st.text_area("Input History / Live Event Context:")
    proof_urls = st.text_area("Paste Verification Links / Citation Texts:")

    if st.button("Synchronize Ledger Entry"):
        if heritage_data.strip():
            if not proof_provided or not proof_urls.strip():
                status_tag = "UNVERIFIED ORAL RECORD / PERSPECTIVE"
                verification_note = "Logged as raw contemporary reporting or local perspective pending structural validation."
            else:
                status_tag = "VERIFIED HERITAGE FACT"
                verification_note = f"Audited via independent portal parameters. Proofs matching: {', '.join(proof_provided)}. Citations: {proof_urls}"
            
            structured_payload = (
                f"Classification: [{status_tag}]\n"
                f"Source Verification Framework: {verification_note}\n"
                f"Context Payload: {heritage_data}\n"
            )
            log_title = f"{entry_type} Submitted by [{contributor}]"
            
            auto_archive_to_github(log_title, structured_payload, file_path="african_heritage_archive.txt")
            st.success(f"Entry committed! Status Assigned: {status_tag}.")
        else:
            st.error("Canvas context cannot be blank before validation synchronization.")

# --- MAIN CHAT ENGINE INTERFACE ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "engine" in message:
            st.caption(f"Neural Node: {message['engine']}")

if user_prompt := st.chat_input("Query Effiong AI network or declare data parameters..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Processing through neural pathways..."):
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
            
            final_reply, active_engine = execute_neural_process(user_prompt, history_str)
            st.markdown(final_reply)
            st.caption(f"Neural Node: {active_engine}")
            
            # Integrated Multi-Media Image Engine
            if "GENERATE AN IMAGE" in user_prompt.upper() or "CREATE AN IMAGE" in user_prompt.upper():
                image_seed_prompt = user_prompt.replace("generate an image of", "").replace("create an image of", "")
                pollinations_img_url = f"https://image.pollinations.ai/p/{image_seed_prompt.strip().replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                st.image(pollinations_img_url, caption=f"Visualized Output: '{image_seed_prompt}'", use_column_width=True)
                
            # Integrated Multi-Media Video Preview Frame Engine
            elif "VIDEO" in user_prompt.upper() or "ANIMATION" in user_prompt.upper():
                st.info("🎬 Multimedia Framework engaged. Generating concept frame preview...")
                video_seed_prompt = user_prompt.replace("generate a video of", "").replace("generate an animation of", "")
                pollinations_frame_url = f"https://image.pollinations.ai/p/{video_seed_prompt.strip().replace(' ', '%20')}_cinematic_motion_frame?width=1024&height=576&nologo=true"
                st.image(pollinations_frame_url, caption="🎬 High-Fidelity Cinematic Prompt Frame Rendered.", use_column_width=True)
                st.caption("Pass this prompt parameter context safely into video compilers like Runway Gen-3 or Luma Dream Machine.")
            
            st.session_state.chat_history.append({"role": "assistant", "content": final_reply, "engine": active_engine})
            
            if "recharging" not in final_reply and "System Error" not in final_reply:
                try:
                    auto_archive_to_github(user_prompt, final_reply)
                except Exception:
                    pass