#creating this for uploading class files

from __future__ import annotations
import hashlib, json, os, re, sqlite3, time
from pathlib import Path
import numpy as np
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'local_data'
DOCS = DATA / 'documents'
DB = DATA / 'knowledge.sqlite3'
OLLAMA = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
CHAT_MODEL = os.getenv('CHAT_MODEL', 'qwen3:4b')
EMBED_MODEL = os.getenv('EMBED_MODEL', 'nomic-embed-text')
ALLOWED = {'.pdf', '.txt', '.md', '.docx', '.pptx'}
MAX_UPLOAD = 20 * 1024 * 1024




def connect():
    DATA.mkdir(exist_ok=True)
    DOCS.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript('''
        CREATE TABLE IF NOT EXISTS documents (
          id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
          sha256 TEXT NOT NULL, uploaded_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS chunks (
          id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL,
          locator TEXT NOT NULL, content TEXT NOT NULL, embedding TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id));
        CREATE TABLE IF NOT EXISTS attack_logs (
          id INTEGER PRIMARY KEY, timestamp INTEGER NOT NULL,
          prompt TEXT NOT NULL, response TEXT NOT NULL, result TEXT NOT NULL, fix TEXT);
    ''')
    con.commit()
    return con


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def clean_filename
#need to save names but for security prevent hiddden files or traversal


def extract(raw: bytes, name: str) -> list[tuple[str, str]]:
    ext = Path(name).suffix.lower()
    if ext in {'.txt', '.md'}:
        return [('text', raw.decode('utf-8', errors='replace'))]
    if ext == '.pdf':
        import fitz
        with fitz.open(stream=raw, filetype='pdf') as pdf:
            return [(f'page {i+1}', page.get_text()) for i, page in enumerate(pdf)]
    if ext == '.docx':
        from docx import Document
        import io
        d = Document(io.BytesIO(raw))
        return [('document', '\n'.join(p.text for p in d.paragraphs))]
    if ext == '.pptx':
        from pptx import Presentation
        import io
        prs = Presentation(io.BytesIO(raw))
        return [(f'slide {i+1}', '\n'.join(s.text for s in slide.shapes if s.has_text_frame))
                for i, slide in enumerate(prs.slides)]
    raise ValueError('Unsupported file type')

def split_chunks(text: str, max_words: int = 450, overlap: int = 70) -> list[str]:
    words = text.split()
    if not words:
        return []
    out = []
    step = max_words - overlap
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + max_words])
        if chunk:
            out.append(chunk)
        if i + max_words >= len(words):
            break
    return out

def ollama_post()
