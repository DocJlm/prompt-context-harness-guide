---
title: Chapter 1 · Prompt Engineering
description: Saying instructions clearly — the first layer of muscle for LLM app development
---

# Chapter 1 · Prompt Engineering: Saying Instructions Clearly

> "GPT-5 is an excellent metaprompting partner — using the model to improve its own prompts. It generally needs less scaffolding, and shorter, clearer instructions tend to work better."  
> — OpenAI, *GPT-5 Prompting Guide*

## Chapter Guide

⏱️ **Reading time**: ~90 minutes  
🎯 **By the end you will**: be able to write a production-grade prompt that "any model can follow," and iterate on it with Eval-driven discipline.  
🧪 **Companion lab**: [Lab 1 · prompt_patterns](../../../code/lab1-prompting/)

## Chapter Structure

| Section | Topic | Focus |
| :---: | :--- | :--- |
| [§1.1](./01-fundamentals.md) | **The Anatomy of a Prompt** | System / User / Assistant, Role, Delimiter, Output Format |
| [§1.2](./02-patterns.md) | **The Seven Patterns** | Zero-shot · Few-shot · CoT · Self-Consistency · Tree-of-Thought · ReAct · Structured Output |
| [§1.3](./03-advanced.md) | **Advanced: Meta-prompting & the GPT-5 era** | Reasoning Effort · Agentic Eagerness · Tool Preambles · Persistence |
| [§1.4](./04-evaluation.md) | **Evaluation & Iteration** | How do you know your prompt is good? |
| [§1.5](./05-lab.md) | **Hands-on Lab** | Run all five Lab 1 demos |
| [§1.6](./references.md) | **References** | First-party source links |

## One Paragraph: What This Chapter Solves

**Prompt Engineering is the craft of "writing programs in natural language."**  
Its output is one (or several) model instructions, and the goal is to get the model to produce **format-conformant, accurate, repeatable** output in a **single inference**.

Its boundary is just as clear: when the problem becomes "how to not forget across many turns," "how to pick the right content from 1000 documents," "how to make the model use tools"—that's already Chapter 2 and Chapter 3 territory.

But **without the muscle of writing good prompts**, the engineering of the next two chapters can't even be set up: the System Prompt is the first brick of Context Engineering, the Tool Description is the first brick of Harness Engineering, and both are essentially prompts.

## Mental Model: A Prompt = A Dish's Recipe

| Prompt Element | Recipe Analogy |
| :--- | :--- |
| **Role** | "You are a three-Michelin-star chef" |
| **Task** | "Make a four-serving Italian beef bolognese pasta" |
| **Constraints** | "Total time < 30 minutes, only ingredients available in a home kitchen" |
| **Examples / Few-shot** | "You can reference these two sample recipes below..." |
| **Output Format** | "Output in three sections: [Ingredients / Steps / Notes]" |
| **Reasoning hint** | "Before writing the steps, think through the critical timing" |

When writing a recipe, missing any one element causes problems:
- No "Michelin chef" — you might get an edible but mediocre dish.
- No "4 servings" — quantities are uncontrolled.
- No "30 minutes" — you might get a dish that requires 8 hours of simmering.
- No examples — style is random.
- No output format — you get prose, not something you can import into an ordering system.

In the next few sections, we'll **bring each of these to production quality**.

---

Next: [§1.1 The Anatomy of a Prompt →](./01-fundamentals.md)
