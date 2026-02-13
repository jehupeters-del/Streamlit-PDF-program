from __future__ import annotations

import re

QUESTION_PATTERN = re.compile(r"\bquestion\s+(\d+)\b", flags=re.IGNORECASE)


def find_question_numbers(text: str) -> list[int]:
    return [int(match.group(1)) for match in QUESTION_PATTERN.finditer(text)]


def validate_sequence(found_questions: list[int]) -> tuple[bool, int, list[int]]:
    unique = sorted(set(found_questions))
    if not unique:
        return True, 0, []

    max_question = unique[-1]
    expected = set(range(1, max_question + 1))
    missing = sorted(expected.difference(unique))
    return len(missing) == 0, max_question, missing


def infer_smart_output_name(input_name: str) -> str:
    base = input_name.rsplit(".", 1)[0]
    normalized = re.sub(r"[_\-]+", " ", base)
    month_pattern = re.compile(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        flags=re.IGNORECASE,
    )
    year_pattern = re.compile(r"\b(20\d{2})\b")

    month_match = month_pattern.search(normalized)
    year_match = year_pattern.search(normalized)

    month = month_match.group(1).title() if month_match else None
    year = year_match.group(1) if year_match else None

    if month and year:
        return f"{month} {year} solutions.pdf"
    if month:
        return f"{month} solutions.pdf"
    if year:
        return f"{year} solutions.pdf"
    return f"{base}_solutions.pdf"
