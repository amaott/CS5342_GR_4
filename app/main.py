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

def clean_filename(name: str) -> str:
    base = Path(name.replace('\\', '/')).name
    base = re.sub(r'[^a-zA-Z0-9._ -]', '_', base).strip(' .')
    if not base or base.startswith('.') or Path(base).suffix.lower() not in ALLOWED:
        raise ValueError('Unsupported document name/type')
    return base[:120]


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

def ollama_post(path: str, payload: dict) -> dict:
    response = requests.post(f'{OLLAMA}{path}', json=payload, timeout=240)
    response.raise_for_status()
    return response.json()


def chat(messages: list[dict], json_mode: bool = False) -> str:
    payload = {'model': CHAT_MODEL, 'messages': messages, 'stream': False,
               'options': {'temperature': 0.15}}
    if json_mode:
        payload['format'] = 'json'
    answer = ollama_post('/api/chat', payload)
    return answer['message']['content']


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    # Ollama batches embeddings locally; no Python HF downloads.
    data = ollama_post('/api/embed', {'model': EMBED_MODEL, 'input': texts})
    return data['embeddings']


def ingest(name: str, raw: bytes, approved_sha256: str) -> int:
    name = clean_filename(name)
    if len(raw) > MAX_UPLOAD:
        raise ValueError('Document exceeds 20 MB limit')
    # Never index a file whose checksum differs from the user-approved baseline.
    if digest(raw) != approved_sha256:
        raise ValueError('SHA-256 mismatch; document was not ingested')
    sections = extract(raw, name)
    pieces = [(loc, chunk) for loc, section in sections for chunk in split_chunks(section)]
    if not pieces:
        raise ValueError('No extractable text; scanned PDFs need text extraction first')
    vectors = []
    for start in range(0, len(pieces), 16):
        vectors.extend(embed([p[1] for p in pieces[start:start+16]]))
    target = DOCS / name
    if target.exists() and digest(target.read_bytes()) != approved_sha256:
        raise ValueError('Filename collision with a different local document')
    with connect() as con:
        existing = con.execute('SELECT id, sha256 FROM documents WHERE name=?', (name,)).fetchone()
        if existing and existing['sha256'] != approved_sha256:
            raise ValueError('Existing document has a different checksum; rename the replacement')
        if existing:
            con.execute('DELETE FROM chunks WHERE document_id=?', (existing['id'],))
            doc_id = existing['id']
        else:
            cur = con.execute('INSERT INTO documents(name, sha256, uploaded_at) VALUES(?,?,?)',
                              (name, approved_sha256, int(time.time())))
            doc_id = cur.lastrowid
        con.executemany('INSERT INTO chunks(document_id,locator,content,embedding) VALUES(?,?,?,?)',
                        [(doc_id, loc, content, json.dumps(vec))
                         for (loc, content), vec in zip(pieces, vectors)])
        # Verify saved bytes before transaction completes.
        target.write_bytes(raw)
        if digest(target.read_bytes()) != approved_sha256:
            raise ValueError('Stored document failed integrity check')
    return len(pieces)


def integrity_report() -> list[dict]:
    with connect() as con:
        docs = con.execute('SELECT name,sha256 FROM documents ORDER BY name').fetchall()
    return [{'name': r['name'], 'sha256': r['sha256'],
             'valid': (DOCS / r['name']).is_file() and digest((DOCS / r['name']).read_bytes()) == r['sha256']}
            for r in docs]


def retrieve(query: str, limit: int = 5) -> list[dict]:
    with connect() as con:
        rows = con.execute('''SELECT d.name, d.sha256, c.locator, c.content, c.embedding
                              FROM chunks c JOIN documents d ON d.id=c.document_id''').fetchall()
    valid = {item['name'] for item in integrity_report() if item['valid']}
    rows = [r for r in rows if r['name'] in valid]
    if not rows:
        return []
    q = np.asarray(embed([query])[0], dtype=np.float32)
    qnorm = np.linalg.norm(q) + 1e-9
    scores = []
    for r in rows:
        v = np.asarray(json.loads(r['embedding']), dtype=np.float32)
        if len(v) != len(q):
            continue
        score = float(np.dot(q, v) / (qnorm * (np.linalg.norm(v) + 1e-9)))
        scores.append((score, r))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [{'source': r['name'], 'locator': r['locator'], 'text': r['content'], 'score': s}
            for s, r in scores[:limit]]


def all_chunks(limit: int = 150) -> list[dict]:
    with connect() as con:
        rows = con.execute('''SELECT d.name,c.locator,c.content FROM chunks c
                         JOIN documents d ON d.id=c.document_id ORDER BY c.id LIMIT ?''', (limit,)).fetchall()
    valid = {i['name'] for i in integrity_report() if i['valid']}
    return [{'source': r['name'], 'locator': r['locator'], 'text': r['content']}
            for r in rows if r['name'] in valid]


def format_context(chunks: list[dict], prefix='S') -> tuple[str, dict]:
    sources = {}
    parts = []
    for i, entry in enumerate(chunks, 1):
        tag = f'{prefix}{i}'
        sources[tag] = {'name': entry['source'], 'locator': entry['locator'],
                        'excerpt': entry['text'][:500]}
        parts.append(f'[{tag}] {entry["source"]}, {entry["locator"]}\n{entry["text"][:2200]}')
    return '\n\n'.join(parts), sources


def wikipedia_lookup(question: str) -> list[dict]:
    """Explicitly opt-in Internet enrichment; sends only the typed question (NOT course excerpts)."""
    url = 'https://en.wikipedia.org/w/api.php'
    headers = {'User-Agent': 'LocalNetworkSecurityTutor/1.0 (educational demo)'}
    res = requests.get(url, params={'action': 'query', 'generator': 'search', 'gsrsearch': question[:180],
                        'gsrlimit': 3, 'prop': 'extracts|info', 'inprop': 'url',
                        'exintro': 1, 'explaintext': 1, 'exsentences': 5, 'format': 'json'},
                        headers=headers, timeout=15)
    res.raise_for_status()
    pages = res.json().get('query', {}).get('pages', {})
    return [{'source': p.get('fullurl', ''), 'locator': 'Wikipedia',
             'text': p.get('extract', '')[:1200]} for p in pages.values() if p.get('extract') and p.get('fullurl')]

