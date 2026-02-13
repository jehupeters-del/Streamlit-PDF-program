from __future__ import annotations

import re

QUESTION_PATTERN = re.compile(r"\bquestion\s+(\d+)\b", flags=re.IGNORECASE)

MONTH_ALIASES = {
    "jan": "January",
    "january": "January",
    "feb": "February",
    "february": "February",
    "mar": "March",
    "march": "March",
    "apr": "April",
    "april": "April",
    "may": "May",
    "jun": "June",
    "june": "June",
    "jul": "July",
    "july": "July",
    "aug": "August",
    "august": "August",
    "sep": "September",
    "sept": "September",
    "september": "September",
    "oct": "October",
    "october": "October",
    "nov": "November",
    "november": "November",
    "dec": "December",
    "december": "December",
}


def _normalize_year(year_token: str) -> str:
    if len(year_token) == 2:
        return f"20{year_token}"
    return year_token


def _find_month_year(tokens: list[str], compact_text: str) -> tuple[str | None, str | None]:
    for index, token in enumerate(tokens):
        month = MONTH_ALIASES.get(token)
        if not month:
            continue

        if index + 1 < len(tokens) and re.fullmatch(r"\d{2}|\d{4}", tokens[index + 1]):
            return month, _normalize_year(tokens[index + 1])
        if index > 0 and re.fullmatch(r"\d{2}|\d{4}", tokens[index - 1]):
            return month, _normalize_year(tokens[index - 1])

    compact_match = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)(\d{2}|\d{4})",
        compact_text,
        flags=re.IGNORECASE,
    )
    if compact_match:
        month_key = compact_match.group(1).lower()
        year_token = compact_match.group(2)
        return MONTH_ALIASES[month_key], _normalize_year(year_token)

    month_only = next((MONTH_ALIASES[token] for token in tokens if token in MONTH_ALIASES), None)
    year_only = next(
        (_normalize_year(token) for token in tokens if re.fullmatch(r"\d{2}|\d{4}", token)),
        None,
    )
    return month_only, year_only


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
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", base).strip().lower()
    tokens = [token for token in normalized.split() if token]
    compact_text = re.sub(r"\s+", "", normalized)

    month, year = _find_month_year(tokens, compact_text)

    if month and year:
        return f"{month} {year} solutions.pdf"
    if month:
        return f"{month} solutions.pdf"
    if year:
        return f"{year} solutions.pdf"
    return f"{base}_solutions.pdf"
