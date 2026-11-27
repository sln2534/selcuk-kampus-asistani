"""ChromaDB vektör deposu ve embedding modeli."""
from functools import lru_cache

from langchain_chroma import Chroma

from app.config import get_settings


@lru_cache
def get_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    s = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=s.embedding_model,
        google_api_key=s.gemini_api_key,
        client_args={"timeout": s.embedding_timeout},
    )


@lru_cache
def get_vectorstore() -> Chroma:
    s = get_settings()
    return Chroma(
        collection_name=s.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(s.chroma_dir),
    )
