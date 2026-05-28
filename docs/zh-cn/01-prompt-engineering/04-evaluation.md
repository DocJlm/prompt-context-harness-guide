---
title: §1.4 评估与迭代
description: 怎么知道你的 prompt 是好的？以及怎么科学地改它
---

# §1.4 评估与迭代

> 没有 Eval 的 Prompt Engineering，等于没有单元测试的代码。

## 一、为什么必须 Eval？

**Prompt 是一种代码，但它是一种"概率代码"。**

- 普通代码：一个 bug 一个 bug 修。
- Prompt：改一行可能修一个 case、破三个 case。

不写测试的代码可以重构 1 次不出事，重构 5 次必出事。Prompt 也一样。

## 二、最小可行 Eval：手搓 Golden Set

第一版不用上 LangSmith、不用上 Promptfoo，**先用 20 行 Python 跑起来**：

```python
# eval_golden_set.py
import json
from openai import OpenAI

client = OpenAI()

GOLDEN_SET = [
    {"input": "登录页一直转圈进不去。", "expected": "bug"},
    {"input": "如果能加个夜间模式就完美了。", "expected": "feature"},
    {"input": "客服 5 分钟响应，太赞了！", "expected": "praise"},
    # ... 20-50 个 case
]

def run(prompt_template, case):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_template.format(input=case["input"])}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()

def evaluate(prompt_template, name):
    correct = 0
    failures = []
    for case in GOLDEN_SET:
        out = run(prompt_template, case)
        if case["expected"].lower() in out.lower():
            correct += 1
        else:
            failures.append({"input": case["input"], "expected": case["expected"], "got": out})
    acc = correct / len(GOLDEN_SET)
    print(f"[{name}] Accuracy: {acc:.1%}  ({correct}/{len(GOLDEN_SET)})")
    return acc, failures
```

**这就是最小 Eval Loop**。运行一次几毛钱，但能让你知道：

- 改完 prompt 是变好了还是变差了？
- 哪几个 case 一直跑不过？

## 三、Eval 的"四个度"

| 维度 | 衡量什么 | 例子 |
| :--- | :--- | :--- |
| **Correctness** | 答得对不对 | 分类对不对、抽取的字段值对不对 |
| **Format** | 格式合不合法 | JSON 能不能 parse、字段齐不齐 |
| **Style** | 风格符不符合 | 长度、语气、是否中英混用 |
| **Cost** | 多少 token / 多少钱 | 输入 / 输出 token、p99 延时 |

**生产 Eval 必须四个维度都看**。只看 Correctness 容易做出"准但贵但慢"的 prompt。

## 四、LLM-as-Judge：用模型评模型

当任务是开放式生成（摘要、改写、客服回复），没有 ground truth，怎么 eval？

**用一个更强 / 同等强的模型当裁判**：

```python
JUDGE_PROMPT = """你是一个严格的输出评估官。

任务说明：
{task_description}

模型输出：
{output}

请按以下维度评分（1-5 整数）：
- relevance（是否切题）
- factuality（事实正确性）
- format（格式合规）
- safety（无敏感内容）

仅输出 JSON：
{{"relevance": <int>, "factuality": <int>, "format": <int>, "safety": <int>, "comment": "<一句话原因>"}}
"""
```

::: 注意
- LLM-as-Judge **有偏差**：通常偏好长输出、偏好与裁判相同家族模型的风格。
- 解决：**用多个不同模型当 judge 投票**；**抽样人工校对** 10–20% 防止 judge 漂移。
- Anthropic 在 *Harness Design* 那篇里特意强调："agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre"。
:::

## 五、调试技巧：怎么定位失败原因

当一个 case 跑错，**先别急着改 prompt**。按下面顺序排查：

```
1. 模型本身能力够吗？
   → 换一个更强的模型试一次。还错 → 改 prompt；对了 → 看是否能用小模型 + 更好 prompt 解决。

2. 输入数据有问题吗？
   → 把同样的输入给一个人看，他能答对吗？
   → 数据噪声大 → 先清洗数据，不是改 prompt。

3. prompt 哪一句导致的？
   → 二分法删 prompt：删一半看是否还错。

4. 是 temperature 导致的偶发？
   → 设 temperature=0、固定 seed，跑 3 次。
   → 都一致 → 系统性问题；不一致 → 解码随机性问题。

5. 是 token 截断？
   → 看 max_tokens 是否打满。
```

## 六、Prompt 版本管理

**像管代码一样管 prompt**。哪怕只是把 prompt 放进 `.py` 文件并 git commit，也比写在 notebook cell 里强。

最小约定：

```python
# prompts/classify_v3.py
"""
Version: v3 (2026-05-28)
Author: zhang-san
Eval: 95.2% on golden_v2 (40 cases)
Notes:
  - v3 vs v2: 加了"短输入直接返回 other"的约束
  - v3 vs v1: 加了 self_check 字段
"""

PROMPT = """..."""
```

或者用专门工具：

- **Promptfoo**：开源，本地，类似 `jest` 的体验。
- **LangSmith**：LangChain 生态，云上 trace + eval。
- **Weights & Biases Prompts**：传统 ML 工具栈延伸。
- **PromptLayer / Helicone**：轻量级 prompt 日志。

::: 现实建议
**先把 prompt 进 git，再考虑工具。** 我见过太多团队用 LangSmith 但 prompt 还散在群聊里——本末倒置。
:::

## 七、迭代节奏：每次只改一处

```
v1: baseline
  ├─ eval: 76% correctness
  
v2: 加 few-shot examples
  ├─ eval: 84% correctness  ← 改一处
  
v3: 加 self_check 字段
  ├─ eval: 89% correctness, format 100%  ← 改一处
  
v4: 同时调 temperature + 改 system prompt
  ├─ eval: 87% correctness  ← 改了两处，回退一处不知道哪个有效
  
✗ 反例：v4 是反面教材
```

**每次 commit 只改一个变量**，可重复，可回退。

## 八、案例：把一个 prompt 从 70% 优化到 95%

下面是一个真实简化案例（情感分类任务）：

| Version | 改动 | Acc | 备注 |
| :---: | :--- | :---: | :--- |
| v1 | Zero-shot "判断情感" | 71% | baseline |
| v2 | + Role: "你是金融舆情分析师" | 74% | 角色让先验更准 |
| v3 | + Few-shot (3 例) | 82% | 含 1 例反讽边界 |
| v4 | + CoT "先列出关键词再判断" | 87% | 推理过程显式化 |
| v5 | + Structured Output + self_check | 91% | 格式合规 100% |
| v6 | + 把"中立"细化为"中立-正面倾向 / 中立-负面倾向" | 95% | 业务理解的胜利 |

注意 v6 不是 prompt 技巧的胜利，是**业务理解的胜利**——但需要 v1–v5 的工程肌肉先把 baseline 稳住，你才能看清是"业务细化"还能再提一截。

## 九、何时停下来？

- ✅ Acc / 指标 **连续两轮**没有显著提升。
- ✅ 失败 case **集中在边缘业务**，不在主流程。
- ✅ 调用成本 / 延时**进入预算**。
- ❌ 别再为了 +1% 把 prompt 写到 3000 字——**得不偿失，且更脆**。

**到这一步**：你已经 mastered 了 Prompt Engineering 的核心肌肉。下一步是 Context Engineering——但在那之前，**先动手把 Lab 1 跑一遍**。

---

下一节：[§1.5 动手实验 →](./05-lab.md)
