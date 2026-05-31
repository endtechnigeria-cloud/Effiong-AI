import streamlit as st
from google import genai
from google.genai import types
import requests
import base64
import re

# 1. Page Config
st.set_page_config(page_title="Effiong AI Dashboard", page_icon="🌍", layout="wide")

st.title("🌍 EFFIONG AI — Sovereign Intelligence Portal")
st.caption("Active Caching | Auto-Archiving Brain Ledger | Fail-Safe Quota Fallback Layer")

# 2. Extract Cloud Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    gh_token = st.secrets.get("GITHUB_TOKEN", None)
    gh_repo = st.secrets.get("GITHUB_REPO", None)
except Exception:
    st.error("Missing core secret variables in Streamlit Dashboard Settings.")
    st.stop()

# Initialize Google GenAI client
client = genai.Client(api_key=api_key)

# 3. HELPER FUNCTIONS: Read/Write Memory to GitHub Online Storage Base
def fetch_archive_from_github():
    if not gh_token or not gh_repo:
        return ""
    url = f"https://api.github.com/repos/{gh_repo}/contents/effiong_brain_ledger.txt"
    headers = {"Authorization": f"token {gh_token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content_b64 = res.json()['content']
        return base64.b64decode(content_b64).decode('utf-8')
    return ""

def append_to_github_archive(user_q, ai_ans):
    if not gh_token or not gh_repo:
        return
    url = f"https://api.github.com/repos/{gh_repo}/contents/effiong_brain_ledger.txt"
    headers = {"Authorization": f"token {gh_token}"}
    
    # Get current file info if it exists
    res = requests.get(url, headers=headers)
    sha = None
    current_content = ""
    if res.status_code == 200:
        sha = res.json()['sha']
        current_content = base64.b64decode(res.json()['content']).decode('utf-8')
    
    # Append new transaction
    new_entry = f"\n\n[QUERY]: {user_q}\n[MEMORY]: {ai_ans}\n---"
    updated_content = current_content + new_entry
    updated_b64 = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": "Effiong AI Brain Sync: Self-Updated Memory Ledger",
        "content": updated_b64
    }
    if sha:
        payload["sha"] = sha
        
    requests.put(url, headers=headers, json=payload)

# 4. Fetch Entire Online Memory Before Initializing System Instructions
ledger_memory = fetch_archive_from_github()
if not ledger_memory:
    ledger_memory = "No previously stored memory entries found in online base."

system_instruction = f"""
You are EFFIONG AI, operating in Sovereign Mode.
You have access to a local memory base containing answers you previously reasoned or generated.

[LOCAL COMPREHENSIVE MEMORY LEDGER]:
{ledger_memory}

Rule: If the information requested by the user already exists explicitly within your [LOCAL COMPREHENSIVE MEMORY LEDGER], summarize or reproduce it accurately without initiating an external live web search or fabricating entirely new alternative assertions. Maintain internal consistency.
"""

# 5. Chat Interface Execution
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Engage with Effiong AI..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # --- CACHE CHECK ENGINE ---
        # Look for existing keywords in ledger to decide if we bypass or proceed
        local_match = None
        cleaned_prompt = user_prompt.lower().strip()
        
        # Simple local text scan for matching historical queries inside the file
        if cleaned_prompt in ledger_memory.lower():
            # Find the blocks that fit best using regex or basic block search
            blocks = ledger_memory.split("---")
            for block in blocks:
                if "[QUERY]:" in block and cleaned_prompt in block.lower():
                    local_match = block.split("[MEMORY]:")[-1].strip()
                    break

        # --- EXECUTION STAGE ---
        if local_match:
            # Bypassed Google completely! Pulling directly from its own local base saved online
            ai_response = f"💡 **[Effiong Local Brain Base Memory Match]:**\n\n{local_match}"
            message_placeholder.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
        else:
            try:
                # Invoke the main cloud brain
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                ai_response = response.text
                
                # Check for direct image/video rendering strings
                if ".mp4" in ai_response or "video.pollinations.ai" in ai_response:
                    message_placeholder.markdown(ai_response)
                    urls = re.findall(r'(https?://[^\s)]+\.(?:mp4|webm|ogg))', ai_response)
                    for url in urls:
                        st.video(url)
                else:
                    message_placeholder.markdown(ai_response)
                
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                # SELF-UPDATE MODULE: Transmit fresh learning instantly to online GitHub text storage
                with st.spinner("Synchronizing structural insights to permanent storage base..."):
                    append_to_github_archive(user_prompt, ai_response)
                    
            except Exception as e:
                # --- AUTOMATIC FALLBACK LAYER ---
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.warning("⚠️ **Google Free Tier Quota Exhausted.** Activating Effiong Local Knowledge Fallback Protocol...")
                    
                    # We send a specialized hidden instruction locally via string formatting to search our file context
                    fallback_prompt = f"Using your provided [LOCAL COMPREHENSIVE MEMORY LEDGER], answer the question: {user_prompt}"
                    
                    # Because Google API is offline, we use a basic keyword retrieval tool locally to summarize what we have
                    relevant_notes = [b for b in ledger_memory.split("---") if any(w in b.lower() for w in cleaned_prompt.split())]
                    
                    if relevant_notes:
                        fallback_response = "### 📚 Fallback Ledger Synthesized Response:\n" + "\n".join(relevant_notes)
                    else:
                        fallback_response = "### 📚 Fallback Ledger Active:\nI cannot find an exact pattern matchup in my local archives for this topic, and my live Google neural link is currently resting. Please try again soon or look into your ledger file configurations."
                        
                    message_placeholder.markdown(fallback_response)
                    st.session_state.messages.append({"role": "assistant", "content": fallback_response})
                else:
                    st.error(f"Error engaging processing cluster: {e}")