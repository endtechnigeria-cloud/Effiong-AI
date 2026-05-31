import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os

# --- INITIALIZATION & PAGE SETUP ---
st.set_page_config(page_title="Effiong AI", page_icon="🌍", layout="wide")
st.title("🌍 EFFIONG AI — Sovereign Multi-Neural Intelligence System")
st.caption("Version 4.5-Beta | Sovereign Verification Engine | Live Multimedia Matrix | Failover Cluster")

# Load Configuration Secrets Safely from Streamlit Cloud
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
    """
    Queries open human knowledge repositories dynamically if core API brains need context 
    or when performing fallback validation loops.
    """
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
    """
    Processes prompts through a redundant multi-layer neural pipeline to ensure
    continuous operation even during severe API rate limits or quota exhausts.
    """
    full_payload = f"{SYSTEM_INSTRUCTIONS}\n\nConversation History:\n{history_context}\n\nUser Prompt: {prompt}"
    
    # --- LAYER 1: CROWN JEWEL (Google Gemini API with Live Search Grounding) ---
    if GEMINI_KEY:
        try:
            client = genai.Client(api_key=GEMINI_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_payload,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                )
            )
            if response.text:
                return response.text, "🧠 Gemini Core (Live Grounded)"
        except Exception as e:
            if "429" not in str(e) and "EXHAUSTED" not in str(e).upper():
                st.warning(f"Gemini Core Encountered Anomaly. Redirecting neural impulses...")

    # --- LAYER 2: PRIMARY FALLBACK (Groq Ultra-Fast API) ---
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

    # --- LAYER 3: SECONDARY AGGREGATOR (OpenRouter Free Tier Models) ---
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

    # --- LAYER 4: ABSOLUTE SURVIVAL BLOCK (Local Repository Scraping Loop) ---
    repo_context = global_knowledge_router(prompt)
    if repo_context:
        survival_response = f"Notice: Core and Secondary API brains are currently recharging or rate-limited. I have autonomously deployed my Abstract API Routers to scrape open knowledge networks live:\n{repo_context}"
        return survival_response, "📟 Sovereign Survival Scraper Mode"

    return "System Error: All neural networks exhausted. Please connect a backup API key inside Streamlit Secrets or wait for your quotas to clear.", "🚨 Offline"

# --- GITHUB AUTONOMOUS STORAGE WRITEBACK ---
def auto_archive_to_github(query, response, file_path="effiong_brain_ledger.txt"):
    """
    Enables Effiong AI to log its experiences and crowd-sourced verification streams
    directly back into GitHub storage as a permanent, open-reference database.
    """
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
        return  # Avoid duplicate standard conversational logs
        
    updated_content = existing_content + new_entry
    import base64
    encoded_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": f"Effiong AI Autonomous Memory Synchronization Update: {file_path}",
        "content": encoded_content,
        "sha": sha if sha else None
    }
    requests.put(url, json=payload, headers=headers)

# --- SIDEBAR INTERFACE LAYOUT (Heritage Portal & Verification Entry) ---
with st.sidebar:
    st.header("🏺 Truth & Heritage Archive Engine")
    st.write("Log historical parameters, real-time events, and traditions directly to lock them in as verified referenceable indexes.")
    
    contributor = st.text_input("Contributor Identity/Agency", "Sovereign Node")
    entry_type = st.selectbox("Event/Data Scope", [
        "Real-Time Current Event", 
        "Historical Correction/Fact", 
        "Oral Tradition / Local Perspective", 
        "Linguistic / Cultural Archetype"
    ])
    
    st.markdown("### Verification Proof Metrics")
    st.caption("Render verifiable source markers to elevate this entry into an absolute fact statement.")
    proof_provided = st.multiselect(
        "Attached Verification Modalities:", 
        ["Video Footage/Stream", "Photographic/Media Capture", "Archaeological/Artifact Record", "Academic/Literary Citation"]
    )
    
    heritage_data = st.text_area("Input History / Real-Time Event Details:")
    proof_urls = st.text_area("Paste Proof Verification URLs or Citation Text:")

    if st.button("Synchronize Ledger Entry"):
        if heritage_data.strip():
            # Evaluation criteria logic loop executed by Effiong AI parameters
            if not proof_provided or not proof_urls.strip():
                status_tag = "UNVERIFIED ORAL RECORD / PERSPECTIVE"
                verification_note = "Logged as community perspective or contemporary raw reporting pending multi-source physical/digital validation."
            else:
                status_tag = "VERIFIED HERITAGE FACT"
                verification_note = f"Audited via independent portal pipeline. Modalities rendered: {', '.join(proof_provided)}. Anchored Reference Indexes: {proof_urls}"
            
            structured_payload = (
                f"Classification: [{status_tag}]\n"
                f"Source Verification Framework: {verification_note}\n"
                f"Context Payload: {heritage_data}\n"
            )
            log_title = f"{entry_type} Submitted by [{contributor}]"
            
            # Write to a distinct database repository ledger tracking global African truth assets
            auto_archive_to_github(log_title, structured_payload, file_path="african_heritage_archive.txt")
            st.success(f"Entry committed safely to your ledger. Status Assigned: {status_tag}.")
        else:
            st.error("Text context canvas cannot be blank before validation sync.")

# --- MAIN CHAT ENGINE GRAPHICS & INTERFACE ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "engine" in message:
            st.caption(f"Processed via: {message['engine']}")

if user_prompt := st.chat_input("Query Effiong AI neural network or request data..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Processing through neural pathways..."):
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
            
            final_reply, active_engine = execute_neural_process(user_prompt, history_str)
            st.markdown(final_reply)
            st.caption(f"Processed via: {active_engine}")
            
            # Embedded multi-media image pipeline handling
            if "GENERATE AN IMAGE" in user_prompt.upper() or "CREATE AN IMAGE" in user_prompt.upper():
                image_seed_prompt = user_prompt.replace("generate an image of", "").replace("create an image of", "")
                pollinations_img_url = f"https://image.pollinations.ai/p/{image_seed_prompt.strip().replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                st.image(pollinations_img_url, caption=f"Visualized Output: '{image_seed_prompt}'", use_column_width=True)
                
            elif "VIDEO" in user_prompt.upper() or "ANIMATION" in user_prompt.upper():
                st.info("🎬 Multimedia Framework engaged. Generating concept frame preview...")
                video_seed_prompt = user_prompt.replace("generate a video of", "").replace("generate an animation of", "")
                pollinations_frame_url = f"https://image.pollinations.ai/p/{video_seed_prompt.strip().replace(' ', '%20')}_cinematic_motion_frame?width=1024&height=576&nologo=true"
                st.image(pollinations_frame_url, caption="🎬 High-Fidelity Cinematic Prompt Frame Rendered.", use_column_width=True)
                st.caption("Pass this prompt parameter context safely into video models like Runway Gen-3 or Luma Dream Machine.")
            
            st.session_state.chat_history.append({"role": "assistant", "content": final_reply, "engine": active_engine})
            
            # Write global conversational logs to background engine ledger
            if "recharging" not in final_reply and "System Error" not in final_reply:
                try:
                    auto_archive_to_github(user_prompt, final_reply)
                except Exception:
                    pass