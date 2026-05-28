"""共享：client 构造、tool schema 工具、ANSI 颜色。"""
import os
from openai import OpenAI

MODEL = os.getenv("MODEL", "gpt-4o-mini")


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置 OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)


def banner(name: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {name}  [model={MODEL}]")
    print("=" * 60)


# ANSI 简单上色（终端调试用）
class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    END = "\033[0m"
