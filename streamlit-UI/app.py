"""Streamlit UI for the local Network Security Tutor & Quiz Bot.

Presentation-only changes. Backend functions are called as provided by the team.
"""
from pathlib import Path
from html import escape

import requests
import streamlit as st
from backend import agents, core

st.set_page_config(page_title="StudyShield | Network Security Tutor", page_icon="🛡️", layout="wide")

css_file = Path(__file__).with_name("style.css")
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def hero(title: str, description: str) -> None:
    st.markdown(
        f'<div class="hero"><h2>{escape(title)}</h2><p>{escape(description)}</p></div>',
        unsafe_allow_html=True,
    )


def sources_panel(sources: dict, tags=None) -> None:
    tags = tags if tags is not None else list(sources)
    if not tags:
        return
    with st.expander(f"📚 View sources ({len(tags)})"):
        for tag in tags:
            item = sources.get(tag)
            if item:
                st.markdown(f"**[{tag}] {item.get('name', 'Unknown')}** — {item.get('locator', '')}")
                st.caption(item.get("excerpt", ""))


# Navigation uses actual buttons, not radio controls.
PAGES = [
    ("Q&A Tutor", "☏"),
    ("Quiz Agent", "☷"),
    ("Course Documents", "▱"),
    ("Security & Integrity", "♢"),
]
if "active_page" not in st.session_state:
    st.session_state.active_page = "Q&A Tutor"

with st.sidebar:
    st.markdown(
        '<div class="ui-brand"><span class="ui-brand-mark">◉</span>'
        '<div><div class="ui-brand-name">Network Security<br>Tutor</div>'
        '<div class="ui-brand-caption">STUDY WORKSPACE</div></div></div>',
        unsafe_allow_html=True,
    )
    for label, glyph in PAGES:
        selected = st.session_state.active_page == label
        if st.button(
            f"{glyph}   {label}",
            key=f"nav_{label}",
            use_container_width=True,
            type="primary" if selected else "secondary",
        ):
            st.session_state.active_page = label
            st.rerun()
    st.divider()
    st.markdown('<div class="ui-section">COURSE</div>', unsafe_allow_html=True)
    st.markdown('<div class="ui-course">♧ &nbsp; CS5342: Network Security</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="ui-section">SYSTEM</div>', unsafe_allow_html=True)
    try:
        response = requests.get(core.OLLAMA + "/api/tags", timeout=2)
        response.raise_for_status()
        st.markdown('<div class="ui-status">● &nbsp; AI Engine Online</div>', unsafe_allow_html=True)
    except requests.RequestException:
        st.markdown('<div class="ui-status offline">● &nbsp; Ollama unavailable</div>', unsafe_allow_html=True)
    st.markdown('<div class="ui-subtle">Local Ollama<br>Private · Local-first</div>', unsafe_allow_html=True)

page = st.session_state.active_page

if page == "Q&A Tutor":
    st.markdown('<div class="qa-page-marker"></div>', unsafe_allow_html=True)
    hero("Q&A Tutor", "Ask questions about network security based on your course materials.")
    web_enabled = st.toggle(
        "Enable optional Wikipedia lookup",
        value=False,
        help="Only your typed question is sent externally when enabled. Do not enter private text.",
    )
    if "history" not in st.session_state:
        st.session_state.history = []
    if not st.session_state.history:
        st.markdown(
            '<div class="ui-empty"><div class="ui-empty-icon">✦</div>'
            '<h3>Start with a question</h3>'
            '<p>Explore your course notes, understand concepts, and review cited sources.</p>'
            '</div>', unsafe_allow_html=True
        )
        st.markdown('<div class="ui-prompts-label">✦ TRY ASKING</div>', unsafe_allow_html=True)
        suggestions = [
            "How does RSA work?",
            "What is a digital signature?",
            "Explain the TLS handshake.",
        ]
        prompt_cols = st.columns(3)
        for i, suggestion in enumerate(suggestions):
            with prompt_cols[i]:
                if st.button(suggestion, key=f"prompt_{i}", use_container_width=True):
                    st.session_state.pending_question = suggestion
                    st.rerun()
    for item in st.session_state.history:
        with st.chat_message("user"):
            st.write(item["question"])
        with st.chat_message("assistant"):
            st.write(item["answer"])
            sources_panel(item.get("sources", {}))
    question = st.chat_input("Ask a question about your course documents…")
    question = st.session_state.pop("pending_question", None) or question
    if question:
        with st.spinner("Searching your course documents…"):
            try:
                result = agents.tutor(question, web_enabled=web_enabled)
                st.session_state.history.append({"question": question, **result})
                st.rerun()
            except Exception as exc:
                st.error(f"Question could not be answered: {exc}")

elif page == "Quiz Agent":
    hero("Practice with a quiz", "Generate questions from your indexed documents, submit answers, and review feedback.")
    left, right = st.columns([2, 1])
    with left:
        topic = st.text_input("Topic", placeholder="e.g., TLS, RSA, Kerberos (blank = mixed topics)")
    with right:
        count = st.slider("Questions", 3, 12, 6)
    if st.button("Generate quiz", type="primary", use_container_width=True):
        with st.spinner("Generating questions from course sources…"):
            try:
                st.session_state.quiz = agents.make_quiz(topic, count)
                st.session_state.quiz_results = None
                st.session_state.quiz_version = st.session_state.get("quiz_version", 0) + 1
                st.rerun()
            except Exception as exc:
                st.error(f"Quiz generation failed: {exc}")
    quiz = st.session_state.get("quiz")
    if quiz:
        st.divider()
        st.subheader(f"Your quiz · {len(quiz['questions'])} questions")
        with st.form(f"quiz_answers_{st.session_state.get('quiz_version', 0)}"):
            answers = {}
            for i, q in enumerate(quiz["questions"]):
                st.markdown(f"**Question {i + 1}**")
                st.write(q["question"])
                if q["type"] in ("mcq", "tf"):
                    answers[str(i)] = st.radio(
                        "Select an answer", q["options"], index=None,
                        key=f"answer_{st.session_state.get('quiz_version', 0)}_{i}",
                    ) or ""
                else:
                    answers[str(i)] = st.text_area(
                        "Your answer", key=f"answer_{st.session_state.get('quiz_version', 0)}_{i}"
                    )
                st.caption("Source tags: " + ", ".join(q.get("citations", [])))
                st.divider()
            submitted = st.form_submit_button("Submit answers", type="primary")
        if submitted:
            with st.spinner("Grading your answers…"):
                try:
                    st.session_state.quiz_results = agents.grade(
                        quiz["questions"], answers, quiz["sources"]
                    )
                except Exception as exc:
                    st.error(f"Grading failed: {exc}")
        results = st.session_state.get("quiz_results")
        if results is not None:
            total = sum(item["score"] for item in results)
            st.metric("Your score", f"{total:g} / {len(results)}")
            st.info("AI grading for open-ended answers is provisional; review source evidence before treating scores as final.")
            for i, result in enumerate(results, 1):
                with st.container(border=True):
                    st.markdown(f"**Question {i} · {result['score']:g} / 1**")
                    st.write(result["reason"])
                    st.markdown("**Expected answer**")
                    st.write(result["correct"])
                    sources_panel(quiz["sources"], result.get("citations", []))

elif page == "Course Documents":
    hero("Course document library", "Upload, approve, and index your study materials locally.")
    st.info("Review the SHA-256 hash before approving a document for indexing.")
    uploaded = st.file_uploader("Choose a document", type=["pdf", "txt", "md", "docx", "pptx"])
    if uploaded is not None:
        data = uploaded.getvalue()
        st.write(f"**File:** {uploaded.name} · **Size:** {len(data):,} bytes")
        st.caption("SHA-256")
        st.code(core.digest(data), language=None)
        approved = st.checkbox("I approve this document and its displayed SHA-256 hash for local indexing")
        if st.button("Verify and index document", disabled=not approved, type="primary"):
            with st.spinner("Extracting text and creating embeddings…"):
                try:
                    n = core.ingest(uploaded.name, data, core.digest(data))
                    st.success(f"Indexed {n} text chunks. SHA-256 verified.")
                except Exception as exc:
                    st.error(f"Upload failed: {exc}")
    st.subheader("Indexed documents")
    try:
        report = core.integrity_report()
        if report:
            for item in report:
                with st.container(border=True):
                    st.write(("✅" if item["valid"] else "❌"), item["name"], "—", "Verified" if item["valid"] else "Integrity mismatch")
        else:
            st.caption("No documents indexed yet.")
    except Exception as exc:
        st.error(f"Could not read local database: {exc}")

else:
    hero("Security & integrity", "Inspect local document integrity and track required security evidence.")
    st.info("Network captures and adversarial test logs must still be performed and submitted separately.")
    if st.button("Run integrity check", type="primary"):
        try:
            report = core.integrity_report()
            if not report:
                st.warning("No indexed documents to check.")
            for item in report:
                st.write(("✅ PASS" if item["valid"] else "❌ FAIL") + " — " + item["name"])
                st.code(item["sha256"], language=None)
        except Exception as exc:
            st.error(f"Integrity check failed: {exc}")
    st.subheader("Verification checklist")
    st.checkbox("Capture local-only traffic using Wireshark/tcpdump")
    st.checkbox("Capture opted-in internet lookup traffic")
    st.checkbox("Record at least 3 prompt-injection tests and fixes")
    st.checkbox("Include threat model and mitigation notes")
