from __future__ import annotations

from pathlib import Path

import fitz
import pytest


@pytest.fixture
def synthetic_pdf_bytes() -> bytes:
    document = fitz.open()
    page1 = document.new_page()
    page1.insert_text((72, 72), "Cover page")
    page2 = document.new_page()
    page2.insert_text((72, 72), "Question 1\nQuestion 2")
    page3 = document.new_page()
    page3.insert_text((72, 72), "Question 4")
    try:
        return document.tobytes(deflate=True, garbage=3)
    finally:
        document.close()


@pytest.fixture
def real_world_fixture_paths() -> list[Path]:
    base = Path(__file__).parent / "fixtures" / "real_world"
    base.mkdir(parents=True, exist_ok=True)

    paths = [
        base / "math_practice_january_2025.pdf",
        base / "science_review_2024.pdf",
    ]

    if all(path.exists() for path in paths):
        return paths

    docs_content = {
        paths[0]: [
            "January 2025 Math Practice\nInstructions and formula sheet",
            "Question 1\nSolve x + 5 = 9",
            "Worked example page",
            "Question 2\nFactor x^2 + 5x + 6",
            "Question 4\nFind area of a triangle",
        ],
        paths[1]: [
            "Science Review 2024\nUnit Overview",
            "Question 1\nDefine photosynthesis",
            "Question 2\nDescribe the water cycle",
            "Question 3\nState Newton's second law",
        ],
    }

    for path, pages in docs_content.items():
        document = fitz.open()
        try:
            for text in pages:
                page = document.new_page()
                page.insert_text((72, 72), text)
            path.write_bytes(document.tobytes(deflate=True, garbage=3))
        finally:
            document.close()

    return paths
