# Lab 3 · Mini Harness

第 3 章配套实验。**纯 Python**（不依赖 LangGraph / LangChain）从零造一个 mini Harness。

## 准备

```bash
pip install -r requirements.txt

export OPENAI_API_KEY=sk-xxxxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # 可选
export MODEL=gpt-4o-mini
```

## Demo 列表

| # | 文件 | 主题 |
| :---: | :--- | :--- |
| 1 | `01_tool_loop.py` | 100 行实现 ReAct Tool Loop |
| 2 | `02_hooks.py` | 加 Middleware：日志 + 危险命令拦截 |
| 3 | `03_subagent.py` | 加 Sub-agent（外包搜索任务） |
| 4 | `04_progress.py` | 加 Progress 持久化 + Session 恢复 |
| 5 | `05_real_task.py` | 跑一个真实任务：为 fake_project 写 README |

## 跑

```bash
python 01_tool_loop.py
python 02_hooks.py
python 03_subagent.py
python 04_progress.py
python 04_progress.py --resume    # 恢复上一个 session
python 05_real_task.py
```
