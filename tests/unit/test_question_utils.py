import pytest

from src.services.question_utils import (
    find_question_numbers,
    infer_smart_output_name,
    validate_sequence,
)


@pytest.mark.unit
def test_find_question_numbers_case_insensitive() -> None:
    text = "question 1, Question 2, QUESTION 5"
    assert find_question_numbers(text) == [1, 2, 5]


@pytest.mark.unit
def test_validate_sequence_detects_missing() -> None:
    is_valid, max_question, missing = validate_sequence([1, 2, 4, 4])
    assert not is_valid
    assert max_question == 4
    assert missing == [3]


@pytest.mark.unit
def test_validate_sequence_no_questions() -> None:
    is_valid, max_question, missing = validate_sequence([])
    assert is_valid
    assert max_question == 0
    assert missing == []


@pytest.mark.unit
def test_infer_smart_output_name_month_year() -> None:
    assert infer_smart_output_name("math_january_2025_test.pdf") == "January 2025 solutions.pdf"


@pytest.mark.unit
def test_infer_smart_output_name_fallback() -> None:
    assert infer_smart_output_name("worksheet.pdf") == "worksheet_solutions.pdf"
