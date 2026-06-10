import streamlit as st
import streamlit.components.v1 as components
import re

def parse_ai_response_into_segments(raw_ai_text, message_index):
    """
    Analyzes Effiong AI's response text and groups paragraphs/sentences into
    segmented nodes based on whether they Answer, Ask, or Instruct.
    """
    # Break down the response text into paragraphs or distinct line blocks
    lines = [line.strip() for line in raw_ai_text.split('\n') if line.strip()]
    segments = []
    
    current_chunk = []
    current_type = None
    segment_counter = 0

    def get_header_title(seg_type, count):
        if seg_type == "question":
            return f"❓ Sovereign Follow-up Inquiry Node #{count}"
        elif seg_type == "instruction":
            return f"🛠️ Sovereign Executive Instruction Node #{count}"
        else:
            return f"⚡ Sovereign Contextual Resolution Node #{count}"

    for line in lines:
        # Detect the nature of the AI text line
        if line.endswith('?'):
            line_type = "question"
        elif any(line.startswith(prefix) for prefix in ["1.", "2.", "3.", "-", "•"]) or any(keyword in line.lower() for keyword in ["step", "please", "make sure", "ensure", "follow"]):
            line_type = "instruction"
        else:
            line_type = "answer"

        # If the context type shifts, flush the previous accumulated block into a segment panel
        if current_type is not None and line_type != current_type and current_chunk:
            segment_counter += 1
            segments.append({
                "id": f"seg_{message_index}_{segment_counter}",
                "title": get_header_title(current_type, segment_counter),
                "type": "text",
                "content": " ".join(current_chunk)
            })
            current_chunk = []

        current_type = line_type
        current_chunk.append(line)

    # Flush remaining text into the final segment block
    if current_chunk:
        segment_counter += 1
        segments.append({
            "id": f"seg_{message_index}_{segment_counter}",
            "title": get_header_title(current_type, segment_counter),
            "type": "text",
            "content": " ".join(current_chunk)
        })

    # Safe fallback if text analysis generates no structural divisions
    if not segments:
        segments.append({
            "id": f"seg_{message_index}_1",
            "title": "⚡ Sovereign Contextual Resolution Node",
            "type": "text",
            "content": raw_ai_text
        })

    return segments


def render_segmented_chat():
    if not st.session_state.master_messages:
        st.markdown("""
        <div class="landing-hero">
            <div class="landing-title">🐆 Effiong AI</div>
            <div class="landing-caption">The World's Preeminent Future-Discerning, Truth-Seeking, and Historical Preservation Platform</div>
        </div>
        """, unsafe_allow_html=True)

    stream_container = st.container()
    with stream_container:
        for msg_idx, msg in enumerate(st.session_state.master_messages):
            if msg["role"] == "user":
                st.markdown(f"""
                <div style='background-color: #121620; padding: 16px; border-radius: 8px; margin-bottom: 24px; border: 1px solid #212631;'>
                    <span style='color: #D27D2D; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;'>User Query</span>
                    <p style='margin: 8px 0 0 0; color: #FFFFFF; font-size: 1.1rem; line-height: 1.5;'>{msg['content']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for seg in msg["segments"]:
                    seg_id = f"{msg_idx}_{seg['id']}"
                    
                    st.markdown(f"""
                    <div class="segmented-response-box">
                        <div class="segment-header">{seg['title']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if seg["type"] == "text":
                        st.markdown(f"<div style='color: #E6EDF2; font-size: 1.05rem; line-height: 1.6; padding-left: 5px; padding-bottom: 10px;'>{seg['content']}</div>", unsafe_allow_html=True)
                        
                        if st.session_state.last_spoken_trigger == seg_id:
                            clean_speech_text = seg["content"].replace("'", "\\'").replace("\n", " ")
                            st.markdown(f"""
                            <script>
                                var msg = new SpeechSynthesisUtterance('{clean_speech_text}');
                                window.speechSynthesis.speak(msg);
                            </script>
                            """, unsafe_allow_html=True)
                        
                    elif seg["type"] == "image":
                        st.image(seg["content"], caption=seg.get("caption", ""))
                        
                    elif seg["type"] == "video":
                        st.video(seg["content"])
                        if "caption" in seg:
                            st.caption(seg["caption"])
                        
                    elif seg["type"] == "document":
                        st.markdown(f"<div style='margin-bottom: 12px; color: #8B949E; padding-left: 5px;'>📄 Generated Material Node: <b>{seg['filename']}</b></div>", unsafe_allow_html=True)
                        st.download_button(
                            label="📥 Download Material Asset",
                            data=seg["content"],
                            file_name=seg["filename"],
                            mime="text/plain",
                            key=f"dl_{seg_id}"
                        )

                    if seg_id not in st.session_state.segment_threads:
                        st.session_state.segment_threads[seg_id] = []

                    for thread_msg in st.session_state.segment_threads[seg_id]:
                        if thread_msg["role"] == "user":
                            st.markdown(f"<div style='padding-left: 24px; border-left: 2px solid #D27D2D; color: #D27D2D; font-size: 0.95rem; margin-top: 12px;'><b>You:</b> {thread_msg['content']}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='padding-left: 24px; border-left: 2px solid #8B949E; color: #C9D1D9; font-size: 0.95rem; margin-top: 8px; margin-bottom: 12px;'><b>Effiong AI:</b> {thread_msg['content']}</div>", unsafe_allow_html=True)

                    with st.form(key=f"form_{seg_id}", clear_on_submit=True):
                        col1, col2 = st.columns([6, 1])
                        with col1:
                            thread_input = st.text_input(
                                "Branch off here...",
                                key=f"input_{seg_id}",
                                label_visibility="collapsed",
                                placeholder="Refine or branch off on this specific aspect..."
                            )
                        with col2:
                            st.form_submit_button("Branch")

                        if thread_input:
                            st.session_state.segment_threads[seg_id].append({"role": "user", "content": thread_input})
                            reply_blueprint = f"Analyzing specific segment thread branch: '{thread_input}'."
                            st.session_state.segment_threads[seg_id].append({"role": "assistant", "content": reply_blueprint})
                            st.rerun()
                    
                    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    st.write("---")

    input_col, voice_col = st.columns([10, 2], vertical_alignment="center")
    
    with input_col:
        master_input = st.chat_input("Message Effiong AI...")
        
    with voice_col:
        components.html("""
        <div style="display: flex; align-items: center; justify-content: flex-start; height: 100%;">
            <button id="mic-btn" style="
                background-color: #121620; 
                color: #F0F6FC; 
                border: 1px solid #212631; 
                padding: 12px 14px; 
                border-radius: 12px; 
                cursor: pointer; 
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
                width: 100%;
                font-family: system-ui, -apple-system, sans-serif;
                transition: all 0.2s ease;
            ">
                <span id="mic-icon">🎙️</span> <span id="mic-text">Speak</span>
            </button>
        </div>

        <script>
            const micBtn = document.getElementById('mic-btn');
            const micIcon = document.getElementById('mic-icon');
            const micText = document.getElementById('mic-text');
            
            let recognition;
            let isListening = false;
            let finalTranscript = '';
            
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = 'en-US';
                recognition.continuous = true;
                recognition.interimResults = true;
                
                recognition.onstart = function() {
                    isListening = true;
                    finalTranscript = '';
                    micBtn.style.borderColor = '#D27D2D';
                    micBtn.style.backgroundColor = '#211A12';
                    micText.innerText = "Listening...";
                    micIcon.innerText = "🔴";
                };
                
                recognition.onresult = function(event) {
                    let interimTranscript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalTranscript += event.results[i][0].transcript + ' ';
                        } else {
                            interimTranscript += event.results[i][0].transcript;
                        }
                    }
                    
                    let liveOutput = finalTranscript + interimTranscript;
                    var rootDoc = window.parent.document;
                    var chatInputBox = rootDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    
                    if (chatInputBox && liveOutput.trim().length > 0) {
                        const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeTextAreaValueSetter.call(chatInputBox, liveOutput.trim());
                        chatInputBox.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                };
                
                recognition.onerror = function(event) {
                    if (event.error !== 'no-speech') {
                        console.error("Speech Recognition Error: ", event.error);
                        resetButton();
                    }
                };
                
                recognition.onend = function() {
                    if (isListening) {
                        recognition.start();
                    }
                };
                
                function resetButton() {
                    isListening = false;
                    recognition.stop();
                    micBtn.style.borderColor = '#212631';
                    micBtn.style.backgroundColor = '#121620';
                    micText.innerText = "Speak";
                    micIcon.innerText = "🎙️";
                    
                    var rootDoc = window.parent.document;
                    var chatInputBox = rootDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    if (chatInputBox) {
                        chatInputBox.focus();
                    }
                }
                
                micBtn.addEventListener('click', function() {
                    if (!isListening) {
                        recognition.start();
                    } else {
                        resetButton();
                    }
                });
                
            } else {
                micText.innerText = "Unsupported Browser";
                micBtn.style.opacity = "0.5";
            }
        </script>
        """, height=52, scrolling=False)

    if master_input:
        st.session_state.master_messages.append({"role": "user", "content": master_input})
        
        # Connect to our Sovereign multi-brain router backend
        from src.services.brain_router import execute_sovereign_intelligence_cycle
        
        with st.spinner("Effiong AI querying knowledge repositories and synchronizing cloud brains..."):
            live_ai_response = execute_sovereign_intelligence_cycle(master_input)
        
        # Dynamically segment based strictly on the content of the computed AI response
        message_index = len(st.session_state.master_messages)
        parsed_segments = parse_ai_response_into_segments(live_ai_response, message_index)
        
        # Assign text-to-speech to focus target on the first segment block
        st.session_state.last_spoken_trigger = f"{message_index}_{parsed_segments[0]['id']}"
        
        st.session_state.master_messages.append({
            "role": "assistant",
            "segments": parsed_segments
        })
        st.rerun()
