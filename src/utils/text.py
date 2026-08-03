# text.py
"""LLM çıktılarını temizlemek için yardımcılar."""
import re
from typing import Any

from pydantic import BaseModel
from strip_markdown import strip_markdown


def clean_output(text: str) -> str:
    """Markdown/formatlama artıklarını temizler ve metni sadeleştirir."""
    text = strip_markdown(text)
    # Kod işaretleyicileri kalıntılarını da temizle
    text = re.sub(r"[`*_>#|~]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_value(value: Any) -> Any:
    if isinstance(value, str):
        return clean_output(value)
    if isinstance(value, list):
        return [_clean_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean_value(v) for k, v in value.items()}
    return value


def clean_model(model: BaseModel) -> BaseModel:
    """Modelin tüm string alanlarını temizler (nested dahil)."""
    return model.__class__.model_validate(_clean_value(model.model_dump()))

