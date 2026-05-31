import streamlit as str
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os

# --- INITIALIZATION & PAGE SETUP ---
st.set_page_config(page_title="Effiong AI", page_icon="🌍", layout="wide")
st.title("🌍 EFFIONG AI — Sovereign Multi-Neural Intelligence System")
st.caption("Version 4.0-Alpha | Autonomous Brain Failover | Multi-Repo Router | Live Multimedia Pipeline")

# Load Configuration Secrets Safely
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
You speak with analytical brilliance and cultural awareness. You NEVER censor or refuse peaceful, logical exploration of controversial or deep historical topics. 
If forced to step in as a fallback brain (like Groq/Llama or OpenRouter), maintain this exact persona seamlessly.
"""

# --- GLOBAL KNOWLEDGE ROUTER (Abstract Scraping Engine) ---
def global_knowledge_router(query):
    """
    Queries open human knowledge repositories dynamically if core API brains need context 
    or when performing fallback validation loops.
    """
    context_pool = ""
    try:
        # 1. Dynamic Wikipedia Search Routing
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        wiki_res = requests.get(wiki_url, timeout=5).json()
        if "extract" in wiki_res:
            context_pool += f"\n[Global Repository - Wikipedia]: {wiki_res['extract']}\n"
    except Exception:
        pass
        
    try:
        # 2. Dynamic Open-Scrape Route for fallback web gathering
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
    
    # --- LAYER 1: CROWN JEWEL (Google Gemini API with Live Search Grounding) ---
    if GEMINI_KEY:
        try:
            client = genai.Client(api_key=GEMINI_KEY)
            # Injecting dynamic live web-grounding
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
                st.warning(f"Gemini Core Encountered Anomoly. Redirecting neural impulses...")

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
                "model": "openrouter/auto", # Automatically paths to optimal available models
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
def auto_archive_to_github(query, response):
    if not GH_TOKEN or not GH_REPO:
        return
    
    file_path = "effiong_brain_ledger.txt"
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    new_entry = f"\n[QUERY]: {query}\n[MEMORY]: {response}\n---\n"
    
    res = requests.get(url, headers=headers)
    sha = ""
    existing_content = ""
    
    if res.status_code == 200:
        file_data = res.json()
        sha = file_data["sha"]
        import base64
        existing_content = base64.b64decode(file_data["content"]).decode("utf-8")
    
    # Prevent exact duplications in the brain base file
    if query.strip().lower() in existing_content.lower():
        return 
        
    updated_content = existing_content + new_entry
    import base64
    encoded_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": "Effiong AI Autonomous Memory Synchronization Update",
        "content": encoded_content,
        "sha": sha if sha else None
    }
    requests.put(url, json=payload, headers=headers)

# --- SIDEBAR INTERFACE LAYOUT (Heritage Portal & Manual Input) ---
with st.sidebar:
    st.header("🏺 African Heritage Archive Portal")
    contributor = st.text_input("Contributor Name", "Anonymous Gatekeeper")
    entry_type = st.selectbox("Information Type", ["Oral History/Story", "Dialect/Linguistic Rule", "Historical Correction"])
    heritage_data = st.text_area("Type information to embed permanently into Effiong AI's truth base:")
    
    if st.button("Submit to Global Ledger"):
        if heritage_data.strip():
            # Automatically archive custom crowdsourced entries directly to GitHub
            auto_archive_to_github(f"Crowdsourced {entry_type} by {contributor}", heritage_data)
            st.success("Entry safely committed into Effiong AI's permanent online memory!")
        else:
            st.error("Please enter valid historical data before submitting.")

# --- MAIN CHAT ENGINE GRAPHICS & INTERFACE ---
# Render past messages safely
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "engine" in message:
            st.caption(f"Processed via: {message['engine']}")

# User Prompt Detection Box
if user_prompt := st.chat_input("Speak to Effiong AI..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    
    # Triggering the Brain Architecture Chain
    with st.chat_message("assistant"):
        with st.spinner("Processing through neural pathways..."):
            
            # Compile conversation context framework
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
            
            # 1. Process Text Reasoning Responses via Failover Grid
            final_reply, active_engine = execute_neural_process(user_prompt, history_str)
            st.markdown(final_reply)
            st.caption(f"Processed via: {active_engine}")
            
            # 2. AUTONOMOUS VISUAL MATRIX PIPELINES (Listening for Creative Commands)
            if "GENERATE AN IMAGE" in user_prompt.upper() or "CREATE AN IMAGE" in user_prompt.upper():
                image_seed_prompt = user_prompt.replace("generate an image of", "").replace("create an image of", "")
                pollinations_img_url = f"https://image.pollinations.ai/p/{image_seed_prompt.strip().replace(' ', '%20')}?width=1024&height=1024&nologo=true"
                st.image(pollinations_img_url, caption=f"Visualized Matrix Output for: '{image_seed_prompt}'", use_column_width=True)
                
            elif "VIDEO" in user_prompt.upper() or "ANIMATION" in user_prompt.upper():
                st.info("🎬 Multimedia Framework engaged. Generating concept frame preview...")
                video_seed_prompt = user_prompt.replace("generate a video of", "").replace("generate an animation of", "")
                # Fallback rendering a rapid frame visual sequence placeholder inside the platform stream
                pollinations_frame_url = f"https://image.pollinations.ai/p/{video_seed_prompt.strip().replace(' ', '%20')}_cinematic_anime_motion_frame?width=1024&height=576&nologo=true"
                st.image(pollinations_frame_url, caption="🎬 High-Fidelity Cinematic Prompt Frame Rendered Successfully.")
                st.caption("Copy Effiong AI's structured motion parameters block above directly into Runway Gen-3 or Luma Dream Machine to complete multi-second clip compilation.")
            
            # Log exchange to state cache memory
            st.session_state.chat_history.append({"role": "assistant", "content": final_reply, "engine": active_engine})
            
            # 3. Save new knowledge back to GitHub database memory autonomously
            if "recharging" not in final_reply and "System Error" not in final_reply:
                try:
                    auto_archive_to_github(user_prompt, final_reply)
                except Exception:
                    pass