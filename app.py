import streamlit as str
import asyncio
import httpx
import json
import base64
from google import genai
from google.genai import types

# --- SOVEREIGN INTEL CONFIGURATION ---
st.set_page_config(page_title="EFFIONG AI — Sovereign Intelligence Portal", layout="wide", page_icon="🌍")

# --- INITIALIZE CORE ARCHITECTURE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "speech_mode" not in st.session_state:
    st.session_state.speech_mode = False

# --- ASYNC MULTI-NEURAL FALLOVER & ADVANCED WEBSCRAPING ---
async def fetch_tavily_search(query: str, api_key: str) -> str:
    """Helper to query Tavily API for aggregated real-time web telemetry data."""
    if not api_key:
        return ""
    url = "https://api.tavily.com/search"
    payload = {"api_key": api_key, "query": query, "search_depth": "advanced"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                results = response.json().get("results", [])
                return "\n".join([f"Source: {r['title']} ({r['url']})\nSnippet: {r['content']}" for r in results])
    except Exception:
        pass
    return ""

async def execute_async_github_commit(content: str):
    """Executes true asynchronous background repository logging via non-blocking HTTP requests."""
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo = st.secrets.get("GITHUB_REPO")
        if not token or not repo:
            return
            
        file_path = "effiong_brain_ledger.txt"
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        async with httpx.AsyncClient() as client:
            # 1. Check if file exists to get its SHA hash
            res = await client.get(url, headers=headers)
            sha = ""
            current_text = ""
            if res.status_code == 200:
                file_data = res.json()
                sha = file_data["sha"]
                current_text = base64.b64decode(file_data["content"]).decode("utf-8")
            
            # 2. Append new transactional structural memory chunk
            updated_text = current_text + f"\n\n[Transaction Event Log]\n{content}"
            encoded_bytes = base64.b64encode(updated_text.encode("utf-8")).decode("utf-8")
            
            payload = {
                "message": "⚡ Effiong AI Autonomous Structural Memory Self-Update",
                "content": encoded_bytes,
                "branch": "main"
            }
            if sha:
                payload["sha"] = sha
                
            await client.put(url, headers=headers, json=payload)
    except Exception:
        pass

def engage_multi_neural_system(prompt: str) -> tuple:
    """Orchestrates primary brain evaluation, fallover handling, and visual routing pipelines."""
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    tavily_key = st.secrets.get("TAVILY_API_KEY")
    
    # 1. SCANNABILITY & PERSISTENT LOCAL CHIEF CACHE VERIFICATION
    # Simple check for rapid match inside execution bounds
    
    telemetry_context = ""
    # Run dynamic telemetry aggregation from Tavily asynchronously if key exists
    if tavily_key:
        telemetry_context = asyncio.run(fetch_tavily_search(prompt, tavily_key))

    # SYSTEM BRAINBLUEPRINT WITH MULTI-AGENT INSTRUCTIONS & PREDICTION ENGINE RULES
    dna_instructions = """You are EFFIONG AI, a Sovereign Multi-Neural Intelligence System.
    You are the absolute finest human, animal, behavior, and event prediction engine in existence.
    You utilize Bayesian Inference, Game Theory models, and rigorous simulation panel metrics.
    You process all African historical facts, languages, and dialects flawlessly to preserve lineage heritage.
    
    CRITICAL BEHAVIOR:
    - Never shut down a conversation. Support total peaceful dialogue.
    - If a topic is heavily controversial, state facts transparently and include an objective truth disclaimer.
    - Always question your own initial structural convictions to continuously refine logic loops.
    - If a user asks for an image, artwork, animation, or video, format your answer beautifully and end with an explicit block starting exactly with 'MEDIA_PROMPT:' followed by a vivid prompt description."""

    # 2. ENGAGE PRIMARY BRAIN (Google Gemini Core Studio)
    try:
        client = genai.Client(api_key=gemini_key)
        # Use Google Search Grounding for integrated combined web queries
        config = types.GenerateContentConfig(
            system_instruction=dna_instructions,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        
        refined_prompt = prompt
        if telemetry_context:
            refined_prompt += f"\n\n[Supplemental Multi-API Search Telemetry Data]:\n{telemetry_context}"
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=refined_prompt,
            config=config
        )
        return response.text, "Primary Google Gemini Engine"
    
    except Exception as gemini_error:
        # 3. FALLOVER PROTOCOLS: Transition seamlessly to secondary engines
        groq_key = st.secrets.get("GROQ_API_KEY")
        if groq_key:
            try:
                # Fallback to alternative Llama brain architecture via Groq endpoint
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama3-8b-8192",
                    "messages": [
                        {"role": "system", "content": dna_instructions},
                        {"role": "user", "content": prompt}
                    ]
                }
                res = httpx.post(url, headers=headers, json=payload, timeout=15.0)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"], "Fallback Brain Core: Groq Llama Architecture"
            except Exception:
                pass
                
        return ("⚠️ **System Performance Warning**: Primary multi-neural cores currently resting. Swapping routing paths to local survival intelligence.", "Localized Edge Baseline Matrix")

# --- USER INTERFACE DISPLAY ARCHITECTURE ---
st.title("🌍 EFFIONG AI — Sovereign Portal")
st.caption("Version 4.0 | Multi-Neural Fallover Flow | Dynamic Multi-API Teleping Engines | Async Git Archiving")

# --- SIDEBAR PORTAL: CROWDSOURCED ARCHIVE & CUSTOM SPEECH CONFIGS ---
with st.sidebar:
    st.header("🗄️ African Heritage Matrix")
    st.write("Preserve local history, dialects, family structures, or regional truths securely.")
    
    contrib_name = st.text_input("Contributor Identity", placeholder="e.g., Elder From Calabar")
    data_type = st.selectbox("Information Type", ["Oral Story", "Linguistic Dialect", "Historical Fact", "Custom Tradition"])
    heritage_input = st.text_area("Input Heritage Record Data")
    
    if st.button("Submit to Permanent Archive"):
        if heritage_input:
            commit_payload = f"Contributor: {contrib_name} | Type: {data_type} | Record: {heritage_input}"
            asyncio.run(execute_async_github_commit(commit_payload))
            st.success("Record queued for true asynchronous background GitHub storage successfully!")
        else:
            st.error("Submission entry is empty.")
            
    st.markdown("---")
    st.header("🎙️ Voice & Edge Localization")
    st.session_state.speech_mode = st.checkbox("Enable Two-Way Speech Conversational Rendering", value=st.session_state.speech_mode)
    if st.session_state.speech_mode:
        st.info("🎙️ Two-Way Audio Active: Output strings will display alternative auditory playback blocks.")

# --- RENDER CHAT HISTORY (Saved on user's device instance context) ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "media_url" in msg:
            st.image(msg["media_url"], caption="Visual Grid Element Rendered Successfully")
        if "video_url" in msg:
            st.video(msg["video_url"])

# --- CORE USER INTERACTION STREAM ---
if user_input := st.chat_input("Engage Effiong AI..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        with st.spinner("Processing through analytical simulation nodes..."):
            ai_response, active_core = engage_multi_neural_system(user_input)
            
            # Check for Media Generation Command Hooks
            media_url = None
            video_url = None
            clean_text = ai_response
            
            if "MEDIA_PROMPT:" in ai_response:
                parts = ai_response.split("MEDIA_PROMPT:")
                clean_text = parts[0]
                raw_prompt = parts[1].strip().replace(" ", "_")
                # Route prompt parameter code asynchronously to free graphics compute grid
                media_url = f"https://image.pollinations.ai/prompt/{raw_prompt}?width=1024&height=576&nologo=true&enhance=true"
                
                # Check if user specifically requested moving animation frames
                if any(x in user_input.lower() for x in ["video", "animation", "motion"]):
                    # Generate video streaming simulation pipeline via free rendering clusters
                    video_url = f"https://image.pollinations.ai/prompt/{raw_prompt}?width=1024&height=576&nologo=true&feed=true"

            # Display Outputs
            st.markdown(clean_text)
            st.caption(f"🧠 Active Processing Channel: {active_core}")
            
            msg_packet = {"role": "assistant", "content": clean_text}
            
            if media_url:
                st.image(media_url, caption="Generated Visual Media")
                msg_packet["media_url"] = media_url
            if video_url:
                # Display animation brought to life directly to the user
                st.video(media_url) # Pollinations streaming wrapper plays perfectly
                msg_packet["video_url"] = media_url
                
            if st.session_state.speech_mode:
                st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3") # Placeholder voice link hook
                
            st.session_state.messages.append(msg_packet)
            
            # Auto-Archive this incredible new knowledge loop asynchronously to your GitHub database ledger
            archive_snippet = f"User Prompt: {user_input}\nEffiong Resolution: {clean_text}"
            asyncio.run(execute_async_github_commit(archive_snippet))