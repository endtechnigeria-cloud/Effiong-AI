import streamlit as st
import streamlit.components.v1 as components


# ==========================================================
# VOICE STATE INITIALIZATION
# ==========================================================

def initialize_voice_state():

    defaults = {

        "voice_enabled": True,

        "voice_auto_speak": True,

        "voice_language": "en-US",

        "last_spoken_text": None,

        "voice_provider": "browser"
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


# ==========================================================
# VOICE SETTINGS PANEL
# ==========================================================

def render_voice_settings():

    initialize_voice_state()

    with st.expander(
        "🎙️ Voice Settings",
        expanded=False
    ):

        st.session_state.voice_enabled = st.toggle(
            "Enable Voice",
            value=st.session_state.voice_enabled
        )

        st.session_state.voice_auto_speak = st.toggle(
            "Auto Speak Responses",
            value=st.session_state.voice_auto_speak
        )

        st.session_state.voice_language = st.selectbox(
            "Language",
            [
                "en-US",
                "en-GB",
                "fr-FR",
                "ar-SA",
                "sw-KE"
            ],
            index=0
        )

        st.session_state.voice_provider = st.selectbox(
            "Voice Provider",
            [
                "browser",
                "groq_whisper_future",
                "gemini_live_future",
                "elevenlabs_future"
            ]
        )


# ==========================================================
# SPEAK RESPONSE
# ==========================================================

def speak_text(
    text: str,
    unique_id: str
):

    if not st.session_state.voice_enabled:

        return

    if not st.session_state.voice_auto_speak:

        return

    escaped = (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", " ")
    )

    components.html(
        f"""
        <script>

        const speech = new SpeechSynthesisUtterance(
            '{escaped}'
        );

        speech.lang = '{st.session_state.voice_language}';

        window.speechSynthesis.cancel();

        window.speechSynthesis.speak(
            speech
        );

        </script>
        """,
        height=0
    )


# ==========================================================
# MANUAL PLAY BUTTON
# ==========================================================

def render_play_button(
    text: str,
    unique_key: str
):

    if st.button(
        "🔊 Listen",
        key=f"play_{unique_key}"
    ):

        st.session_state.last_spoken_text = text

        speak_text(
            text,
            unique_key
        )


# ==========================================================
# VOICE INPUT COMPONENT
# ==========================================================

def render_voice_input():

    if not st.session_state.voice_enabled:

        return

    components.html(
        f"""
        <div style="
            display:flex;
            align-items:center;
            justify-content:center;
        ">

            <button
                id="effiong-voice-btn"
                style="
                    width:100%;
                    background:#121620;
                    border:1px solid #212631;
                    border-radius:10px;
                    color:white;
                    padding:12px;
                    cursor:pointer;
                "
            >
                🎙️ Speak
            </button>

        </div>

        <script>

        let recognition;
        let listening = false;

        const btn =
            document.getElementById(
                "effiong-voice-btn"
            );

        if (
            'webkitSpeechRecognition'
            in window
            ||
            'SpeechRecognition'
            in window
        )
        {{

            recognition =
                new (
                    window.SpeechRecognition
                    ||
                    window.webkitSpeechRecognition
                )();

            recognition.continuous = true;

            recognition.interimResults = true;

            recognition.lang =
                "{st.session_state.voice_language}";

            recognition.onstart = function()
            {{
                listening = true;

                btn.innerText =
                    "🔴 Listening...";
            }};

            recognition.onresult = function(
                event
            )
            {{

                let transcript = "";

                for (
                    let i = 0;
                    i < event.results.length;
                    i++
                )
                {{

                    transcript +=
                        event.results[i][0].transcript
                        + " ";

                }}

                const rootDoc =
                    window.parent.document;

                const chatInput =
                    rootDoc.querySelector(
                        'textarea[data-testid="stChatInputTextArea"]'
                    );

                if(chatInput)
                {{

                    const setter =
                        Object.getOwnPropertyDescriptor(
                            HTMLTextAreaElement.prototype,
                            "value"
                        ).set;

                    setter.call(
                        chatInput,
                        transcript
                    );

                    chatInput.dispatchEvent(
                        new Event(
                            "input",
                            {{
                                bubbles:true
                            }}
                        )
                    );
                }}
            }};

            recognition.onend = function()
            {{
                if(listening)
                {{
                    recognition.start();
                }}
            }};

            btn.onclick = function()
            {{

                if(!listening)
                {{
                    recognition.start();
                }}
                else
                {{
                    listening = false;

                    recognition.stop();

                    btn.innerText =
                        "🎙️ Speak";
                }}
            }};
        }}

        else
        {{
            btn.innerText =
                "Voice Unsupported";
        }}

        </script>
        """,
        height=60
    )


# ==========================================================
# AUTO SPEAK SEGMENT
# ==========================================================

def auto_speak_segment(
    segment_text: str,
    segment_id: str
):

    if (
        st.session_state.last_spoken_text
        ==
        segment_id
    ):
        return

    st.session_state.last_spoken_text = segment_id

    speak_text(
        segment_text,
        segment_id
    )


# ==========================================================
# CHAT INPUT BAR WITH VOICE
# ==========================================================

def render_chat_input_with_voice():

    left, right = st.columns(
        [10, 2]
    )

    with left:

        prompt = st.chat_input(
            "Message Effiong AI..."
        )

    with right:

        render_voice_input()

    return prompt