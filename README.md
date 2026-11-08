# CS5342_GR_4


# Network Security Tutor — Streamlit UI
This package contains a Streamlit interface plus unchanged copies of the two uploaded teammate Python files, placed under backend/ so their relative imports work:
- backend/agents.py = supplied agents.py
- backend/core.py = supplied main (1).py (renamed for the .core import)
Setup
From the network_tutor_ui directory:
python -m pip install -r requirements.txt
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama serve

If Ollama is already running, do not start a second instance. In another terminal:
streamlit run app.py

The application uses local SQLite storage in local_data/ and Ollama at http://127.0.0.1:11434 by default. Internet lookup is off by default; enabling it sends the typed question to Wikipedia. Do not put private course content into an internet-enabled question.
Features
- Q&A Tutor with course citations
- Quiz generation and grading (MCQ, true/false, open-ended)
- Local document upload with explicit SHA-256 approval and integrity checking
- Security verification checklist (not a substitute for real traffic captures and attack logs)
Integration note
The backend copies were not modified. If your teammates update them, replace the copies or merge this UI into the repository's actual Python package. This UI has passed Python syntax compilation, not end-to-end model testing. Real testing requires installed dependencies, a running Ollama service and downloaded local models.

Do not commit local_data/ or confidential course files to GitHub.
