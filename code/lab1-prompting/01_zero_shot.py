"""Demo 1 · Zero-shot 情感分类

观察什么：
1. 输出通常不止一个词——模型会自由发挥。
2. 把 temperature 改成 1.5 跑 5 次，结果开始随机。
3. 加一句反讽测试，看 zero-shot 是否能识别。
"""
from _common import get_client, MODEL, banner

client = get_client()

SAMPLES = [
    "这家店服务真差，菜也凉了。",
    "我超级喜欢这本书！",
    "包装一般般，没什么特别。",
    "这服务真'好'啊，让我等了一小时。",  # 反讽
]


def classify(text: str, temperature: float = 0.0) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是一个情感分类器。"},
            {"role": "user", "content": f"请将这条评论分类为 positive / negative / neutral：\n\n{text}"},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def main():
    banner("Demo 1 · Zero-shot Sentiment Classification")
    for s in SAMPLES:
        result = classify(s)
        print(f"\n输入: {s}\n输出: {result}")

    print("\n--- 同一句话，temperature=1.5 跑 3 次：")
    for i in range(3):
        print(f"  Run {i+1}: {classify(SAMPLES[3], temperature=1.5)}")


if __name__ == "__main__":
    main()
