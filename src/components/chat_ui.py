import streamlit as st
import streamlit.components.v1 as components

from typing import Dict
from typing import List
from typing import Optional

from datetime import datetime
import html
import uuid


# ==========================================================
# UI CONFIG
# ==========================================================

SEGMENT_BORDER = "#D27D2D"
CARD_BACKGROUND = "#161B24"
CARD_BORDER = "#212631"

TEXT_PRIMARY = "#E6EDF2"
TEXT_SECONDARY = "#8B949E"


# ==========================================================
# SAFE HTML
# ==========================================================

def safe_text(text: str) -> str:

    if not text:
        return ""

    return html.escape(str(text))


# ==========================================================
# BADGE COMPONENT
# ==========================================================

def render_badge(
    label: str,
    color: str = "#D27D2D"
):

    st.markdown(
        f"""
        <span style="
            background:{color}20;
            color:{color};
            border:1px solid {color};
            border-radius:999px;
            padding:2px 8px;
            font-size:0.7rem;
            font-weight:600;
        ">
            {safe_text(label)}
        </span>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# SECTION HEADER
# ==========================================================

def render_section_header(
    title: str
):

    st.markdown(
        f"""
        <div style="
            margin-top:25px;
            margin-bottom:10px;
            color:{TEXT_SECONDARY};
            font-size:0.75rem;
            font-weight:700;
            text-transform:uppercase;
            letter-spacing:0.08em;
        ">
            {safe_text(title)}
        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# GENERIC CARD
# ==========================================================

def render_card(
    title: str,
    content: str
):

    st.markdown(
        f"""
        <div style="
            background:{CARD_BACKGROUND};
            border:1px solid {CARD_BORDER};
            border-radius:8px;
            padding:16px;
            margin-bottom:12px;
        ">
            <div style="
                color:{TEXT_SECONDARY};
                font-size:0.75rem;
                margin-bottom:8px;
            ">
                {safe_text(title)}
            </div>

            <div style="
                color:{TEXT_PRIMARY};
                line-height:1.6;
            ">
                {safe_text(content)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# COLLAPSIBLE CARD
# ==========================================================

def render_expandable_card(
    title: str,
    content: str
):

    with st.expander(title):

        st.write(content)

# ==========================================================
# SEGMENT HEADER GENERATOR
# ==========================================================

def get_segment_title(
    segment_type: str,
    index: int
):

    if segment_type == "question":

        return (
            f"❓ Sovereign Inquiry Node #{index}"
        )

    elif segment_type == "instruction":

        return (
            f"🛠 Executive Action Node #{index}"
        )

    elif segment_type == "prediction":

        return (
            f"🔮 Prediction Node #{index}"
        )

    return (
        f"⚡ Context Resolution Node #{index}"
    )


# ==========================================================
# RESPONSE SEGMENT PARSER
# ==========================================================

def parse_response_segments(
    response_text: str,
    message_index: int
):

    segments = []

    lines = [
        line.strip()
        for line in response_text.split("\n")
        if line.strip()
    ]

    segment_count = 0

    for line in lines:

        if line.endswith("?"):

            seg_type = "question"

        elif (
            line.startswith("-")
            or line.startswith("•")
            or line.startswith("1.")
        ):

            seg_type = "instruction"

        else:

            seg_type = "answer"

        segment_count += 1

        segments.append({

            "id":
                f"{message_index}_{segment_count}",

            "type":
                seg_type,

            "title":
                get_segment_title(
                    seg_type,
                    segment_count
                ),

            "content":
                line
        })

    return segments


# ==========================================================
# SINGLE SEGMENT RENDERER
# ==========================================================

def render_text_segment(
    segment: Dict
):

    st.markdown(
        f"""
        <div class="segmented-response-box">
            <div class="segment-header">
                {safe_text(segment['title'])}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div style="
            color:{TEXT_PRIMARY};
            line-height:1.7;
            margin-bottom:15px;
        ">
            {safe_text(segment['content'])}
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================================================
# PDF RENDERING ENGINE
# ==========================================================

def render_pdf_segment(
    segment: Dict
):
    """
    Expected Structure

    {
        "type":"pdf",
        "title":"Research Report",
        "file_name":"report.pdf",
        "file_bytes":pdf_bytes
    }
    """

    render_section_header(
        "Generated PDF Asset"
    )

    st.markdown(
        f"""
        <div style="
            background:{CARD_BACKGROUND};
            border:1px solid {CARD_BORDER};
            border-radius:8px;
            padding:16px;
            margin-bottom:12px;
        ">
            <div style="
                color:{TEXT_PRIMARY};
                font-weight:600;
                margin-bottom:8px;
            ">
                📄 {safe_text(segment.get('title','PDF Report'))}
            </div>

            <div style="
                color:{TEXT_SECONDARY};
                font-size:0.85rem;
            ">
                Download or preview this generated report.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if segment.get("file_bytes"):

        st.download_button(
            label="📥 Download PDF",
            data=segment["file_bytes"],
            file_name=segment.get(
                "file_name",
                "report.pdf"
            ),
            mime="application/pdf",
            use_container_width=True
        )


# ==========================================================
# DOCUMENT NODE
# ==========================================================

def render_document_segment(
    segment: Dict
):

    render_section_header(
        "Generated Document"
    )

    filename = segment.get(
        "file_name",
        "document.txt"
    )

    content = segment.get(
        "content",
        ""
    )

    render_card(
        filename,
        "Document generated successfully."
    )

    st.download_button(
        label="📥 Download Document",
        data=content,
        file_name=filename,
        use_container_width=True
    )


# ==========================================================
# IMAGE NODE
# ==========================================================

def render_image_segment(
    segment: Dict
):
    """
    Structure

    {
        "type":"image",
        "content": image_bytes_or_url,
        "caption":"..."
    }
    """

    render_section_header(
        "Generated Image Asset"
    )

    image_data = segment.get("content")

    if image_data:

        st.image(
            image_data,
            use_container_width=True
        )

    if segment.get("caption"):

        st.caption(
            segment["caption"]
        )


# ==========================================================
# MULTI IMAGE GALLERY
# ==========================================================

def render_image_gallery(
    segment: Dict
):
    """
    Structure

    {
        "type":"gallery",
        "images":[...]
    }
    """

    render_section_header(
        "Image Gallery"
    )

    images = segment.get(
        "images",
        []
    )

    if not images:
        return

    cols = st.columns(
        min(3, len(images))
    )

    for idx, img in enumerate(images):

        with cols[idx % len(cols)]:

            st.image(
                img,
                use_container_width=True
            )


# ==========================================================
# VIDEO NODE
# ==========================================================

def render_video_segment(
    segment: Dict
):
    """
    Structure

    {
        "type":"video",
        "content":video_url_or_bytes,
        "caption":"..."
    }
    """

    render_section_header(
        "Generated Video Asset"
    )

    video_data = segment.get(
        "content"
    )

    if video_data:

        st.video(
            video_data
        )

    if segment.get("caption"):

        st.caption(
            segment["caption"]
        )


# ==========================================================
# AUDIO NODE
# ==========================================================

def render_audio_segment(
    segment: Dict
):

    render_section_header(
        "Generated Audio Asset"
    )

    audio_data = segment.get(
        "content"
    )

    if audio_data:

        st.audio(
            audio_data
        )


# ==========================================================
# RESEARCH REPORT NODE
# ==========================================================

def render_research_report_segment(
    segment: Dict
):

    render_section_header(
        "Research Report"
    )

    report_title = segment.get(
        "title",
        "Research Report"
    )

    report_content = segment.get(
        "content",
        ""
    )

    render_expandable_card(
        report_title,
        report_content
    )


# ==========================================================
# SOURCE PANEL
# ==========================================================

def render_sources_panel(
    sources: List[Dict]
):

    if not sources:
        return

    render_section_header(
        "Sources"
    )

    for source in sources:

        title = source.get(
            "title",
            "Source"
        )

        source_type = source.get(
            "type",
            "reference"
        )

        url = source.get(
            "url",
            ""
        )

        st.markdown(
            f"""
            <div style="
                background:{CARD_BACKGROUND};
                border:1px solid {CARD_BORDER};
                border-radius:8px;
                padding:12px;
                margin-bottom:8px;
            ">
                <div style="
                    color:{TEXT_PRIMARY};
                    font-weight:600;
                ">
                    {safe_text(title)}
                </div>

                <div style="
                    color:{TEXT_SECONDARY};
                    font-size:0.8rem;
                    margin-top:4px;
                ">
                    {safe_text(source_type)}
                </div>

                <div style="
                    margin-top:6px;
                ">
                    <a href="{url}" target="_blank">
                        Open Source
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==========================================================
# UNIVERSAL MULTIMEDIA ROUTER
# ==========================================================

def render_multimedia_segment(
    segment: Dict
):

    seg_type = segment.get(
        "type",
        "text"
    )

    if seg_type == "pdf":

        render_pdf_segment(
            segment
        )

    elif seg_type == "document":

        render_document_segment(
            segment
        )

    elif seg_type == "image":

        render_image_segment(
            segment
        )

    elif seg_type == "gallery":

        render_image_gallery(
            segment
        )

    elif seg_type == "video":

        render_video_segment(
            segment
        )

    elif seg_type == "audio":

        render_audio_segment(
            segment
        )

    elif seg_type == "research_report":

        render_research_report_segment(
            segment
        )

    else:

        render_text_segment(
            segment
        )

# ==========================================================
# TRUTH MATRIX PANEL
# ==========================================================

def render_truth_matrix(
    truth_matrix: Dict
):

    if not truth_matrix:
        return

    render_section_header(
        "Truth Matrix Analysis"
    )

    classification = truth_matrix.get(
        "classification",
        "UNKNOWN"
    )

    score = truth_matrix.get(
        "score",
        0
    )

    fact_layer = truth_matrix.get(
        "fact_layer",
        ""
    )

    speculation_layer = truth_matrix.get(
        "speculation_layer",
        ""
    )

    warning = truth_matrix.get(
        "warning",
        ""
    )

    st.markdown(
        f"""
        <div style="
            background:{CARD_BACKGROUND};
            border:1px solid {CARD_BORDER};
            border-radius:10px;
            padding:18px;
            margin-bottom:15px;
        ">
            <div style="
                font-size:1rem;
                font-weight:700;
                color:#D27D2D;
                margin-bottom:10px;
            ">
                Truth Classification
            </div>

            <div style="
                color:{TEXT_PRIMARY};
                margin-bottom:8px;
            ">
                <b>{safe_text(classification)}</b>
            </div>

            <div style="
                color:{TEXT_SECONDARY};
                margin-bottom:15px;
            ">
                Confidence Score: {score}/100
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    render_card(
        "Fact Layer",
        fact_layer
    )

    render_card(
        "Speculation Layer",
        speculation_layer
    )

    render_card(
        "Verification Notice",
        warning
    )


# ==========================================================
# EVIDENCE PANEL
# ==========================================================

def render_evidence_panel(
    evidence_data: Dict
):

    if not evidence_data:
        return

    render_section_header(
        "Evidence Assessment"
    )

    score = evidence_data.get(
        "score",
        0
    )

    source_count = evidence_data.get(
        "source_count",
        0
    )

    evidence_count = evidence_data.get(
        "evidence_count",
        0
    )

    st.metric(
        "Evidence Score",
        score
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Sources",
            source_count
        )

    with col2:
        st.metric(
            "Evidence Items",
            evidence_count
        )


# ==========================================================
# PREDICTION PANEL
# ==========================================================

def render_prediction_panel(
    prediction: Dict
):

    if not prediction:
        return

    render_section_header(
        "Prediction Analysis"
    )

    topic = prediction.get(
        "topic",
        "Unknown Topic"
    )

    confidence = prediction.get(
        "confidence",
        0
    )

    uncertainty = prediction.get(
        "uncertainty",
        "UNKNOWN"
    )

    forecast = prediction.get(
        "forecast",
        ""
    )

    disclaimer = prediction.get(
        "disclaimer",
        ""
    )

    st.markdown(
        f"""
        <div style="
            background:{CARD_BACKGROUND};
            border-left:4px solid #D27D2D;
            border-radius:8px;
            padding:16px;
            margin-bottom:15px;
        ">
            <div style="
                color:#D27D2D;
                font-weight:700;
                margin-bottom:8px;
            ">
                🔮 {safe_text(topic)}
            </div>

            <div style="
                color:{TEXT_PRIMARY};
            ">
                Confidence: {confidence}%
            </div>

            <div style="
                color:{TEXT_SECONDARY};
                margin-top:6px;
            ">
                {safe_text(uncertainty)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    render_card(
        "Forecast",
        forecast
    )

    render_card(
        "Forecast Disclaimer",
        disclaimer
    )


# ==========================================================
# RESEARCH FINDINGS PANEL
# ==========================================================

def render_research_panel(
    research_data: Dict
):

    if not research_data:
        return

    render_section_header(
        "Research Findings"
    )

    summary = research_data.get(
        "summary",
        ""
    )

    findings = research_data.get(
        "findings",
        []
    )

    render_card(
        "Research Summary",
        summary
    )

    if findings:

        for idx, finding in enumerate(findings):

            render_card(
                f"Finding #{idx+1}",
                str(finding)
            )


# ==========================================================
# REPOSITORY RESULTS PANEL
# ==========================================================

def render_repository_panel(
    repository_results: List[Dict]
):

    if not repository_results:
        return

    render_section_header(
        "Repository Intelligence"
    )

    for repo in repository_results:

        title = repo.get(
            "title",
            "Repository Result"
        )

        content = repo.get(
            "content",
            ""
        )

        source = repo.get(
            "source",
            "Unknown"
        )

        st.markdown(
            f"""
            <div style="
                background:{CARD_BACKGROUND};
                border:1px solid {CARD_BORDER};
                border-radius:8px;
                padding:14px;
                margin-bottom:10px;
            ">
                <div style="
                    color:#D27D2D;
                    font-weight:600;
                    margin-bottom:4px;
                ">
                    {safe_text(title)}
                </div>

                <div style="
                    color:{TEXT_SECONDARY};
                    font-size:0.75rem;
                    margin-bottom:8px;
                ">
                    Source: {safe_text(source)}
                </div>

                <div style="
                    color:{TEXT_PRIMARY};
                    line-height:1.5;
                ">
                    {safe_text(content[:800])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==========================================================
# HERITAGE VERIFICATION PANEL
# ==========================================================

def render_heritage_panel(
    heritage_data: Dict
):

    if not heritage_data:
        return

    render_section_header(
        "Heritage Verification"
    )

    title = heritage_data.get(
        "title",
        "Unknown Node"
    )

    status = heritage_data.get(
        "status",
        "PENDING"
    )

    reviewed = heritage_data.get(
        "reviewed",
        ""
    )

    status_color = (
        "#2EA043"
        if "FACT" in status.upper()
        else "#D27D2D"
    )

    st.markdown(
        f"""
        <div style="
            background:{CARD_BACKGROUND};
            border:1px solid {CARD_BORDER};
            border-radius:10px;
            padding:16px;
            margin-bottom:12px;
        ">
            <div style="
                color:{TEXT_PRIMARY};
                font-weight:700;
                margin-bottom:8px;
            ">
                {safe_text(title)}
            </div>

            <div style="
                color:{status_color};
                font-weight:600;
                margin-bottom:5px;
            ">
                {safe_text(status)}
            </div>

            <div style="
                color:{TEXT_SECONDARY};
                font-size:0.8rem;
            ">
                Reviewed: {safe_text(reviewed)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================================
# KNOWLEDGE GRAPH PREVIEW PANEL
# ==========================================================

def render_knowledge_graph_panel(
    graph_data: Dict
):

    if not graph_data:
        return

    render_section_header(
        "Knowledge Graph Preview"
    )

    node_count = graph_data.get(
        "nodes",
        0
    )

    edge_count = graph_data.get(
        "edges",
        0
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Nodes",
            node_count
        )

    with col2:
        st.metric(
            "Edges",
            edge_count
        )

    st.info(
        "Future Sovereign Knowledge Graph Visualization Layer"
    )

# ==========================================================
# AGENT EXECUTION PANEL
# ==========================================================

def render_agent_report_panel(
    agent_report: Dict
):

    if not agent_report:
        return

    render_section_header(
        "Agent Activity Report"
    )

    agent_count = agent_report.get(
        "agent_count",
        0
    )

    st.metric(
        "Agents Executed",
        agent_count
    )

    results = agent_report.get(
        "results",
        []
    )

    for result in results:

        agent_name = result.get(
            "agent",
            "unknown"
        )

        status = result.get(
            "status",
            "unknown"
        )

        st.markdown(
            f"""
            <div style="
                background:{CARD_BACKGROUND};
                border:1px solid {CARD_BORDER};
                border-radius:8px;
                padding:12px;
                margin-bottom:8px;
            ">
                <div style="
                    color:#D27D2D;
                    font-weight:600;
                ">
                    {safe_text(agent_name)}
                </div>

                <div style="
                    color:{TEXT_SECONDARY};
                ">
                    Status: {safe_text(status)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==========================================================
# OPERATOR TELEMETRY
# ==========================================================

def render_operator_panel():

    telemetry = st.session_state.get(
        "operator_telemetry",
        {}
    )

    render_section_header(
        "Operator Control Center"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Messages",
            telemetry.get(
                "messages",
                0
            )
        )

    with col2:

        st.metric(
            "Repositories",
            telemetry.get(
                "repositories",
                0
            )
        )

    with col3:

        st.metric(
            "Models",
            telemetry.get(
                "models",
                0
            )
        )

    with col4:

        st.metric(
            "Agents",
            telemetry.get(
                "agents",
                0
            )
        )


# ==========================================================
# BRAIN ROUTE PANEL
# ==========================================================

def render_route_panel():

    route = st.session_state.get(
        "last_model_route",
        "Unknown"
    )

    render_section_header(
        "Model Route"
    )

    render_card(
        "Active Brain",
        route
    )


# ==========================================================
# MEMORY PANEL
# ==========================================================

def render_memory_panel():

    total_messages = len(
        st.session_state.get(
            "master_messages",
            []
        )
    )

    render_section_header(
        "Memory Layer"
    )

    st.metric(
        "Stored Messages",
        total_messages
    )


# ==========================================================
# THREAD RENDERER
# ==========================================================

def render_segment_thread(
    segment_id: str
):

    if segment_id not in st.session_state.segment_threads:

        st.session_state.segment_threads[
            segment_id
        ] = []

    for item in st.session_state.segment_threads[
        segment_id
    ]:

        role = item.get(
            "role",
            ""
        )

        content = item.get(
            "content",
            ""
        )

        if role == "user":

            st.markdown(
                f"""
                <div style="
                    margin-left:20px;
                    border-left:2px solid #D27D2D;
                    padding-left:10px;
                    margin-top:8px;
                ">
                    <b>You:</b>
                    {safe_text(content)}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div style="
                    margin-left:20px;
                    border-left:2px solid #8B949E;
                    padding-left:10px;
                    margin-top:8px;
                ">
                    <b>Effiong AI:</b>
                    {safe_text(content)}
                </div>
                """,
                unsafe_allow_html=True
            )


# ==========================================================
# THREAD INPUT
# ==========================================================

def render_thread_input(
    segment_id: str
):

    with st.form(
        key=f"thread_form_{segment_id}",
        clear_on_submit=True
    ):

        thread_text = st.text_input(
            "Branch discussion",
            key=f"thread_{segment_id}",
            label_visibility="collapsed"
        )

        submitted = st.form_submit_button(
            "Branch"
        )

        if submitted and thread_text:

            st.session_state.segment_threads[
                segment_id
            ].append({

                "role":
                    "user",

                "content":
                    thread_text
            })

            st.session_state.segment_threads[
                segment_id
            ].append({

                "role":
                    "assistant",

                "content":
                    (
                        "Branch processing "
                        "placeholder."
                    )
            })

            st.rerun()


# ==========================================================
# COMPLETE MESSAGE RENDERER
# ==========================================================

def render_message(
    message: Dict,
    message_index: int
):

    if message["role"] == "user":

        st.markdown(
            f"""
            <div style="
                background:#121620;
                border:1px solid {CARD_BORDER};
                border-radius:8px;
                padding:15px;
                margin-bottom:20px;
            ">
                <b>User Query</b>
                <br><br>
                {safe_text(message['content'])}
            </div>
            """,
            unsafe_allow_html=True
        )

        return

    segments = message.get(
        "segments",
        []
    )

    for segment in segments:

        seg_id = segment["id"]

        seg_type = segment.get(
            "type",
            "text"
        )

        if seg_type == "text":

            render_text_segment(
                segment
            )

        else:

            render_multimedia_segment(
                segment
            )

        render_segment_thread(
            seg_id
        )

        render_thread_input(
            seg_id
        )


# ==========================================================
# CHAT HISTORY RENDERER
# ==========================================================

def render_chat_history():

    messages = st.session_state.get(
        "master_messages",
        []
    )

    if not messages:

        st.markdown(
            """
            <div class="landing-hero">
                <div class="landing-title">
                    🐆 Effiong AI
                </div>

                <div class="landing-caption">
                    Sovereign Wisdom Engine
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        return

    for idx, msg in enumerate(messages):

        render_message(
            msg,
            idx
        )


# ==========================================================
# MAIN CHAT LOOP
# ==========================================================

def render_segmented_chat():

    render_operator_panel()

    render_route_panel()

    render_memory_panel()

    st.write("")

    render_chat_history()

    st.write("---")

    user_input = st.chat_input(
        "Message Effiong AI..."
    )

    if user_input:

        st.session_state.master_messages.append({

            "role":
                "user",

            "content":
                user_input
        })

        from src.services.brain_router import (
            execute_sovereign_intelligence_cycle
        )

        with st.spinner(
            "Synchronizing Intelligence Layers..."
        ):

            response = (
                execute_sovereign_intelligence_cycle(
                    user_input
                )
            )

        msg_index = len(
            st.session_state.master_messages
        )

        parsed_segments = (
            parse_response_segments(
                response,
                msg_index
            )
        )

        st.session_state.master_messages.append({

            "role":
                "assistant",

            "segments":
                parsed_segments
        })

        st.rerun()