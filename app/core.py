import hashlib
import re
from pathlib import Path


def clean_filename(filename):
    filename = Path(filename).name
    if filename.startswith("."):
        raise ValueError("Invalid filename")
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename or "file"


def digest(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def split_chunks(text, chunk_size=500, overlap=70):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))

        if end == len(words):
            break

        start = end - overlap

    return chunks
