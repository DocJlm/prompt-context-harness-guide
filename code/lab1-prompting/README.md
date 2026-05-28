# Lab 1 · Prompt Patterns

第 1 章配套实验。5 个 demo 让你亲手把 Prompt Engineering 的核心模式跑一遍。

## 准备

```bash
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，默认走 OpenAI
export MODEL=gpt-4o-mini                            # 可选，默认 gpt-4o-mini
```

**国内模型示例**（DeepSeek）：

```bash
export OPENAI_BASE_URL=https://api.deepseek.com/v1
export OPENAI_API_KEY=<deepseek-key>
export MODEL=deepseek-chat
```

## Demo 列表

| # | 文件 | 主题 |
| :---: | :--- | :--- |
| 1 | `01_zero_shot.py` | Zero-shot baseline |
| 2 | `02_few_shot.py` | Few-shot 多样性示例 |
| 3 | `03_cot.py` | Chain-of-Thought |
| 4 | `04_structured_output.py` | JSON Schema 强制输出 |
| 5 | `05_eval_loop.py` | Golden set + acc 评估 |

## 跑

```bash
python 01_zero_shot.py
python 02_few_shot.py
python 03_cot.py
python 04_structured_output.py
python 05_eval_loop.py
```

## 学习路径

按顺序跑。每个 demo 跑完，**对照 [§1.2 七大模式](../../docs/zh-cn/01-prompt-engineering/02-patterns.md) 里描述的"观察什么"做笔记**，然后做 [§1.5 实验作业](../../docs/zh-cn/01-prompt-engineering/05-lab.md#实验作业)。
