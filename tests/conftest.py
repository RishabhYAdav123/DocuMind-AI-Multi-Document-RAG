import pymupdf
import pytest

from config.settings import Settings


@pytest.fixture
def settings():
    return Settings(_env_file=None, google_api_key="", min_similarity=0.1)


def pdf_bytes(*pages: str) -> bytes:
    with pymupdf.open() as doc:
        for text in pages:
            doc.new_page().insert_textbox((50, 50, 550, 750), text, fontsize=11)
        return doc.tobytes()


@pytest.fixture
def data():
    return pdf_bytes("Northstar revenue was USD 12 million in 2023. Revenue grew to USD 15 million in 2024.",
                     "Project Aurora received research funding of USD 1.2 million in 2024.")
