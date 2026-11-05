"""Streamlit UI for the local Network Security Tutor & Quiz Bot."""
"""Streamlit UI for the local Network Security Tutor & Quiz Bot."""

import re
import requests
import streamlit as st
from pathlib import Path
from backend import agents, core

# Page configuration
#st.set_page_config(
   # page_title='Network Security Tutor',
   # page_icon='🛡️',
   # layout='wide'
#)

# Load custom CSS
css_path = Path(__file__).parent / "style.css"

if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )
else:
    st.warning("Custom CSS file not found.")

st.title('🛡️ Network Security Tutor & Quiz Bot')
st.caption('Local-first course assistant • CS5342')

with st.sidebar:
    st.markdown("## 🛡️ Security AI")


    st.write("")

    st.markdown("##### WORKSPACE")

    page = st.radio(
        "Navigation",
        [
            "📚 Q&A Tutor",
            "🧠 Quiz Agent",
            "📂 Course Documents",
            "🛡️ Security & Integrity"
        ],
        label_visibility="collapsed",
        format_func=lambda x: x
    )

    page = page.split(" ", 1)[1]

    st.divider()

    st.markdown("##### SYSTEM STATUS")

    try:
        response = requests.get(
            core.OLLAMA + "/api/tags",
            timeout=2
        )
        response.raise_for_status()
        st.success("● AI Engine Online")
    except requests.RequestException:
        st.warning("● AI Engine Offline")

    st.caption("Local Ollama")
    st.caption("Private • Local-first")

    st.divider()

    st.caption("Network Security Tutor")
    st.caption("Version 1.0 • Course Project")

def sources_panel(sources, tags=None):
    tags = list(sources) if tags is None else tags
    if not tags:
        return

    with st.expander('Source citations'):
        for tag in tags:
            item = sources.get(tag)
            if item:
                st.markdown(
                    f'**[{tag}] {item.get("name", "Unknown")}** '
                    f'— {item.get("locator", "")}'
                )
                st.caption(item.get('excerpt', ''))


# Q&A Tutor Page
if page == 'Q&A Tutor':
    st.header('Ask about network security')
    st.caption(
        'Your AI-powered study companion for Network Security.'
    )

    st.write("")

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        with st.container(border=True):
            st.markdown("### 📚 Ask Questions")
            st.write(
                "Get explanations grounded in "
                "verified course materials."
            )

    with col2:
        with st.container(border=True):
            st.markdown("### 🧠 Generate Quizzes")
            st.write(
                "Practice network security concepts "
                "with AI-generated questions."
            )

    with col3:
        with st.container(border=True):
            st.markdown("### 🛡️ Verify Sources")
            st.write(
                "Explore course citations and "
                "check document integrity."
            )

    st.write("")

    # Optional Wikipedia lookup
    web_enabled = st.toggle(
        'Allow optional Wikipedia citation lookup',
        value=False,
        help=(
            'Only your typed question is sent externally '
            'when enabled; do not enter private text.'
        )
    )

    # Chat history
    if 'history' not in st.session_state:
        st.session_state.history = []

    for item in st.session_state.history:
        with st.chat_message('user'):
            st.write(item['question'])

        with st.chat_message('assistant'):
            st.write(item['answer'])

            cited_tags = set(
                re.findall(r'\bS\d+\b', item['answer'])
            )

            sources_panel(
                item['sources'],
                [
                    tag for tag in item['sources']
                    if tag in cited_tags
                ]
            )

    # Chat input
    question = st.chat_input(
        'Ask a question about your course documents'
    )

    if question:
        with st.spinner('Searching verified local documents...'):
            try:
                result = agents.tutor(
                    question,
                    web_enabled=web_enabled
                )

                st.session_state.history.append({
                    'question': question,
                    **result
                })

                st.rerun()

            except Exception as exc:
                st.error(
                    f'Question could not be answered: {exc}'
                )

elif page == 'Quiz Agent':
    st.header('🧠 Quiz Generator')
    st.caption(
        'Test your knowledge with AI-generated questions '
        'based on verified course materials.'
    )

    st.write("")

    with st.container(border=True):
        st.markdown("#### ⚙️ Quiz Settings")

        topic = st.text_input(
            'Choose a topic',
            placeholder='e.g., TLS, RSA, Kerberos',
            help='Leave blank to generate questions from random topics.'
        )

        count = st.slider(
            'Number of questions',
            min_value=3,
            max_value=12,
            value=6
        )
    if st.button('Generate quiz', type='primary'):
        with st.spinner('Generating questions from verified course sources...'):
            try:
                st.session_state.quiz = agents.make_quiz(topic, count)
                st.session_state.quiz_results = None
            except Exception as exc:
                st.error(f'Quiz generation failed: {exc}')
    quiz = st.session_state.get('quiz')
    if quiz:
        with st.form('quiz_answers'):
            answers = {}
            for i, q in enumerate(quiz['questions']):
                st.markdown(f'**{i+1}. {q["question"]}**')
                if q['type'] in ('mcq', 'tf'):
                    answers[str(i)] = st.radio('Select an answer', q['options'], index=None, key=f'answer_{i}') or ''
                else:
                    answers[str(i)] = st.text_area('Your answer', key=f'answer_{i}')
                st.caption('Citations: ' + ', '.join(q.get('citations', [])))
            submitted = st.form_submit_button('Submit answers', type='primary')
        if submitted:
            with st.spinner('Grading...'):
                try:
                    st.session_state.quiz_results = agents.grade(quiz['questions'], answers, quiz['sources'])
                except Exception as exc:
                    st.error(f'Grading failed: {exc}')
        results = st.session_state.get('quiz_results')
        if results:
            total = sum(item['score'] for item in results)
            st.subheader(f'Score: {total:g} / {len(results)}')

            st.info(
                'AI grading for open-ended questions is provisional. '
                'Review the answer and course evidence before treating '
                'the score as final.'
            )

            for i, result in enumerate(results, 1):
                st.markdown(f'**Question {i}: {result["score"]:g} / 1**')
                st.write(result['reason'])
                st.write('Expected answer:', result['correct'])
                sources_panel(quiz['sources'], result.get('citations', []))


elif page == 'Course Documents':
    st.header('Upload course documents')
    st.info('Documents are processed locally. Review the SHA-256 hash before approving ingestion.')

    uploaded = st.file_uploader(
        'Choose a file',
        type=['pdf', 'txt', 'md', 'docx', 'pptx']
    )

    if uploaded is not None:
        data = uploaded.getvalue()
        st.write('File:', uploaded.name, '· Size:', f'{len(data):,} bytes')
        st.code(core.digest(data), language=None)

        approved = st.checkbox(
            'I approve this document and its displayed SHA-256 hash for local indexing'
        )

        if st.button('Verify and index document', disabled=not approved, type='primary'):
            with st.spinner('Extracting text and creating local embeddings...'):
                try:
                    n = core.ingest(uploaded.name, data, core.digest(data))
                    st.success(f'Indexed {n} text chunks. SHA-256 verified.')
                except Exception as exc:
                    st.error(f'Upload failed: {exc}')

    st.subheader('Indexed documents')

    try:
        report = core.integrity_report()

        if report:
            for item in report:
                st.write(
                    ('✅' if item['valid'] else '❌'),
                    item['name'],
                    '—',
                    'Verified' if item['valid'] else 'Integrity mismatch'
                )

            # DELETE DOCUMENT SECTION
            st.divider()
            st.subheader('Delete a document')

            document_names = [item['name'] for item in report]

            selected_document = st.selectbox(
                'Select the document you want to delete',
                document_names
            )

            confirm_delete = st.checkbox(
                f'I understand that deleting {selected_document} '
                'will remove its indexed content and local file.'
            )

            if st.button(
                'Delete selected document',
                disabled=not confirm_delete,
                type='secondary'
            ):
                try:
                    deleted = core.delete_document(selected_document)

                    if deleted:
                        st.success(f'{selected_document} was successfully deleted.')
                        st.rerun()
                    else:
                        st.warning('Document was not found in the database.')

                except Exception as exc:
                    st.error(f'Delete failed: {exc}')

        else:
            st.caption('No documents indexed yet.')

    except Exception as exc:
        st.error(f'Could not read local database: {exc}')


else:
    st.header('Security & Integrity')
    st.info('This page displays local integrity checks. Network traffic capture and adversarial test logs must still be performed and submitted separately.')

    if st.button('Run integrity check', type='primary'):
        try:
            report = core.integrity_report()

            if not report:
                st.warning('No indexed documents to check.')

            for item in report:
                st.write(('✅ PASS' if item['valid'] else '❌ FAIL') + ' — ' + item['name'])
                st.code(item['sha256'], language=None)

        except Exception as exc:
            st.error(f'Integrity check failed: {exc}')

    st.subheader('Verification checklist')
    st.checkbox('Capture local-only traffic using Wireshark/tcpdump')
    st.checkbox('Capture opted-in internet lookup traffic')
    st.checkbox('Record at least 3 prompt-injection tests and fixes')
    st.checkbox('Include threat model and mitigation notes')
