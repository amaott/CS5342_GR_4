import pytest
from app.core import clean_filename, digest, split_chunks
from app.agents import parse_json

def test_sha256():
    assert digest(b'abc') == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

def test_path_traversal():
    assert clean_filename('../../slides.pdf') == 'slides.pdf'
    with pytest.raises(ValueError): clean_filename('.env')

def test_chunks():
    chunks = split_chunks(' '.join(str(n) for n in range(700)))
    assert len(chunks) == 2 and chunks[0].split()[-70:] == chunks[1].split()[:70]

def test_json():
    assert parse_json('```json\n{"questions": []}\n```') == {'questions':[]}
#testing the main file upload