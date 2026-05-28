"""Demo 2 · Few-shot：3 个示例搞定 zero-shot 解不了的反讽

要点：
- 示例的多样性 > 数量
- 把例子写成 assistant 角色的多轮历史，比写在 user 里更有效
"""
from _common import get_client, MODEL, banner

client = get_client()


def classify_few_shot(text: str) -> str:
    messages = [
        {"role": "system", "content": "你是一个情感分类器。**只输出一个词**：positive / negative / neutral。"},

        # 示例 1：明显负面
        {"role": "user", "content": "服务员态度恶劣。"},
        {"role": "assistant", "content": "negative"},

        # 示例 2：明显正面
        {"role": "user", "content": "我超级喜欢这本书！"},
        {"role": "assistant", "content": "positive"},

        # 示例 3：中性
        {"role": "user", "content": "包装一般般，没什么特别。"},
        {"role": "assistant", "content": "neutral"},

        # 示例 4：反讽（边界 case）
        {"role": "user", "content": "你们的'快速响应'让我等了 3 小时。"},
        {"role": "assistant", "content": "negative"},

        # 真正的问题
        {"role": "user", "content": text},
    ]
    response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
    return response.choices[0].message.content.strip()


SAMPLES = [
    "这家店服务真差，菜也凉了。",
    "我超级喜欢这本书！",
    "包装一般般，没什么特别。",
    "这服务真'好'啊，让我等了一小时。",
    "饭还行，没让我惊艳但也不踩雷。",
]


def main():
    banner("Demo 2 · Few-shot Sentiment Classification")
    for s in SAMPLES:
        print(f"\n输入: {s}\n输出: {classify_few_shot(s)}")


if __name__ == "__main__":
    main()
