# AI Agent Lab 项目基础范式

后续学习新的 AI / Agent / RAG / Framework 技术时，请优先基于我现有项目：

```text
ai-agent-lab/
```

进行组织和扩展，不要默认新建独立仓库。

## 基础环境

默认沿用当前项目环境：

```text
Python: 3.12+
依赖管理: pip + requirements.txt
环境变量: .env
公共配置: 根目录 config.py
```

如果新技术有特殊要求，再单独调整。

---

## 模型配置

默认优先沿用当前模型体系：

```text
Provider: DashScope

LLM:
qwen-max

Embedding:
text-embedding-v4

Reranker:
gte-rerank
```

统一通过：

```text
DASHSCOPE_API_KEY
```

访问。

如果某项技术需要其他模型，再根据实际情况增加，不强制限定。

---

## 配置规范

API Key 和模型名称尽量放在：

```text
.env
```

例如：

```env
DASHSCOPE_API_KEY=

LLM_MODEL=qwen-max
EMBED_MODEL=text-embedding-v4
RERANK_MODEL=gte-rerank
```

避免把 Key、模型名称、Base URL 等配置硬编码在 Demo 中。

---

## 目录规范

新的学习主题优先放在：

```text
ai-agent-lab/
    └── <topic-name>/
```

推荐基础结构：

```text
<topic-name>/
├── README.md
├── requirements.txt
├── settings.py
├── data/
├── storage/
├── 01_xxx.py
├── 02_xxx.py
├── 03_xxx.py
└── projects/
```

不要求所有目录都存在，根据主题实际需要增减。

---

## 文件职责

```text
README.md
```

记录该主题的核心概念、学习路线和运行方式。

```text
requirements.txt
```

只放该主题额外需要的依赖。

```text
settings.py
```

放该主题公共的模型、框架和配置初始化。

```text
data/
```

放实验输入数据。

```text
storage/
```

放索引、向量库、缓存等运行产物。

```text
01_xxx.py
02_xxx.py
```

按照学习顺序保存独立实验代码。

```text
projects/
```

放相对完整的实战项目。

---

## Git 规范

以下内容通常不提交：

```text
.env
.venv/
__pycache__/
storage/
chroma_db/
运行缓存
本地数据库
```

配置模板可以提交：

```text
.env.example
```

---

## 使用原则

开始学习一个新技术时，先结合当前 `ai-agent-lab`：

```text
确认版本
→ 确认依赖
→ 确认模型
→ 确认配置
→ 确认存放位置
→ 再开始学习和实验
```

优先复用现有工程方式；只有确实有必要时，再引入新的模型供应商、依赖管理方式或项目结构。
