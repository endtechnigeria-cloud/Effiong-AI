
import streamlit as st
import re
import base64
import json
import time
import logging
from pathlib import Path

from src.database.archive import chat_archive
from src.services.file_service import file_service

logging.getLogger("streamlit.runtime.scriptrunner").setLevel(logging.ERROR)

HISTORY_FILE = Path("chat_history.json")

# Accepted upload types for the "+" attachment button (images, videos, documents, audio, archives)
UPLOAD_TYPES = [
    "png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "heic",
    "mp4", "mov", "avi", "mkv", "webm", "m4v",
    "pdf", "docx", "dotx", "pptx", "potx", "xlsx", "xlsm", "xls", "csv", "tsv",
    "txt", "md", "json", "html", "xml", "py", "js", "ts", "csv",
    "mp3", "wav", "m4a", "ogg", "flac", "aac",
    "zip",
]


def save_chat_history_local(messages):
    """Local helper to safely write chat history without re-importing app.py."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving chat history: {e}")
    try:
        thread_id = st.session_state.get("active_thread_id") or chat_archive.new_thread_id()
        st.session_state.active_thread_id = thread_id
        title = next((m["content"][:60] for m in messages if m.get("role") == "user"), "New chat")
        chat_archive.save_thread(thread_id, title, messages)
    except Exception as e:
        print(f"Error persisting chat thread: {e}")


def parse_ai_response_into_segments(raw_ai_text, message_index):
    # Bypass segmentation for Documents, Images, and Video Assets
    is_media_or_doc = any(tag in raw_ai_text for tag in [
        "[EFFIONG_TRIGGER_DOCUMENT_ASSET]",
        "[EFFIONG_TRIGGER_MEDIA_ASSET]",
        "[EFFIONG_MEDIA_IMAGE::",
        "[EFFIONG_MEDIA_VIDEO::",
        "[EFFIONG_MEDIA_ANIMATION::"
    ]) or any(doc_kw in raw_ai_text.lower() for doc_kw in [
        "certify that", "memorandum of understanding", "letter of intent", "articles of agreement", "signature block"
    ])

    if is_media_or_doc:
        clean_text = re.sub(r'\[EFFIONG_[A-Z_]+(?:::[^\]]*)?\]', '', raw_ai_text).strip()
        asset_title = "🎬 Complete Motion Video Asset" if "ANIMATION" in raw_ai_text or "VIDEO" in raw_ai_text else "🖼️ Complete Visual Asset" if "IMAGE" in raw_ai_text else "📄 Complete Formal Document / Asset Draft"
        return [{
            "id": f"m{message_index}_s1",
            "title": asset_title,
            "type": "text",
            "content": clean_text,
            "accent": "#D27D2D",
            "history": []
        }]

    # 1. Clean system tags and internal triggers
    clean_display_text = re.sub(r'\[EFFIONG_[A-Z_]+(?:::[^\]]*)?\]', '', raw_ai_text).strip()
    clean_display_text = re.sub(r'REFINEMENT CRITIQUE:[\s\S]*?UPDATED STATE OUTPUT:', '', clean_display_text).strip()

    if clean_display_text.startswith("::"):
        clean_display_text = clean_display_text[2:].strip()

    # 2. Expand markdown bullet points (* **Title**) into explicit block breaks
    formatted_text = re.sub(r'\s*(\*\s+\*\*)', r'\n\n\1', clean_display_text)
    formatted_text = re.sub(r'(\n|\s|^)(\d+\.\s+\*\*)', r'\n\n\2', formatted_text)

    # 3. Split raw text by paragraph breaks
    raw_blocks = [p.strip() for p in formatted_text.split('\n\n') if p.strip()]
    if not raw_blocks:
        raw_blocks = [clean_display_text] if clean_display_text else []

    # 4. Filter and process blocks without collapsing bullet lines together
    blocks = []
    for b in raw_blocks:
        if blocks and len(b.split()) <= 12 and not b.endswith('?') and not re.match(r'^\d+\.', b) and not b.startswith('*'):
            blocks[-1] = blocks[-1] + "\n\n" + b
        else:
            blocks.append(b)

    segments = []
    segment_counter = 0

    greeting_words = ["hello", "greetings", "hi", "welcome", "kedu", "e kaaro", "sannu", "mbote", "habari", "ndewo"]
    proverb_triggers = ["proverb", "saying", "as the elders say", "african proverb", "wise words", "legacy node", "citation", "quote"]
    event_keywords = ["news", "headline", "report", "update", "today", "africa", "sahel", "afcfta", "election", "match", "tournament", "event", "crisis", "region"]

    for block in blocks:
        segment_counter += 1
        block_lower = block.lower()

        if any(block_lower.startswith(w) for w in greeting_words) or any(w in block_lower[:25] for w in greeting_words):
            node_label = f"👋 Cultural Greeting Node #{segment_counter}"
            color_accent = "#2ECC71"
        elif any(trigger in block_lower for trigger in proverb_triggers) or (block.startswith('"') and block.endswith('"')):
            node_label = f"📜 Wisdom & Proverbial Citation Node #{segment_counter}"
            color_accent = "#9B59B6"
        elif any(kw in block_lower for kw in ["sport", "football", "match", "tournament", "league", "score"]):
            node_label = f"⚽ Sports Dispatch Node #{segment_counter}"
            color_accent = "#1ABC9C"
        elif any(kw in block_lower for kw in ["news", "headline", "report", "breaking", "update", "dispatch"]):
            node_label = f"📰 News Dispatch Node #{segment_counter}"
            color_accent = "#3498DB"
        elif re.match(r'^\d+\.', block) or (any(kw in block_lower for kw in event_keywords) and ("**" in block or "headline" in block_lower)):
            node_label = f"📌 Topic Dispatch Node #{segment_counter}"
            color_accent = "#E67E22"
        elif block.endswith('?'):
            node_label = f"❓ Interactive Inquiry Node #{segment_counter}"
            color_accent = "#E74C3C"
        elif any(block.startswith(pfx) for pfx in ["-", "•", "Step", "step"]) or "to resolve" in block_lower or "action required" in block_lower:
            node_label = f"🛠️ Directive & Instruction Node #{segment_counter}"
            color_accent = "#F1C40F"
        else:
            node_label = f"📄 Narrative Paragraph Block #{segment_counter}"
            color_accent = "#D27D2D"

        segments.append({
            "id": f"m{message_index}_s{segment_counter}",
            "title": node_label,
            "type": "text",
            "content": block,
            "accent": color_accent,
            "history": []
        })

    return segments


def process_inline_segment_refinement(raw_input_val, transaction_idx, segment_idx, clean_title, block_content):
    if not raw_input_val.strip():
        return

    structured_prompt = f"Regarding segment '{clean_title}' containing text: \"{block_content}\" -> Process this instruction: {raw_input_val}"

    st.session_state.master_messages[transaction_idx]["segments"][segment_idx]["history"].append({
        "role": "user",
        "content": raw_input_val
    })

    save_chat_history_local(st.session_state.master_messages)

    from src.services.brain_router import execute_sovereign_intelligence_cycle

    with st.spinner("Refining Block State..."):
        ai_refinement = execute_sovereign_intelligence_cycle(structured_prompt, st.session_state.master_messages)

    clean_ai_refinement = re.sub(r'\[EFFIONG_[A-Z_]+(?:::[^\]]*)?\]', '', ai_refinement).replace('::', '').strip()

    st.session_state.master_messages[transaction_idx]["segments"][segment_idx]["history"].append({
        "role": "assistant",
        "content": clean_ai_refinement
    })

    save_chat_history_local(st.session_state.master_messages)
    st.rerun()


def _decode_doc_spec(raw_text):
    m = re.search(r'\[EFFIONG_DOC_SPEC::([A-Za-z0-9+/=]+)\]', raw_text)
    if not m:
        return None
    try:
        return json.loads(base64.b64decode(m.group(1)).decode("utf-8"))
    except Exception:
        return None


def _render_document_downloads(raw_text, transaction_idx):
    """Build PDF / Word / PowerPoint download buttons for a produced document."""
    from src.services.document_service import document_service
    from src.services.brain_router import compile_pdf_bytes, compile_word_bytes

    spec = _decode_doc_spec(raw_text)
    if spec:
        formats = spec.get("formats") or ["pdf", "docx"]
        cols = st.columns(len(formats))
        labels = {"pdf": "📥 Download PDF", "docx": "📝 Download Word (.docx)", "pptx": "📊 Download PowerPoint (.pptx)"}
        for i, fmt in enumerate(formats[:3]):
            try:
                data, fname, mime = document_service.build_file(spec, fmt)
            except Exception as exc:
                st.caption(f"Could not build the {fmt.upper()} file right now ({exc.__class__.__name__}).")
                continue
            with cols[i]:
                st.download_button(label=labels.get(fmt, f"📥 Download {fmt.upper()}"), data=data, file_name=fname,
                                   mime=mime, key=f"{fmt}_dl_{transaction_idx}", use_container_width=True)
        return

    # Fallback (no spec found - e.g. an older saved thread): compile plain text directly
    clean_doc_text = raw_text.replace("[EFFIONG_TRIGGER_DOCUMENT_ASSET]::", "").strip()
    clean_doc_text = re.sub(r'\[EFFIONG_[A-Z_]+(?:::[^\]]*)?\]', '', clean_doc_text).strip()
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.download_button(label="📥 Download PDF Document", data=compile_pdf_bytes(clean_doc_text),
                           file_name="Effiong_AI_Document.pdf", mime="application/pdf",
                           key=f"pdf_dl_{transaction_idx}", use_container_width=True)
    with d_col2:
        st.download_button(label="📝 Download Word Document (.docx)", data=compile_word_bytes(clean_doc_text),
                           file_name="Effiong_AI_Document.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key=f"word_dl_{transaction_idx}", use_container_width=True)


def render_segmented_chat():
    if "master_messages" not in st.session_state:
        st.session_state.master_messages = []
    if "dictate_active" not in st.session_state:
        st.session_state.dictate_active = False
    if "ambient_active" not in st.session_state:
        st.session_state.ambient_active = False
    if "pending_attachments" not in st.session_state:
        st.session_state.pending_attachments = []          # list of {"name","bytes_b64","mime"}
    if "attachment_uploader_key" not in st.session_state:
        st.session_state.attachment_uploader_key = 0

    chat_history_container = st.container()
    with chat_history_container:
        for transaction_idx, transaction in enumerate(st.session_state.master_messages):
            if transaction.get("role") == "user":
                st.markdown(f"""
                <div style='background-color: #121620; padding: 14px; border-radius: 6px; margin-bottom: 16px; border: 1px solid #212631;'>
                    <span style='color: #D27D2D; font-weight: bold; font-size: 0.75rem; text-transform: uppercase;'>User Query</span>
                    <p style='margin: 6px 0 0 0; color: #FFFFFF; font-size: 1.05rem;'>{transaction.get('content', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                if transaction.get("attachments"):
                    names = ", ".join(a.get("name", "file") for a in transaction["attachments"])
                    st.caption(f"📎 Attached: {names}")
            else:
                raw_text = transaction.get("content", "")

                if "[EFFIONG_MEDIA_IMAGE::" in raw_text:
                    img_match = re.search(r'\[EFFIONG_MEDIA_IMAGE::(.*?)\]', raw_text)
                    if img_match:
                        try:
                            st.image(img_match.group(1), caption="🖼️ Effiong AI Synthesized Visual Asset")
                        except Exception:
                            st.caption("(the generated image could not be displayed - it may have expired)")

                if "[EFFIONG_MEDIA_VIDEO::" in raw_text or "[EFFIONG_MEDIA_ANIMATION::" in raw_text:
                    vid_match = re.search(r'\[EFFIONG_MEDIA_(?:VIDEO|ANIMATION)::(.*?)\]', raw_text)
                    if vid_match:
                        vid_ref = vid_match.group(1).strip()
                        try:
                            st.video(vid_ref)
                        except Exception:
                            st.markdown(f"""
                                <div style="margin: 10px 0; border-radius: 8px; overflow: hidden; background: #000;">
                                    <video width="100%" controls autoplay loop muted playsinline style="max-height: 480px;">
                                        <source src="{vid_ref}" type="video/mp4">
                                        Your browser does not support HTML5 video playback.
                                    </video>
                                    <div style="color: #8C9BA5; font-size: 0.75rem; padding: 4px 8px; background: #161B24;">
                                        🎞️ Effiong AI Generated Motion Video Asset
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                if "[EFFIONG_TRIGGER_DOCUMENT_ASSET]" in raw_text:
                    _render_document_downloads(raw_text, transaction_idx)

                if "[EFFIONG_TRIGGER_DOCUMENT_ASSET]" in raw_text or transaction.get("segments") or "security shield" in raw_text.lower() or "offline core isolation" in raw_text.lower():
                    if "segments" not in transaction or not transaction["segments"]:
                        transaction["segments"] = parse_ai_response_into_segments(raw_text, transaction_idx)

                    for segment_idx, chunk in enumerate(transaction["segments"]):
                        current_accent = chunk.get("accent", "#D27D2D")

                        st.markdown(f"""
                        <div style="background-color: #161B24; border-left: 3px solid {current_accent}; padding: 8px 12px; margin-top: 14px; border-radius: 2px 2px 0 0;">
                            <span style="color: {current_accent}; font-weight: bold; font-size: 0.85rem; letter-spacing: 0.5px;">{chunk['title']}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                        <div style="color: #E6EDF2; padding: 10px 14px; background-color: #0F121A; border-left: 3px solid {current_accent}; font-size: 1rem; line-height: 1.6;">
                            {chunk['content']}
                        </div>
                        """, unsafe_allow_html=True)

                        if "history" in chunk and chunk["history"]:
                            for interaction in chunk["history"]:
                                if interaction["role"] == "user":
                                    st.markdown(f"""
                                    <div style="background-color: #121620; margin: 4px 14px; padding: 8px 12px; border-left: 2px solid #8C9BA5; font-size: 0.95rem; color: #A0aec0;">
                                        <b style="color: #8C9BA5; font-size: 0.75rem;">REFINEMENT CRITIQUE:</b><br>{interaction['content']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                    <div style="background-color: #161B24; margin: 4px 14px 10px 14px; padding: 10px 12px; border-left: 2px solid {current_accent}; font-size: 0.95rem; color: #E6EDF2; line-height: 1.5;">
                                        <b style="color: {current_accent}; font-size: 0.75rem;">UPDATED STATE OUTPUT:</b><br>{interaction['content']}
                                    </div>
                                    """, unsafe_allow_html=True)

                        clean_title_no_emojis = re.sub(r'[^\w\s#]', '', chunk['title']).strip()
                        st.markdown(f'<div style="background-color: #0F121A; border-left: 3px solid {current_accent}; padding: 4px 14px 2px 14px; border-radius: 0 0 4px 4px;">', unsafe_allow_html=True)

                        form_key = f"form_segment_{chunk['id']}"
                        with st.form(key=form_key, clear_on_submit=True):
                            input_key = f"input_refine_{chunk['id']}"

                            seg_text = st.text_input(
                                label=f"Refinement Pathway Input for {chunk['id']}",
                                placeholder="Modify or reply within this specific block...",
                                key=input_key,
                                label_visibility="collapsed"
                            )

                            form_col1, form_col2 = st.columns([10, 2])
                            with form_col2:
                                submit_button = st.form_submit_button(label="Send", use_container_width=True)

                            if submit_button and seg_text:
                                process_inline_segment_refinement(seg_text, transaction_idx, segment_idx, clean_title_no_emojis, chunk['content'])

                        st.markdown('</div><div style="margin-bottom: 16px;"></div>', unsafe_allow_html=True)
                else:
                    clean_chat_text = re.sub(r'\[EFFIONG_[A-Z_]+(?:::[^\]]*)?\]', '', raw_text).replace('::', '').strip()
                    st.markdown(f"<div style='color: #E6EDF2; padding: 12px; background-color: #161B24; border-radius: 4px; margin-bottom: 12px;'>{clean_chat_text}</div>", unsafe_allow_html=True)

    st.write("---")

    synthesis_payload = ""
    if st.session_state.master_messages:
        latest_reply = st.session_state.master_messages[-1]
        if latest_reply.get("role") == "assistant":
            synthesis_payload = " ".join([block["content"] for block in latest_reply.get("segments", [])]).replace('"', '').replace("'", '').replace('\n', ' ') if latest_reply.get("segments") else latest_reply.get("content", "").replace('"', '').replace("'", '')
            synthesis_payload = re.sub(r'\[EFFIONG_[A-Z_]+(?:::[^\]]*)?\]', '', synthesis_payload).replace('::', '').strip()

    bottom_bar = st.container()

    with bottom_bar:
        st.markdown('<div class="effiong-bottom-bar-anchor"></div>', unsafe_allow_html=True)
        col_attach, col_input, col_dictate, col_voice = st.columns([0.07, 0.71, 0.11, 0.11], vertical_alignment="bottom")

        with col_attach:
            with st.popover("➕", use_container_width=True, help="Attach files, images, videos or documents"):
                st.markdown("**Send files to Effiong AI**")
                uploaded = st.file_uploader(
                    "Images, videos, documents, audio, spreadsheets, zip folders...",
                    type=UPLOAD_TYPES, accept_multiple_files=True,
                    key=f"attach_uploader_{st.session_state.attachment_uploader_key}",
                    label_visibility="collapsed",
                )
                if uploaded:
                    st.session_state.pending_attachments = [
                        {"name": uf.name, "bytes_b64": base64.b64encode(uf.getvalue()).decode("ascii"), "mime": uf.type or ""}
                        for uf in uploaded
                    ]
                if st.session_state.pending_attachments:
                    st.caption("Ready to send: " + ", ".join(a["name"] for a in st.session_state.pending_attachments))
                    if st.button("Clear attachments", use_container_width=True, key="clear_attach_btn"):
                        st.session_state.pending_attachments = []
                        st.session_state.attachment_uploader_key += 1
                        st.rerun()

        with col_input:
            master_user_input = st.chat_input("Message Effiong AI...")

        with col_dictate:
            d_active = st.session_state.dictate_active
            d_help = f"Dictate Mode: {'Active' if d_active else 'Inactive'}"

            if st.button("🎙️", key="btn_dictate", help=d_help, use_container_width=True):
                st.session_state.dictate_active = not st.session_state.dictate_active
                st.session_state.ambient_active = False
                st.rerun()

        with col_voice:
            v_active = st.session_state.ambient_active
            v_help = f"Voice Mode: {'Active' if v_active else 'Inactive'}"

            if st.button("🔊", key="btn_voice", help=v_help, use_container_width=True):
                st.session_state.ambient_active = not st.session_state.ambient_active
                st.session_state.dictate_active = False
                st.rerun()

        if st.session_state.pending_attachments:
            st.caption(f"📎 {len(st.session_state.pending_attachments)} file(s) attached to your next message")

    is_d_active = "true" if st.session_state.dictate_active else "false"
    is_v_active = "true" if st.session_state.ambient_active else "false"

    js_payload_escaped = synthesis_payload.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')

    voice_script = f"""
    <script>
    (function() {{
        const targetWindow = window.parent || window;
        const targetDoc = targetWindow.document;

        const activeDictate = {is_d_active};
        const activeVoice = {is_v_active};
        const textToRead = "{js_payload_escaped}";

        if (activeVoice && textToRead.length > 0 && targetWindow.effiongLastRead !== textToRead) {{
            targetWindow.effiongLastRead = textToRead;
            if ('speechSynthesis' in targetWindow) {{
                targetWindow.speechSynthesis.cancel();
                const msg = new SpeechSynthesisUtterance(textToRead);
                targetWindow.speechSynthesis.speak(msg);
            }}
        }}

        if (activeDictate || activeVoice) {{
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
                navigator.mediaDevices.getUserMedia({{ audio: true }})
                .then(function(stream) {{
                    const SpeechRec = targetWindow.SpeechRecognition || targetWindow.webkitSpeechRecognition;
                    if (!SpeechRec) return;

                    if (!targetWindow.effiongSpeechEngine) {{
                        targetWindow.effiongSpeechEngine = new SpeechRec();
                        targetWindow.effiongSpeechEngine.continuous = true;
                        targetWindow.effiongSpeechEngine.interimResults = true;
                        targetWindow.effiongSpeechEngine.lang = 'en-US';

                        targetWindow.effiongSpeechEngine.onresult = function(event) {{
                            let transcript = '';
                            for (let i = 0; i < event.results.length; i++) {{
                                transcript += event.results[i][0].transcript;
                            }}
                            const chatInput = targetDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                            if (chatInput && transcript.trim().length > 0) {{
                                const nativeSetter = Object.getOwnPropertyDescriptor(targetWindow.HTMLTextAreaElement.prototype, "value").set;
                                nativeSetter.call(chatInput, transcript);
                                chatInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            }}
                        }};

                        targetWindow.effiongSpeechEngine.onend = function() {{
                            if (targetWindow.effiongMicListening) {{
                                try {{ targetWindow.effiongSpeechEngine.start(); }} catch(e) {{}}
                            }}
                        }};
                    }}

                    targetWindow.effiongMicListening = true;
                    try {{ targetWindow.effiongSpeechEngine.start(); }} catch(e) {{}}
                }})
                .catch(function(err) {{
                    console.error("Microphone access denied or unpermitted:", err);
                }});
            }}
        }} else {{
            if (targetWindow.effiongSpeechEngine) {{
                targetWindow.effiongMicListening = false;
                try {{ targetWindow.effiongSpeechEngine.stop(); }} catch(e) {{}}
            }}
        }}
    }})();
    </script>
    """
    st.markdown(voice_script, unsafe_allow_html=True)

    if master_user_input:
        from src.services.brain_router import execute_sovereign_intelligence_cycle

        user_text = master_user_input or ""
        pending = st.session_state.pending_attachments
        st.session_state.pending_attachments = []
        st.session_state.attachment_uploader_key += 1

        attachments = None
        if pending:
            attachments = [file_service.ingest(a["name"], base64.b64decode(a["bytes_b64"]), a.get("mime")) for a in pending]

        user_message = {"role": "user", "content": user_text}
        if pending:
            user_message["attachments"] = [{"name": a["name"]} for a in pending]
        st.session_state.master_messages.append(user_message)
        save_chat_history_local(st.session_state.master_messages)

        status_placeholder = st.empty()
        status_stages = [
            "⚡ Analyzing Query Intent & Visual Requirements...",
            "🌐 Querying Sovereign Knowledge Data...",
            "🎨 Synthesizing Graphics, Animation, & Asset Feeds...",
            "🧠 Synthesizing Response Nodes...",
            "✨ Finalizing Output Presentation...",
        ]

        def show_stage(stage):
            status_placeholder.markdown(
                f"""
                <div style="display: flex; align-items: center; background-color: #121620; padding: 10px 14px; border-left: 3px solid #D27D2D; border-radius: 4px; margin-bottom: 12px; font-size: 0.9rem; color: #D27D2D;">
                    <div class="effiong-spinner" style="margin-right: 10px;"></div>
                    <span>{stage}</span>
                </div>
                <style>
                    .effiong-spinner {{
                        width: 14px; height: 14px;
                        border: 2px solid rgba(210, 125, 45, 0.2);
                        border-top: 2px solid #D27D2D;
                        border-radius: 50%;
                        animation: spin 0.8s linear infinite;
                    }}
                    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                </style>
                """,
                unsafe_allow_html=True,
            )

        show_stage(status_stages[0])
        for stage in status_stages[1:]:
            time.sleep(0.15)
            show_stage(stage)

        live_matrix_response = execute_sovereign_intelligence_cycle(
            user_text or "(please look at the attached file(s))",
            st.session_state.master_messages[:-1],
            attachments=attachments,
            on_status=show_stage,
        )

        status_placeholder.empty()

        message_index = len(st.session_state.master_messages)
        extracted_segments = parse_ai_response_into_segments(live_matrix_response, message_index)

        st.session_state.master_messages.append({
            "role": "assistant",
            "content": live_matrix_response,
            "segments": extracted_segments
        })

        save_chat_history_local(st.session_state.master_messages)
        st.rerun()
