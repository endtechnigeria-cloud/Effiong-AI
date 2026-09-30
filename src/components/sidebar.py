
import streamlit as st

from src.core.guard import ExecutionBudget
from src.database.archive import chat_archive, heritage_archive
from src.database.heritage_store import HeritageStore
from src.services.archive_publisher import archive_publisher
from src.services.verification_service import VerificationService

_verification_service = VerificationService()


def _get_store() -> HeritageStore:
    if "heritage_store" not in st.session_state:
        st.session_state.heritage_store = HeritageStore(heritage_archive.load_from_remote_if_empty())
    return st.session_state.heritage_store


def render_effiong_sidebar():
    # Insert anchor marker for parent document selector
    st.markdown('<div id="effiong-sidebar-anchor"></div>', unsafe_allow_html=True)

    if "sidebar_view" not in st.session_state:
        st.session_state.sidebar_view = "heritage"

    store = _get_store()

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
                evidence_url = st.text_input("Evidence link (optional)", placeholder="https://... a source that backs this up")
                uploaded_proof = st.file_uploader("Evidence Asset", accept_multiple_files=False, key="sb_file_uploader")

                submit = st.form_submit_button("Log into Effiong Core", use_container_width=True)

                if submit and title:
                    evidence_files = []
                    if uploaded_proof is not None:
                        from src.services.file_service import file_service

                        att = file_service.ingest(uploaded_proof.name, uploaded_proof.getvalue(), uploaded_proof.type)
                        evidence_files.append(att.meta())
                    with st.spinner("Checking evidence across the web and open repositories..."):
                        try:
                            verification = _verification_service.verify_claim(
                                title=title, narrative=details or "", verification_class=proof_type,
                                evidence_urls=[evidence_url] if evidence_url else [], evidence_files=evidence_files,
                                budget=ExecutionBudget(deadline_seconds=45),
                            )
                        except Exception as exc:
                            verification = {}
                            st.warning(f"Automatic verification couldn't complete ({exc.__class__.__name__}) - logged as pending.")
                    node = store.create_node(title=title, description=details or "", verification_class=proof_type,
                                             evidence_url=evidence_url, verification=verification, evidence_files=evidence_files)
                    heritage_archive.save(store.get_all_nodes())
                    st.session_state["_last_logged_node_id"] = node["id"]
                    st.success(f"Archive Node Indexed as **{node['status']}** ({node['id']})")
                    st.rerun()

            st.markdown("<div style='margin-top: 20px; border-top: 1px solid #212631; padding-top: 15px;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='color: #8B949E; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px;'>Integrity Ledger</p>", unsafe_allow_html=True)

            nodes = store.get_all_nodes()
            if nodes:
                stats = store.get_statistics()
                st.caption(f"{stats['total_nodes']} record(s) . {stats['verified_nodes']} verified . {stats['pending_nodes']} pending")
                for log in reversed(nodes[-25:]):
                    status_color = "#2EA043" if log["status"] == "Verified" else ("#E74C3C" if log["status"] == "Disputed" else "#D27D2D")
                    status_bg = "#132316" if log["status"] == "Verified" else ("#2A1416" if log["status"] == "Disputed" else "#211A12")

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
                    cols = st.columns(2)
                    with cols[0]:
                        if st.button("📄 Report", key=f"rep_{log['id']}", use_container_width=True):
                            st.session_state[f"_show_report_{log['id']}"] = True
                    with cols[1]:
                        if st.button("🌍 Archive", key=f"arc_{log['id']}", use_container_width=True):
                            with st.spinner("Publishing to Wayback / Zenodo / OSF / Figshare / Wikimedia..."):
                                receipts = archive_publisher.publish(log)
                            store.add_archive_receipts(log["id"], receipts)
                            heritage_archive.save(store.get_all_nodes())
                            ok = [r["service"] for r in receipts if r["status"] in ("published", "draft")]
                            st.info("Archived to: " + (", ".join(ok) if ok else "no service returned success - see receipts"))
                    if st.session_state.get(f"_show_report_{log['id']}"):
                        from src.utilities import doc_engine

                        report_md = HeritageStore.record_markdown(log)
                        st.download_button("📥 Download record PDF", data=doc_engine.compile_pdf_bytes(report_md, doc_type="African Heritage Record"),
                                           file_name=f"{log['id']}.pdf", mime="application/pdf", key=f"dl_{log['id']}", use_container_width=True)
            else:
                st.markdown("<p style='color: #8B949E; font-size: 0.8rem; font-style: italic;'>No archive nodes logged yet.</p>", unsafe_allow_html=True)

        # TAB B: Active Chat History Archive View (With New Chat Action Component)
        elif st.session_state.sidebar_view == "history":
            if st.button("➕ New Chat Session", use_container_width=True, type="secondary"):
                st.session_state.master_messages = []
                st.session_state.segment_threads = {}
                st.session_state.last_spoken_trigger = None
                st.session_state.active_thread_id = chat_archive.new_thread_id()
                st.success("New chat initialized.")
                st.rerun()

            st.markdown("<div style='margin-bottom: 15px; border-bottom: 1px solid #212631; padding-bottom: 5px;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='color: #D27D2D; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;'>Active Chat History</p>", unsafe_allow_html=True)

            threads = chat_archive.list_threads()
            if threads:
                for t in threads[:30]:
                    is_current = t["id"] == st.session_state.get("active_thread_id")
                    label = ("💬 " if not is_current else "🟢 ") + (t["title"] or "Untitled")
                    if st.button(label[:44], key=f"thread_{t['id']}", use_container_width=True):
                        loaded = chat_archive.load_thread(t["id"])
                        if loaded:
                            st.session_state.master_messages = loaded.get("messages", [])
                            st.session_state.active_thread_id = t["id"]
                            st.rerun()
            else:
                st.markdown("<p style='color: #8B949E; font-size: 0.8rem; font-style: italic;'>No active chat history threads.</p>", unsafe_allow_html=True)

        # Fixed Infrastructure Footer Layout
        st.markdown("""
        <div style='margin-top: 30px; border-top: 1px solid #212631; padding-top: 12px; text-align: center; color: #8B949E; font-size: 0.65rem; letter-spacing: 0.05em;'>
            EFFIONG ENGINE v3.0.0<br>
            <span style='color: #D27D2D;'>•</span> Secure Sandbox Active <span style='color: #D27D2D;'>•</span>
        </div>
        """, unsafe_allow_html=True)
