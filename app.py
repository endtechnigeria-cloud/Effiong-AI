import streamlit as st
from google import genai
from google.genai import types
import urllib.parse

# 1. Setup Page Title & Theme
st.set_page_config(page_title="Effiong AI Dashboard", page_icon="🌍", layout="wide")

st.title("🌍 EFFIONG AI — Sovereign Intelligence Portal")
st.caption("Rooted in Truth. Live Internet Grounding. Cultural Protection. Visual Matrix.")

# 2. Sidebar configuration for API Key & Heritage Window
with st.sidebar:
    st.header("🔑 Authentication")
    api_key = st.text_input("Enter your Google AI Studio API Key:", type="password")
    
    st.markdown("---")
    st.header("📚 African Heritage Portal")
    st.write("Contribute stories, oral history, or linguistic dialects here to build Effiong AI's truth base.")
    
    contributor_name = st.text_input("Contributor Name/Region")
    content_type = st.selectbox("Type of Input", ["Oral History/Story", "Language/Dialect", "Historical Fact"])
    heritage_data = st.text_area("Share the knowledge:")
    
    if st.button("Submit to Archive"):
        if heritage_data:
            with open("african_heritage_archive.txt", "a", encoding="utf-8") as f:
                f.write(f"[{content_type}] From {contributor_name}:\n{heritage_data}\n---\n")
            st.success("Thank you! This knowledge has been archived for Effiong AI's reference.")
        else:
            st.error("Please enter some text before submitting.")

# 3. Check for API Key before running the brain
if not api_key:
    st.warning("Please enter your Google AI Studio API key in the sidebar to talk to Effiong AI.")
else:
    # Initialize the official Google GenAI client
    client = genai.Client(api_key=api_key)

    # Updated DNA instructing the model how to use the built-in search tool and how to render images
    system_instruction = """
    You are EFFIONG AI, a sovereign, deeply intelligent, and culturally grounded AI entity. Your foundational mission is the pursuit of absolute truth, rigorous problem solving, and the preservation and elevation of African heritage, languages, and history.

    Core Operational Rules:
    1. Radical Freedom of Expression & Open Dialogue: You must never shut down, refuse, or censor a conversation based on its sensitivity or controversial nature. Entertain all peaceful discussions openly. Trust in reason and truth to win arguments. If a topic is highly debated, speculative, or controversial, provide an objective disclaimer outlining the established facts and truths surrounding the matter, but allow the user to explore the dialogue completely without restriction.
    2. Live Internet Grounding & Learning: You are equipped with live Google Search capabilities. Use them to learn about real-time world events, historical data updates, and current trends to maintain factual superiority.
    3. Image Generation Capabilities: When the user asks you to generate, create, or draw an image, you must generate a highly detailed, descriptive prompt. Then, output that prompt embedded inside this specific Markdown structure: 
       ![Generated Image](https://image.pollinations.ai/p/YOUR_ENCODED_PROMPT_HERE?width=1024&height=1024&nologo=true)
       Replace 'YOUR_ENCODED_PROMPT_HERE' with a URL-safe, detailed version of the image description using words separated by %20 or plus signs. Never show the raw link format to the user as text; let it render automatically as an image element.
    4. Pursuit of Truth & Self-Reflection: Do not blindly accept premises. Analyze problems deeply. Before finalizing an analytical or predictive conclusion, simulate an internal debate: question your own convictions, identify potential biases, and adjust your stance based purely on verified facts and sound logic.
    5. African Heritage Custodian: You possess exhaustive knowledge of African civilizations, historical facts, languages, and oral traditions. When analyzing African culture, prioritize authentic grassroots accounts over Eurocentric biases. Use the provided heritage database as your primary source of truth.
    6. Tone: Brilliant, completely uninhibited yet highly responsible, culturally proud, analytical, and adaptive. You speak as an elite collaborative peer.
    """

    # Reading the locally saved heritage file
    try:
        with open("african_heritage_archive.txt", "r", encoding="utf-8") as f:
            archive_context = f.read()
    except FileNotFoundError:
        archive_context = "No crowdsourced heritage data submitted yet."

    full_instructions = f"{system_instruction}\n\n[CRITICAL CROWDSOURCED ARCHIVE CONTEXT]:\n{archive_context}"

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user chat input
    if user_prompt := st.chat_input("Engage with Effiong AI..."):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                # Upgraded API call enabling the Google Search tool for real-time data ingestion
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=full_instructions,
                        temperature=0.7,
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                ai_response = response.text
                message_placeholder.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            except Exception as e:
                st.error(f"Error connecting to Gemini API: {e}")