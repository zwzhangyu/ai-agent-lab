# 我的 AI Agent 学习笔记（示例）

## 当前学习路线

当前重点是理解 RAG 的基础数据流：
Document -> Node -> Embedding -> Retriever -> Context -> LLM -> Answer。

学习 LlamaIndex 时，优先理解底层通用原理，而不是记忆大量 API。

## 项目约定

实验项目统一使用 Python。
模型服务优先使用 DashScope。
LLM 默认使用 qwen-max。
Embedding 默认使用 text-embedding-v4。

## 学习原则

每个主题先运行一个最小 Demo，再拆解框架内部的数据流。
实验代码尽量保持简单、可独立运行、方便后续复习。
