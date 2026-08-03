# ai.py
"""
LLM sağlayıcı ayarları. Tüm değerler env değişkenleriyle override edilebilir:
- AI_BASE_URL  : OpenAI-uyumlu API kök adresi
- AI_MODEL     : model adı
- AI_API_KEY   : API anahtarı
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AI_", extra="ignore")

    base_url: str = "https://opencode.ai/zen/go/v1"
    model: str = "deepseek-v4-flash"
    api_key: str = ""

    @property
    def normalized_base_url(self) -> str:
        # Kullanıcı tam endpoint verirse (…/chat/completions) kök adrese indir.
        if self.base_url.endswith("/chat/completions"):
            return self.base_url[: -len("/chat/completions")]
        return self.base_url.rstrip("/")


ai_settings = AISettings()


def get_model() -> OpenAIChatModel:
    # Boş key'e izin verilmeyen AsyncOpenAI client'ı için; yerel (key'siz) endpoint'ler
    # de çalışabilsin diye boşsa placeholder kullanılır.
    api_key = ai_settings.api_key or "not-needed"
    return OpenAIChatModel(
        ai_settings.model,
        provider=OpenAIProvider(
            base_url=ai_settings.normalized_base_url,
            api_key=api_key,
        ),
    )
