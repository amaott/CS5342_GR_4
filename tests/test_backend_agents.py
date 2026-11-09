import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "streamlit-UI")
)

from backend import agents


def test_backend_grade_correct_mcq():
    questions = [{
        "type": "mcq",
        "question": "What is RSA?",
        "answer": "A",
        "citations": [],
        "explanation": "Correct answer"
    }]

    answers = {"0": "a"}

    result = agents.grade(questions, answers, {})

    assert result[0]["score"] == 1


def test_backend_grade_wrong_mcq():
    questions = [{
        "type": "mcq",
        "question": "What is RSA?",
        "answer": "A",
        "citations": [],
        "explanation": "Correct answer"
    }]

    answers = {"0": "B"}

    result = agents.grade(questions, answers, {})

    assert result[0]["score"] == 0


def test_backend_grade_empty_answer():
    questions = [{
        "type": "mcq",
        "question": "What is RSA?",
        "answer": "A",
        "citations": []
    }]

    answers = {"0": "   "}

    result = agents.grade(questions, answers, {})

    assert result[0]["score"] == 0
    assert result[0]["reason"] == "No answer submitted."


def test_backend_grade_rsa_correct_private_exponent():
    questions = [{
        "type": "open",
        "question": "Calculate the private exponent for p = 5, q = 11, e = 3.",
        "answer": "27",
        "citations": []
    }]

    answers = {"0": "27"}

    result = agents.grade(questions, answers, {})

    assert result[0]["score"] == 1
    assert result[0]["correct"] == "27"


def test_backend_grade_rsa_wrong_private_exponent():
    questions = [{
        "type": "open",
        "question": "Calculate the private exponent for p = 5, q = 11, e = 3.",
        "answer": "27",
        "citations": []
    }]

    answers = {"0": "25"}

    result = agents.grade(questions, answers, {})

    assert result[0]["score"] == 0