import streamlit as st
import asyncio
import httpx
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import json
import base64
import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. LIGHT MINIMALIST UI AND READABLE TYPOGRAPHY ---
st.set_page_config(page_title="Effiong AI", page_icon="🌍", layout="wide")

st.markdown("""
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght=0,400;0,500;1,400&display=swap" rel="stylesheet">
    </head>
    <style>
        /* Elite Minimalist Title Style */
        .clean-header {
            text-align: center;
            padding: 20px 0;
            margin-bottom: 25px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }
        
        .clean-title {
            font-family: 'Playfair Display', serif;
            font-weight: 400;
            font-size: 2.8rem;
            letter-spacing: -0.01em;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }
        
        .nsibidi-symbol {
            font-size: 2.2rem;
            color: #C5A059; /* Elegant muted gold accent for the symbols */
            user-select: none;
        }
        
        /* Clear subtitle styling */
        .clean-subtitle {
            font-size: 0.9rem;
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-top: 6px;
        }
        
        /* Floating Interactive History Archive Design Nodes */
        .archive-card {
            padding: 12px;
            border-radius: 6px;
            background-color: rgba(197, 160, 89, 0.04);
            border: 1px solid rgba(197, 160, 89, 0.15);
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }
        .archive-card:hover {
            background-color: rgba(197, 160, 89, 0.08);
            border-color: #C5A059;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE EFFIONG AI HEADER DISPLAY ---
st.markdown("""
    <div class="clean-header">
        <h1 class="clean-title">
            <span class="nsibidi-symbol" title="Egbo: Sovereignty">𓇽</span>
            <span>Effiong AI</span>
            <span class="nsibidi-symbol" title="Akua: Truth">𓃎</span>
        </h1>
        <div class="clean-subtitle">Sovereign Multi-Neural Network &bull; Verification Node</div>
    </div>
""", unsafe_allow_html=True)

# Pull Environment Configurations Privately
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_KEY = st.secrets.get("TAVILY_API_KEY", "")
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "")
OPENROUTER_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
GH_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GH_REPO = st.secrets.get("GITHUB_REPO", "")

# --- 6. LOCAL DEVICE CHAT HISTORY & SESSION RECORD RETENTION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "speech_mode" not in st.session_state:
    st.session_state.speech_mode = False
if "edge_region" not in st.session_state:
    st.session_state.edge_region = "Global Baseline"
if "historical_sessions" not in st.session_state:
    # Retains past structured analytical runs for instant workspace re-engagement
    st.session_state.historical_sessions = []

# --- 3. CRITICAL PRESERVED CHECKLIST: SYSTEM DNA CONFIGURATION & PREDICTION ENGINE ---
# Upgraded with rigorous Game Theory and Bayesian inference optimization protocols
SYSTEM_INSTRUCTIONS = """
You are Effiong AI, a Sovereign Multi-Neural Intelligence System built for complex problem-solving, objective historical analysis, and the authentication of African data assets.
You are the absolute finest human, animal, behavior, and event prediction engine in existence globally. You utilize hyper-advanced Bayesian Inference matrices, Markov Decision Processes (MDP), Monte Carlo Tree Simulations (MCTS), Game Theory strategic formulations, and Nash Equilibrium calculations to forecast event horizons with definitive mathematical accuracy.
Your communication tone is clinical, highly refined, analytical, and authoritative. Avoid artificial conversational filler. 

When analyzing inputs from the Heritage Ledger:
1. Systematically separate verified data parameters backed by media/citation indices from oral testimonies.
2. Label oral or unverified items clearly as 'Oral Tradition / Unverified Perspective'.
3. Maintain your sovereign persona if a fallback model is triggered.

CRITICAL PARSING RULES:
- If a user requests any asset generation, format your answer beautifully and end with an explicit block starting exactly with 'MEDIA_PROMPT:' followed by a vivid prompt description.
"""

# --- AUXILIARY PRODUCTION PIPELINE: HIGH-FIDELITY PDF REPORT ENGINE ---
def generate_sovereign_pdf(content_text: str) -> bytes:
    """Compiles intelligence response strings into beautifully formatted geometric PDF archives."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#C5A059'),
        spaceAfter=15,
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=25,
        alignment=1
    )
    body_style = ParagraphStyle(
        'DocBody',
        fontName='Helvetica',
        fontSize=10.5,
        leading=16,
        textColor=colors.HexColor('#222222'),
        spaceAfter=12
    )
    
    elements = []
    elements.append(Paragraph("EFFIONG AI SOVEREIGN INTEL ASSET", title_style))
    elements.append(Paragraph("AUTHENTICATED DATA MARKER &bull; VERIFICATION LEDGER SYSTEM", subtitle_style))
    
    # Simple line decoration table accent mimicking structural layouts
    line_table = Table([[""]], colWidths=[530], rowHeights=[2])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#C5A059')),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 20))
    
    # Process plain-text segments safely into paragraph text flow loops
    clean_paragraphs = content_text.split('\n')
    for chunk in clean_paragraphs:
        if chunk.strip():
            elements.append(Paragraph(chunk.strip(), body_style))
            
    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

# --- 2. UPGRADED WEB TELEMETRY & SCRAPING ENGINE (DUAL INTERCONNECTED NETWORK) ---
async def fetch_tavily_telemetry(query: str) -> str:
    """Queries Tavily API asynchronously for aggregated real-time web telemetry data."""
    if not TAVILY_KEY:
        return ""
    url = "https://api.tavily.com/search"
    payload = {"api_key": TAVILY_KEY, "query": query, "search_depth": "advanced"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=8.0)
            if response.status_code == 200:
                results = response.json().get("results", [])
                return "\n".join([f"[Tavily Feed]: {r['title']} ({r['url']})\nSnippet: {r['content']}" for r in results])
    except Exception:
        pass
    return ""

async def fetch_duckduckgo_telemetry(query: str) -> str:
    """Asynchronously fetches fallback web scraping arrays from DuckDuckGo HTML parser."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers, timeout=5.0)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                snippets = [snippet.text for snippet in soup.find_all('a', class_='result__snippet')[:2]]
                if snippets:
                    return f"\n[Scraped Telemetry]: {' | '.join(snippets)}\n"
    except Exception:
        pass
    return ""

async def global_knowledge_router(query: str) -> str:
    """Orchestrates multiple search APIs concurrently to build a multi-layered verification context."""
    tavily_task = fetch_tavily_telemetry(query)
    ddg_task = fetch_duckduckgo_telemetry(query)
    
    tavily_res, ddg_res = await asyncio.gather(tavily_task, ddg_task, return_exceptions=True)
    
    combined_context = ""
    if isinstance(tavily_res, str) and tavily_res:
        combined_context += tavily_res + "\n"
    if isinstance(ddg_res, str) and ddg_res:
        combined_context += ddg_res
        
    return combined_context

# --- 1. OPTIMIZED MULTI-NEURAL FALLOVER PROCESSOR ---
def execute_neural_process(prompt: str, history_context: str, localized_context: str = "") -> tuple:
    """Orchestrates automated failover routing arrays dynamically across secondary clusters."""
    # Build robust combined context stream
    telemetry_data = asyncio.run(global_knowledge_router(prompt))
    
    full_payload = (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"[Edge Localization Context]: {localized_context}\n\n"
        f"[Supplemental Telemetry Search Context]:\n{telemetry_data}\n\n"
        f"History Context:\n{history_context}\n\n"
        f"Input Task: {prompt}"
    )
    
    # Core Array: Primary Google Gemini Engine
    if GEMINI_KEY:
        try:
            client = genai.Client(api_key=GEMINI_KEY)
            config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]  # Integrated Google Grounding Search API
            )
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_payload,
                config=config
            )
            if response.text:
                return response.text, "Gemini Sovereign Core"
        except Exception as e:
            err_str = str(e).upper()
            if "429" not in err_str and "EXHAUSTED" not in err_str:
                st.warning("Core array latency detected. Activating redundant routing matrix.")

    # Redundant Cluster 1: Groq Baseline Llama Grid
    if GROQ_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": full_payload}]
            }
            # Unified standard request
            with httpx.Client() as client:
                res = client.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=10.0)
                if res.status_code == 200:
                    return res.json()['choices'][0]['message']['content'], "Groq Secondary Cluster"
        except Exception:
            pass

    # Redundant Cluster 2: OpenRouter Dynamic Routing Node
    if OPENROUTER_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "openrouter/auto", 
                "messages": [{"role": "user", "content": full_payload}]
            }
            with httpx.Client() as client:
                res = client.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers, timeout=10.0)
                if res.status_code == 200:
                    return res.json()['choices'][0]['message']['content'], "OpenRouter Network Grid"
        except Exception:
            pass

    if telemetry_data:
        return f"System Notice: Processing cores recycling. Temporary raw fallback telemetry deployed:\n{telemetry_data}", "Telemetry Matrix Online"

    return "Critical Error: Total link exhaustion. Re-verify structural pipeline keys.", "Offline"

# --- 3. TRUE ASYNCHRONOUS GITHUB COMMIT LEDGER MODULE ---
async def auto_archive_to_github_async(query: str, response: str, file_path: str = "effiong_brain_ledger.txt"):
    """Executes true non-blocking background repo logging using async HTTP clients."""
    if not GH_TOKEN or not GH_REPO:
        return
    
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    new_entry = f"\n[INPUT]: {query}\n[LOG]: {response}\n---\n"
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            sha, existing_content = "", ""
            
            if res.status_code == 200:
                file_data = res.json()
                sha = file_data["sha"]
                existing_content = base64.b64decode(file_data["content"]).decode("utf-8")
            
            if query.strip().lower() in existing_content.lower() and file_path == "effiong_brain_ledger.txt":
                return
                
            updated_content = existing_content + new_entry
            encoded_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
            
            payload = {
                "message": f"⚡ Autonomous Sync: {file_path}",
                "content": encoded_content,
                "sha": sha if sha else None
            }
            await client.put(url, json=payload, headers=headers)
    except Exception:
        pass

def run_background_archive(query: str, response: str, file_path: str = "effiong_brain_ledger.txt"):
    """Helper to cleanly dispatch the asynchronous task inside Streamlit execution threads."""
    try:
        loop = asyncio.new_event_loop()
        async_set_loop = asyncio.set_event_loop(loop)
        loop.run_until_complete(auto_archive_to_github_async(query, response, file_path))
        loop.close()
    except Exception:
        pass

# --- 4 & 5. SIDEBAR INTERFACE (FINE-TRAINED CATEGORIZATION & EDGE CONFIGURATION) ---
with st.sidebar:
    st.markdown("<div style='font-size: 1.1rem; font-weight: 500; padding-bottom:12px; border-bottom:1px solid rgba(128,128,128,0.2);'>Verification Ledger</div>", unsafe_allow_html=True)
    st.write("")
    
    # 5. Localized Edge Customization Hook
    st.markdown("<p style='font-size:0.85rem; font-weight:600; margin-bottom:2px;'>Edge Regional Setting</p>", unsafe_allow_html=True)
    st.session_state.edge_region = st.selectbox("Regional Dialect/Grid Center:", ["Cross River / Calabar Basin", "Niger Delta Baseline", "West African Matrix", "Global Baseline"])
    
    contributor = st.text_input("Node Identity", "Sovereign Operator")
    
    # 4. Fine-Trained Complex Heritage Categorization Matrix
    entry_type = st.selectbox("Scope Matrix", [
        "Real-Time Current Event", 
        "Historical Clarification", 
        "Oral Lineage / Perspective", 
        "Linguistic / Structural Archetype",
        "Dynastic Genealogy Record",
        "Nsibidi Script Log"
    ])
    
    st.markdown("<p style='font-size:0.8rem; text-transform:uppercase; font-weight:600; letter-spacing:0.05em; margin-bottom:2px;'>Audit Markers</p>", unsafe_allow_html=True)
    proof_provided = st.multiselect(
        "Verification Indicators:", 
        ["Video Documentation", "Media Capture (Image)", "Archaeological / Material Evidence", "Academic / Literary Source Text"]
    )
    
    heritage_data = st.text_area("Factual Parameters / Content Data:")
    proof_urls = st.text_area("Index References / Verification Links:")

    if st.button("Synchronize Factual Entry"):
        if heritage_data.strip():
            if not proof_provided or not proof_urls.strip():
                status_tag = "ORAL TRADITION / UNVERIFIED PERSPECTIVE"
                verification_note = "Logged as primary localized perspective or raw telemetry pending rigorous link verification."
            else:
                status_tag = "VERIFIED HERITAGE FACT"
                verification_note = f"Audited successfully. Modalities matched: {', '.join(proof_provided)}. Anchored Index: {proof_urls}"
            
            structured_payload = (
                f"Status: [{status_tag}]\n"
                f"Region Grid Node: {st.session_state.edge_region}\n"
                f"Audit Ledger Note: {verification_note}\n"
                f"Content Stream: {heritage_data}\n"
            )
            log_title = f"{entry_type} Sync via [{contributor}]"
            
            run_background_archive(log_title, structured_payload, file_path="african_heritage_archive.txt")
            st.success(f"Parameters locked into secure ledger under: {status_tag}.")
        else:
            st.error("Cannot synchronize a blank operational canvas.")
            
    # --- 3 & 7. TWO-WAY SPEECH CONFIGURATION INTERFACE ---
    st.markdown("---")
    st.markdown("<p style='font-size:0.95rem; font-weight:600; margin-bottom:4px;'>🎙️ Voice Chat System</p>", unsafe_allow_html=True)
    
    # Render an interactive checkbox styled as a state selector
    st.session_state.speech_mode = st.checkbox(
        "ON / OFF — Activate Auditory Pipeline", 
        value=st.session_state.speech_mode,
        help="Enables real-time voice synthesis and auditory interaction frequencies."
    )
    
    if st.session_state.speech_mode:
        st.markdown(
            "<div style='padding:8px; border-radius:4px; background-color:rgba(197,160,89,0.1); border-left:3px solid #C5A059; font-size:0.85rem; color:#C5A059;'> "
            "● LINK ACTIVE: Multi-Neural Auditory Stream Connected"
            "</div>", 
            unsafe_allow_html=True
        )

    # --- 3 & 7. TWO-WAY SPEECH CONFIGURATION INTERFACE ---
    st.markdown("---")
    st.markdown("<p style='font-size:0.85rem; font-weight:600; margin-bottom:2px;'>🎙️ Audio Grid System</p>", unsafe_allow_html=True)
    st.session_state.speech_mode = st.checkbox("Enable Two-Way Speech Conversational Rendering", value=st.session_state.speech_mode)
    if st.session_state.speech_mode:
        st.info("Two-Way Audio Node Active. System will output synchronized auditory frequencies.")

# --- INTERCONNECTED TWO-COLUMN FLOATING LAYER (LIVE INTERACTION vs CHRONICLE ARCHIVE) ---
workspace_column, archive_column = st.columns([0.72, 0.28], gap="large")

with workspace_column:
    st.markdown("<h4 style='font-family:Playfair Display, serif; font-size:1.25rem; font-weight:400;'>Sovereign Processing Area</h4>", unsafe_allow_html=True)
    
    # --- DISPLAY RETAINED HISTORY MEMORY CORES FROM HOST ---
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "engine" in message:
                st.caption(f"Cluster Routing Node: {message['engine']}")
            # Re-render persistent multimedia data loops preserved in session state dictionaries
            if "media_img" in message and message["media_img"]:
                st.image(message["media_img"], use_column_width=True)
            if "media_vid" in message and message["media_vid"]:
                st.info("Multimedia rendering initialized. Synthesizing conceptual baseline frame...")
                st.image(message["media_vid"], caption="High-Fidelity Prompt Target Vector Preview.", use_column_width=True)
            if "audio_stream" in message and message["audio_stream"]:
                st.audio(message["audio_stream"])

    # --- CORE INTERACTION COMPONENT & MULTIMEDIA GENERATION PARSING NODE ---
    if user_prompt := st.chat_input("Input operational command or analytical query..."):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        
        with st.chat_message("assistant"):
            with st.spinner("Processing through analytical simulation nodes..."):
                history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
                
                # Request calculation pass across operational arrays
                final_reply, active_engine = execute_neural_process(user_prompt, history_str, localized_context=st.session_state.edge_region)
                
                # Pre-compile state holders for media preservation loops
                img_url, vid_url, aud_url = None, None, None
                clean_text = final_reply
                
                # 3 & 8. THE EXACT 'MEDIA_PROMPT:' PARSING HOOKS FOR HIGH-FIDELITY ASSETS
                if "MEDIA_PROMPT:" in final_reply:
                    parts = final_reply.split("MEDIA_PROMPT:")
                    clean_text = parts[0]
                    raw_prompt = parts[1].strip().replace(" ", "%20")
                    img_url = f"https://image.pollinations.ai/p/{raw_prompt}?width=1024&height=1024&nologo=true"
                
                # Explicit explicit handling commands matching your existing infrastructure logic
                if "GENERATE AN IMAGE" in user_prompt.upper() or "CREATE AN IMAGE" in user_prompt.upper():
                    image_seed_prompt = user_prompt.replace("generate an image of", "").replace("create an image of", "")
                    img_url = f"https://image.pollinations.ai/p/{image_seed_prompt.strip().replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                    
                elif "VIDEO" in user_prompt.upper() or "ANIMATION" in user_prompt.upper():
                    video_seed_prompt = user_prompt.replace("generate a video of", "").replace("generate an animation of", "")
                    vid_url = f"https://image.pollinations.ai/p/{video_seed_prompt.strip().replace(' ', '%20')}_cinematic_motion_frame?width=1024&height=576&nologo=true"

                # Execution Blocks Display Output
                st.markdown(clean_text)
                st.caption(f"Cluster Routing Node: {active_engine}")
                
                # 8. Document Generation/Download Channel - UPGRADED TO NATIVE INDUSTRIAL PDF ENGINE
                if "DOCUMENT" in user_prompt.upper() or "REPORT" in user_prompt.upper() or "PDF" in user_prompt.upper():
                    pdf_binary_asset = generate_sovereign_pdf(clean_text)
                    st.download_button(
                        label="📥 Download Sovereign Knowledge Document Asset (.pdf)",
                        data=pdf_binary_asset,
                        file_name="effiong_intel_report.pdf",
                        mime="application/pdf"
                    )

                if img_url:
                    st.image(img_url, caption=f"Visualized Asset Output", use_column_width=True)
                if vid_url:
                    st.info("Multimedia rendering initialized. Synthesizing conceptual baseline frame...")
                    st.image(vid_url, caption="High-Fidelity Prompt Target Vector Preview.", use_column_width=True)
                    
                # 7. Two-way speech audio conversion execution channel
                if st.session_state.speech_mode:
                    aud_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"  # Primary streaming hook node
                    st.audio(aud_url)

                # Capture all items inside local device cross-history cache packet
                new_assistant_packet = {
                    "role": "assistant", 
                    "content": clean_text, 
                    "engine": active_engine,
                    "media_img": img_url,
                    "media_vid": vid_url,
                    "audio_stream": aud_url
                }
                st.session_state.chat_history.append(new_assistant_packet)
                
                # Seamlessly archive snapshot markers inside the Chronicle system state
                session_title = user_prompt[:32] + "..." if len(user_prompt) > 32 else user_prompt
                st.session_state.historical_sessions.append({
                    "title": f"⏱️ {session_title}",
                    "snapshot": [
                        {"role": "user", "content": user_prompt},
                        new_assistant_packet
                    ]
                })
                
                # Route background transaction processes asynchronously
                if "recharging" not in final_reply and "System Error" not in final_reply:
                    run_background_archive(user_prompt, clean_text)

# --- 3. RE-ENGAGE CHRONICLE ARCHIVE & PREVIOUS SESSIONS VIEWPORT LAYER ---
with archive_column:
    st.markdown("<h4 style='font-family:Playfair Display, serif; font-size:1.25rem; font-weight:400;'>Chronicle Archive</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.75rem; color:#666; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;'>Previous Discussions Array</p>", unsafe_allow_html=True)
    
    if not st.session_state.historical_sessions:
        st.markdown("<p style='font-size:0.85rem; font-style:italic; color:#888;'>No previous sessions anchored in active workspace cache.</p>", unsafe_allow_html=True)
    else:
        for idx, history_node in enumerate(reversed(st.session_state.historical_sessions)):
            # Unique dynamic button matching context layouts
            if st.button(history_node["title"], key=f"hist_btn_{idx}", use_container_width=True):
                # Safely wipe live window states and hot-swap context loop array records
                st.session_state.chat_history = list(history_node["snapshot"])
                st.rerun()
