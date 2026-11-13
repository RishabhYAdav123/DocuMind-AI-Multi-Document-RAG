import re
import unicodedata


def normalize_text(text: str) -> str:
    """Keep numbers, punctuation and paragraphs; remove control artifacts."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(c for c in text if c in "\n\t" or not unicodedata.category(c).startswith("C"))
    text = "\n".join(re.sub(r"[\t \u00a0]+", " ", line).strip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()
