"""共享工具：client 构造、模型名读取。所有 demo 都会 import 这里。"""
import os
from openai import OpenAI

MODEL = os.getenv("MODEL", "gpt-4o-mini")


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "请先设置 OPENAI_API_KEY 环境变量（兼容 DeepSeek / 通义 / 智谱等任何 OpenAI-Compatible Key）"
        )
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def banner(name: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {name}    [model={MODEL}]")
    print("=" * 60)
