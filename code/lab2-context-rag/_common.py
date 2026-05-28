"""共享工具：client / embedding / chroma."""
import os
from typing import List
from openai import OpenAI

MODEL = os.getenv("MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), ".chroma")


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置 OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)


_local_embedder = None


def embed(texts: List[str]) -> List[List[float]]:
    """统一接口：兼容 OpenAI / 本地 sentence-transformers。"""
    if EMBED_MODEL == "local":
        global _local_embedder
        if _local_embedder is None:
            from sentence_transformers import SentenceTransformer
            _local_embedder = SentenceTransformer("BAAI/bge-m3")
        return _local_embedder.encode(texts, normalize_embeddings=True).tolist()
    client = get_client()
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def get_chroma():
    import chromadb
    return chromadb.PersistentClient(path=CHROMA_DIR)


def chunk(text: str, size: int = 400, overlap: int = 60) -> List[str]:
    out, i = [], 0
    while i < len(text):
        out.append(text[i : i + size])
        i += size - overlap
    return out


def banner(name: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {name}")
    print(f"  model={MODEL}  embed={EMBED_MODEL}")
    print("=" * 60)
