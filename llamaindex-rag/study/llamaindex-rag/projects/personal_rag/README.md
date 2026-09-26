# 最小完整个人知识库 RAG

把自己的 `.txt` / `.md` / `.pdf` 放进 `data/personal/`。

运行：

```bash
python awesome-agentic-ai-zh/llamaindex-rag/projects/personal_rag/app.py
```

数据流：

```text
TXT / MD / PDF
      ↓
Document
      ↓
SentenceSplitter
      ↓
Node
      ↓
Embedding
      ↓
VectorStoreIndex
      ↓
Retriever (Top-K)
      ↓
Context
      ↓
LLM
      ↓
Answer + Sources
```

默认参数：`chunk_size=512`、`chunk_overlap=50`、`similarity_top_k=3`。
