import re
import unicodedata

def normalize_text(value: str) -> str:
    value = value or ""
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.upper().strip()
    value = re.sub(r"\s+", " ", value)
    return value

def tokenize(value: str):
    text = normalize_text(value)
    return [t for t in re.split(r"[^A-Z0-9]+", text) if t]
