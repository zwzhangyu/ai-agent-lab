# AI Agent Lab

AI 智能体学习与实验项目集合，涵盖 LLM 基础实验、提示词工程、ReAct Agent 构建等方向。

## 项目结构

```
ai-agent-lab/
├── awesome-agentic-ai-zh/          # AI Agent 系列实验
│   ├── llm-intro/                   # LLM 基础实验
│   ├── prompt/                      # 提示词工程实验
│   └── react-agent-from-scratch/    # 从零构建 ReAct Agent
├── python/                          # Python 技术演示
│   └── pkgutil_demo/                # pkgutil 动态模块加载演示
├── config.py                        # 全局环境配置（代理绕过 + .env 加载）
├── requirements.txt                 # 根目录公共依赖
└── .env                             # 环境变量配置（API Keys 等）
```

## 主要项目

### 1. LLM 基础实验 (`awesome-agentic-ai-zh/llm-intro`)

通过 DashScope API 调用通义千问 `qwen-max` 模型，验证 LLM 的关键参数行为：

- **max_tokens 限制**：观察输出截断与 Token 用量
- **temperature=0 一致性**：连续多次调用，验证低温下的输出稳定性
- **中英文 Token 对比**：对比相同语义下中文与英文的 Token 消耗差异

### 2. 提示词工程实验 (`awesome-agentic-ai-zh/prompt`)

以中文电影评论情感分类为任务，对比 **Zero-Shot** 与 **Few-Shot (3-Shot)** 的分类准确率：

- 20 条标注评论数据集，涵盖反讽、混合情感、网络用语等边界案例
- 自动统计准确率并输出对比结论

### 3. ReAct Agent from Scratch (`awesome-agentic-ai-zh/react-agent-from-scratch`)

从零构建的 **ReAct (Reasoning + Acting)** 智能体，不依赖任何 Agent 框架：

- **核心循环**：Thought → Action → PAUSE → Observation，迭代推理直至输出 Final Answer
- **动态工具注册**：基于 `pkgutil` 自动发现并加载 `tools/` 目录下的工具，内置工具包括：
  - `calculator` — 数学运算（加减乘除、幂、取模）
  - `weather` — 实时天气查询（OpenWeatherMap API）
  - `web_search` — 网络搜索（Tavily API）
  - `wikipedia` — 维基百科知识检索
- **记忆管理**：Token 超限时自动摘要旧对话，压缩上下文
- **双端入口**：
  - CLI 交互模式 — `python agent.py`
  - Streamlit Web UI — `streamlit run web_app.py`，侧边栏实时展示思维链

### 4. pkgutil 动态加载演示 (`python/pkgutil_demo`)

演示 Python `pkgutil.iter_modules` + `importlib` 实现目录级模块自动发现与动态加载的机制。

## 环境配置

1. 复制环境变量模板并填入 API Key：

   ```bash
   cp .env.example .env
   ```

2. 安装依赖：

   ```bash
   # 根目录公共依赖
   pip install -r requirements.txt

   # ReAct Agent 额外依赖
   pip install -r awesome-agentic-ai-zh/react-agent-from-scratch/requirements.txt
   ```

3. 项目使用 `NO_PROXY=*` 绕过代理以直连国内 API，已在 `config.py` 中统一配置。

## 技术栈

- **语言**：Python 3.12+
- **LLM**：通义千问 qwen-max（DashScope OpenAI 兼容接口）
- **Web 框架**：Streamlit
- **关键依赖**：openai、tiktoken、tavily-python、wikipedia-api、colorama、python-dotenv
