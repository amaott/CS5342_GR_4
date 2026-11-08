# Local Network Security Tutor & Quiz Bot

**CS 5342 — Network Security | Group Project**

A local-first, agent-based study application for network security. The project combines a Streamlit interface, locally hosted Ollama models, a course-document knowledge base, and two learning workflows: a citation-oriented Q&A tutor and a quiz generator/grader.

> **Project status:** Prototype under integration and testing. Features described below reflect the supplied project materials; they are not a claim that every workflow passes end-to-end testing in the latest GitHub revision.

## Overview

The application is designed to help students study from network security materials without routinely sending private course documents to an external LLM service. Users can upload and verify supported course documents, ask questions based on the local knowledge base, and practice with generated quizzes. Optional Wikipedia lookup is separate from local-only use.

## Features

| Area | Functionality |
| --- | --- |
| **Q&A Tutor Agent** | Answers network security questions using retrieved course content and displays source references. |
| **Quiz Agent** | Generates practice questions and grades answers with feedback; the project targets multiple-choice, true/false, and open-ended formats. |
| **Course Documents** | Local document ingestion, SHA-256-based approval/integrity checks, and storage of course knowledge. |
| **Security & Integrity** | Security-oriented checks and information about local data handling. |
| **Optional Internet Lookup** | Wikipedia-assisted lookup when explicitly enabled; disabled by default. |
| **Streamlit UI** | Navigation among Q&A Tutor, Quiz Agent, Course Documents, and Security & Integrity pages, with an Ollama status indicator. |

## Architecture

```text
User
  |
  v
Streamlit UI (app.py, style.css)
  |-- Q&A Tutor --------> Agent / retrieval logic
  |                         |-- Local course knowledge base (SQLite, embeddings)
  |                         |-- Ollama (qwen3:4b)
  |                         `-- Optional Wikipedia lookup (explicitly enabled)
  |-- Quiz Agent -------> Quiz generation and grading logic
  |-- Course Documents -> Local upload / SHA-256 verification
  `-- Security & Integrity -> Verification information and checks

Ollama embedding model: nomic-embed-text
```

The application is intended to use local inference by default. The exact network behavior must be assessed using the supplied traffic captures and the final configured Ollama endpoint.

## Requirements

- Python 3 and `pip`
- [Ollama](https://ollama.com/) installed and running
- Ollama models: `qwen3:4b` and `nomic-embed-text`
- Dependencies from `requirements.txt`

## Installation and Run

From the project directory containing `app.py` and `requirements.txt`:

```bash
python -m pip install -r requirements.txt
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Start Ollama if it is not already running:

```bash
ollama serve
```

In a separate terminal, from the same project directory:

```bash
streamlit run app.py
```

Open the local address printed by Streamlit (typically `http://localhost:8501`). The UI checks the availability of the configured Ollama server; the supplied configuration uses `http://127.0.0.1:11434` by default.

**Troubleshooting:** If `app.py` cannot be found, check that your terminal is in the directory containing that file. If Ollama is already running, do not start another server instance. Model downloads may take time.

## How to Use

1. **Course Documents:** Upload supported course material and complete the interface's integrity/approval steps before relying on it as a source.
2. **Q&A Tutor:** Ask a network security question. Review the answer and its cited source excerpts; a citation is not itself proof that a claim is supported.
3. **Quiz Agent:** Select a quiz workflow, generate questions, submit answers, and inspect the returned grading and feedback.
4. **Security & Integrity:** Review available verification controls and the security behavior of the prototype.
5. **Optional lookup:** Enable Wikipedia lookup only when external communication is appropriate. Do not include confidential course content or personal information in an externally assisted question.

## Repository Layout

The following paths are documented in the supplied UI and README materials. Confirm the final repository tree before submission.

```text
network_tutor_ui/
├── app.py                 # Streamlit application
├── style.css              # Custom UI styling (when present)
├── requirements.txt       # Python dependencies
├── backend/
│   ├── agents.py          # Agent-related logic
│   └── core.py            # Core application / knowledge-base functions
├── local_data/            # Local runtime data (do not commit)
└── README.md              # Project documentation
```

## Security Design and Verification

The course project requires a threat model, local-versus-internet network traffic verification, adversarial prompt testing, and knowledge-base integrity checks. The supplied threat-model report documents these areas:

- **Prompt injection:** Treat user inputs, retrieved documents, and web content as untrusted; use policy checks and adversarial testing. These controls are not guaranteed to block every attack.
- **Data exposure:** Validate uploads and filenames, keep course data local, and use SHA-256 to detect changes to ingested documents. Hashing detects modification; it does **not** encrypt data or prevent unauthorized access.
- **External communication / key management:** Wikipedia lookup may send typed questions to an external service. A remotely configured Ollama endpoint could also send model requests outside the device. Verify endpoint settings before claiming local-only operation.
- **Traffic verification:** Compare local-only inference with internet-assisted lookup using Wireshark/tcpdump captures and document the actual destinations and transmitted information.

Security testing evidence, packet captures, and reports should be submitted or linked only where appropriate and should not expose private course material or secrets.

## Known Limitations and Testing Status

The supplied project reports and testing discussions identify the following issues or verification needs:

- **Citation grounding:** A Q&A response can contain a course citation that does not adequately support its answer. Verify citations against the cited passages.
- **Over-refusal:** A question combining legitimate course content with malicious instructions may be rejected entirely rather than answering the legitimate portion safely.
- **Response completeness:** Q&A output has been reported as truncated in some tests; confirm behavior against the latest backend commit.
- **Performance:** Quiz generation can be slow depending on local model execution and system resources.
- **End-to-end verification:** The current integrated revision, quiz grading, citation correctness, and security/network claims should be re-tested before final submission.

Do not interpret the presence of a UI control as evidence that its underlying feature has passed end-to-end tests.

## Privacy and Responsible Use

- Do not commit `local_data/`, confidential lecture files, private uploads, credentials, or sensitive packet-capture content to a public repository.
- Keep optional internet lookup disabled for private questions.
- Confirm that Ollama is bound to the intended local endpoint.
- Treat generated explanations and grades as study aids, not authoritative course answers.


