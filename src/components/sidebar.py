import streamlit as st

def render_effiong_sidebar():
    if "sidebar_view" not in st.session_state:
        st.session_state.sidebar_view = "heritage"

    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 10px 0 15px 0; margin-bottom: 15px;'>
            <span style='font-size: 1.8rem;'>🐆</span>
            <h1 style='color: #FFFFFF; font-family: "Comfortaa", cursive; font-size: 1.4rem; margin: 5px 0 2px 0; font-weight: 700; letter-spacing: 0.05em;'>EFFIONG AI</h1>
            <p style='color: #8B949E; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; margin: 0;'>Sovereign Wisdom Engine</p>
        </div>
        """, unsafe_allow_html=True)

        # Dual-Tabs Control Splitter
        col1, col2 = st.columns(2)
        with col1:
            h_active = st.session_state.sidebar_view == "heritage"
            if st.button("📚 Heritage", use_container_width=True, type="primary" if h_active else "secondary", key="sb_tab_heritage"):
                st.session_state.sidebar_view = "heritage"
                st.rerun()
        with col2:
            c_active = st.session_state.sidebar_view == "history"
            if st.button("📜 History", use_container_width=True, type="primary" if c_active else "secondary", key="sb_tab_history"):
                st.session_state.sidebar_view = "history"
                st.rerun()

        st.markdown("<div style='margin-bottom: 20px; border-bottom: 1px solid #212631; padding-bottom: 10px;'></div>", unsafe_allow_html=True)

        # TAB A: African Heritage Menu View
        if st.session_state.sidebar_view == "heritage":
            st.markdown("<p style='color: #D27D2D; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;'>Log Historical Node</p>", unsafe_allow_html=True)
            
            with st.form("sidebar_heritage_form", clear_on_submit=True):
                title = st.text_input("Archive Node Title", placeholder="e.g., Kingdom of Benin records")
                details = st.text_area("Narrative Text Description", placeholder="Transcribe history parameters here...")
                proof_type = st.selectbox("Verification Class", ["Oral Tradition Transcript", "Archaeological Records", "Media Frame proof"])
                uploaded_proof = st.file_uploader("Evidence Asset", accept_multiple_files=False, key="sb_file_uploader")
                
                submit = st.form_submit_button("Log into Effiong Core", use_container_width=True)
                
                if submit and title:
                    node_type = "Fact Node" if "Oral" not in proof_type else "Oral Track Node"
                    st.session_state.heritage_logs.append({
                        "id": f"NODE-00{len(st.session_state.heritage_logs)+1}",
                        "title": title,
                        "type": node_type,
                        "status": "Verified" if "Oral" not in proof_type else "Pending Verification"
                    })
                    st.success("Archive Node Indexed!")
                    st.rerun()

            st.markdown("<div style='margin-top: 20px; border-top: 1px solid #212631; padding-top: 15px;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='color: #8B949E; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px;'>Integrity Ledger</p>", unsafe_allow_html=True)
            
            if "heritage_logs" in st.session_state and st.session_state.heritage_logs:
                for log in st.session_state.heritage_logs:
                    status_color = "#2EA043" if log["status"] == "Verified" else "#D27D2D"
                    status_bg = "#132316" if log["status"] == "Verified" else "#211A12"
                    
                    st.markdown(f"""
                    <div style='background-color: #161B24; border: 1px solid #212631; padding: 10px; border-radius: 6px; margin-bottom: 8px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>
                            <span style='color: #8B949E; font-size: 0.65rem; font-family: monospace;'>{log['id']}</span>
                            <span style='color: {status_color}; background-color: {status_bg}; font-size: 0.6rem; font-weight: 600; padding: 1px 5px; border-radius: 8px; border: 1px solid {status_color}40;'>{log['status']}</span>
                        </div>
                        <div style='color: #E6EDF2; font-size: 0.8rem; font-weight: 500; line-height: 1.3;'>{log['title']}</div>
                        <div style='color: #8B949E; font-size: 0.7rem; margin-top: 2px;'>{log['type']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # TAB B: Active Chat History Archive View (With New Chat Action Component)
        elif st.session_state.sidebar_view == "history":
            # Action Anchor: Initialize a completely fresh thread canvas clean slate
            if st.button("➕ New Chat Session", use_container_width=True, type="secondary"):
                st.session_state.master_messages = []
                st.session_state.segment_threads = {}
                st.session_state.last_spoken_trigger = None
                st.success("New chat initialized.")
                st.rerun()
                
            st.markdown("<div style='margin-bottom: 15px; border-bottom: 1px solid #212631; padding-bottom: 5px;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='color: #D27D2D; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;'>Active Chat History</p>", unsafe_allow_html=True)
            
            if "master_messages" in st.session_state and st.session_state.master_messages:
                user_prompts = [m["content"] for m in st.session_state.master_messages if m["role"] == "user"]
                
                if user_prompts:
                    for i, prompt in enumerate(user_prompts):
                        snippet = prompt if len(prompt) < 32 else f"{prompt[:30]}..."
                        st.markdown(f"""
                        <div style='background-color: #161B24; border: 1px solid #212631; padding: 12px; border-radius: 6px; margin-bottom: 8px;'>
                          <div style='color: #8B949E; font-size: 0.65rem; margin-bottom: 2px;'>Session Thread #{i+1}</div>
                          <div style='color: #F0F6FC; font-size: 0.85rem; font-weight: 500;'>💬 {snippet}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #8B949E; font-size: 0.8rem; font-style: italic;'>No chat history items compiled.</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #8B949E; font-size: 0.8rem; font-style: italic;'>No active chat history threads.</p>", unsafe_allow_html=True)

        # Fixed Infrastructure Footer Layout
        st.markdown("""
        <div style='margin-top: 30px; border-top: 1px solid #212631; padding-top: 12px; text-align: center; color: #8B949E; font-size: 0.65rem; letter-spacing: 0.05em;'>
            EFFIONG ENGINE v2.4.0<br>
            <span style='color: #D27D2D;'>•</span> Secure Sandbox Active <span style='color: #D27D2D;'>•</span>
        </div>
        """, unsafe_allow_html=True)