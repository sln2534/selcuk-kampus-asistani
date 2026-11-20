"""Uygulama ayarları. Tüm değerler ortam değişkenlerinden (.env) okunur."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    # Telegram
    telegram_bot_token: str = ""
    api_url: str = "http://localhost:8000"  # botun konuştuğu FastAPI adresi

    # LLM (Gemini). Gemini 1.5 Flash emekliye ayrıldı; güncel model adını
    # Google AI Studio'dan kontrol edip GEMINI_MODEL ile değiştirin.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    embedding_model: str = "models/gemini-embedding-001"
    # Ana model meşgulse (503/504) ya da kullanılamıyorsa sırayla denenecek yedek modeller
    gemini_fallback_models: str = "gemini-3.5-flash-lite,gemini-3.8-flash"
    llm_timeout: float = 20.0  # saniye; her model için en fazla bekleme

    # RAG
    pdf_dir: Path = ROOT / "data" / "pdfs"
    chroma_dir: Path = ROOT / "data" / "chroma"
    collection_name: str = "selcuk_belgeler"
    chunk_size: int = 1200
    chunk_overlap: int = 200
    top_k: int = 5
    # Chroma mesafe skoru (düşük = daha benzer). Bu eşiğin üstündeki parçalar alakasız sayılır.
    max_distance: float = 0.72

    # Veri dosyaları
    calendar_file: Path = ROOT / "data" / "takvim.json"
    units_file: Path = ROOT / "data" / "birimler.json"
    stats_file: Path = ROOT / "data" / "stats.jsonl"
    cache_file: Path = ROOT / "data" / "cevap_onbellek.json"
    cache_enabled: bool = True  # .env: CACHE_ENABLED=false ile kapatılır

    max_question_len: int = 500


@lru_cache
def get_settings() -> Settings:
    return Settings()
