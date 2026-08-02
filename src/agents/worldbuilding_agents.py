# worldbuilding_agents.py
"""
Karakter, olay, setting, lore vb. gibi seyleri ureten agent.
prompta gore model uretebilir veya bazi kisimlari yazilmis modellerin kalan kisimlarini
istenen prompta ve uyuma gore doldurabilir.
"""

from pydantic_ai import Agent
from pydantic_ai.providers import OpenAIProvider  # veya GroqProvider, AnthropicProvider etc.

from src.models.character import Character
from src.models.world import World
from src.models.setting import Setting
from src.models.lore import Lore
from src.models.event import Event
from src.models.conflict import Conflict
from src.models.scene import Scene
from src.models.chapter import Chapter


# ================================== ===========================================
# PROVIDER AYARI
# =============================================================================
# OpenAI kullanıyorsan:
provider = OpenAIProvider(model="gpt-4o")

# Groq kullanıyorsan (OpenAIProvider ile uyumlu):
# import os
# provider = OpenAIProvider(
#     model="llama-3.3-70b-versatile",
#     base_url="https://api.groq.com/openai/v1",
#     api_key=os.environ["GROQ_API_KEY"],
# )

# Anthropic kullanıyorsan:
# from pydantic_ai.providers import AnthropicProvider
# provider = AnthropicProvider(model="claude-sonnet-4-20250514")


# =============================================================================
# SYSTEM PROMPT
# =============================================================================
SYSTEM_PROMPT = """
Sen bir worldbuilding ve hikaye tasarımı asistanısın.
Kullanıcının verdiği prompt'a göre karakter, mekan, olay, lore, çatışma, sahne veya bölüm
tarihi oluşturuyorsun veya eksik alanları dolduruyorsun.

Kurallar:
- Verdiğin çıktı her zaman istenen modelin şemasına uygun olmalı.
- `id` alanını kendin oluştur (UUID formatında).
- Hiçbir şekilde `content` dışında markdown/formatlama ekleme.
- Kullanıcı kısmen doldurulmuş bir model verirse, eksik alanları mantıklı şekilde tamamla.
- Dünyaya, mevcut lore'a ve karakterlere uygun tutarlılık koru.
"""


# =============================================================================
# AGENT TANIMLARI
# =============================================================================

# Her model tipi için ayrı agent - daha temiz ve tip-güvenli

agent_character = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=Character,
)

agent_world = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=World,
)

agent_setting = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=Setting,
)

agent_lore = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=Lore,
)

agent_event = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=Event,
)

agent_conflict = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=Conflict,
)

agent_scene = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=Scene,
)

agent_chapter = Agent(
    provider=provider,
    system_prompt=SYSTEM_PROMPT,
    result_type=Chapter,
)


# =============================================================================
# MODEL -> AGANT HARİTASI
# =============================================================================
AGENT_MAP = {
    "character": agent_character,
    "world": agent_world,
    "setting": agent_setting,
    "lore": agent_lore,
    "event": agent_event,
    "conflict": agent_conflict,
    "scene": agent_scene,
    "chapter": agent_chapter,
}


# =============================================================================
# KULLANIM
# =============================================================================

def generate(model_type: str, prompt: str, partial_data: dict | None = None):
    """
    Belirtilen model tipi için AI'dan veri üretir.

    Args:
        model_type: "character", "world", "setting", "lore", "event",
                    "conflict", "scene", "chapter"
        prompt: Kullanıcının isteği (örn: "ortaçağ tarzı, kuzeyli bir kraliyet ailesi")
        partial_data: (opsiyonel) Zaten doldurulmuş alanlar.
                      Agent eksik alanları tamamlayacak.

    Returns:
        Pydantic model instance (Character, World, Setting, ...)
    """
    agent = AGENT_MAP.get(model_type)
    if not agent:
        raise ValueError(f"Bilinmeyen model tipi: {model_type}. Seçenekler: {list(AGENT_MAP.keys())}")

    # Eğer kısmi veri varsa, prompt'a ekle
    if partial_data:
        existing = "\n".join(f"- {k}: {v}" for k, v in partial_data.items())
        prompt = f"{prompt}\n\nZaten doldurulmuş alanlar:\n{existing}\nEksik alanları tamamla ve mevcut alanları koru."

    result = agent.run_sync(prompt)
    return result.data


# =============================================================================
# ÖRNEK KULLANIM (test için)
# =============================================================================
if __name__ == "__main__":
    # Yeni bir karakter üret
    karakter = generate(
        model_type="character",
        prompt="Ortaçağ tarzı bir kuzeyli savaşçı, soğuk iklimde yaşayan, sert ama adaletli bir karakter",
    )
    print(karakter.model_dump_json(indent=2))

    # Kısmi veriden karakter tamamla
    karakter2 = generate(
        model_type="character",
        prompt="Bu karaktere uygun kişilik ve konuşma tarzı ekle",
        partial_data={"name": "Eren", "age": "28", "role": "Kuzey Muhafızları Lideri"},
    )
    print(karakter2.model_dump_json(indent=2))

    # Yeni bir mekan üret
    mekan = generate(
        model_type="setting",
        prompt="Buzul çayı kenarında, ortaçağ tarzı, misafirperver ama sessiz bir kasaba",
    )
    print(mekan.model_dump_json(indent=2))

    # Yeni bir lore üret
    mif = generate(
        model_type="lore",
        prompt="Dünyada ateşin nasıl keşfedildiğine dair mitik bir anlatım",
        partial_data={"category": "history", "title": "Ateşin Keşfi"},
    )
    print(mif.model_dump_json(indent=2))