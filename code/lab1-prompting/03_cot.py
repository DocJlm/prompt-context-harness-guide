"""Demo 3 · Chain-of-Thought

要点：
- 给传统模型加 "请逐步推理" 通常能提 20-40 个百分点的多步推理准确率
- 给推理模型（GPT-5 / Claude 4.x / DeepSeek-R1）**不要加** —— 它们自带 CoT

跑 10 次平均看正确率差异。
"""
import re
from _common import get_client, MODEL, banner

client = get_client()

# 题目：原价 200 涨 20% 后再打 8 折，正确答案 192 元
QUESTION = "一个商品原价 200 元，先涨价 20%，再打 8 折，最终多少钱？只回答最终数字（带'元'单位）。"

PROMPT_NAIVE = QUESTION
PROMPT_COT = QUESTION + "\n\n请逐步推理（写出每一步的计算过程），最后再给出最终答案。"


def ask(prompt: str, temperature: float = 0.7) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def parse_answer(text: str) -> int | None:
    """从输出里抓最后一个数字。"""
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if not numbers:
        return None
    return int(float(numbers[-1]))


def main():
    banner("Demo 3 · CoT vs Naive (correct answer: 192)")
    N = 10

    for name, prompt in [("Naive", PROMPT_NAIVE), ("CoT", PROMPT_COT)]:
        correct = 0
        print(f"\n--- {name} ({N} runs) ---")
        for i in range(N):
            answer_text = ask(prompt)
            answer = parse_answer(answer_text)
            ok = answer == 192
            if ok:
                correct += 1
            print(f"  Run {i+1}: {answer} {'✓' if ok else '✗'}")
        print(f"  → Accuracy: {correct}/{N} ({correct/N:.0%})")

    print("\n💡 CoT 通常显著好于 Naive。若你用的是推理模型（GPT-5/Claude 4.x/DeepSeek-R1），")
    print("   两者可能差异不大，因为推理模型自带 CoT。")


if __name__ == "__main__":
    main()
