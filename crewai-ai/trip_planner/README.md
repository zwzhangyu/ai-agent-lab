# Trip Planner Crew（旅行规划智能体团队）

这是一个仿照 CrewAI 官方示例
[`crews/trip_planner`](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/trip_planner)
搭建的多智能体（multi-agent）项目，并**针对你的本地环境做了适配**：
把默认的大模型从 OpenAI 换成了阿里云 DashScope（通义千问），
把搜索工具从 Serper 换成了 Tavily。

你只要给它：出发地、候选城市、出行日期、兴趣爱好，
它就会组织 3 个 Agent 依次协作，最终产出一份完整的 Markdown 旅行行程。

---

## 一、这个项目里的“团队”是怎么分工的

```
main.py 收集用户输入
      │
      ▼
┌──────────────────────────────────────────────────────────┐
│  Crew（顺序执行 Process.sequential，前一个任务的输出       │
│        会自动作为上下文传给后一个任务）                     │
│                                                            │
│  ① 城市选择专家  →  identify_task：从候选城市里选出最佳目的地 │
│  ② 当地城市专家  →  gather_task：产出目的地深度攻略           │
│  ③ 金牌旅行管家  →  plan_task：产出 7 日逐日行程 + 预算       │
└──────────────────────────────────────────────────────────┘
      │
      ▼
   打印结果，并保存到 trip_plan.md
```

三个 Agent 都能使用工具：
- `SearchTools.search_internet`：联网搜索（Tavily）
- `BrowserTools.scrape_and_summarize_website`：抓取并总结网页
- `CalculatorTools.calculate`：做预算相关的数学计算（仅旅行管家使用）

---

## 二、目录结构

```
trip_planner/
├── main.py              # 入口：收集输入 → 组建 Crew → kickoff()
├── trip_agents.py       # 定义 3 个 Agent（角色/目标/工具）
├── trip_tasks.py        # 定义 3 个 Task（描述/期望产出）
├── llm_config.py        # 统一配置 DashScope LLM + 加载 .env + 绕过代理
├── requirements.txt     # 依赖清单
├── .env.example         # 需要的密钥清单（模板）
└── tools/               # 自定义工具
    ├── __init__.py
    ├── search_tools.py      # Tavily 网络搜索
    ├── browser_tools.py     # requests + BeautifulSoup 抓取并总结网页
    └── calculator_tools.py  # 安全的数学表达式计算
```

---

## 三、与原示例的差异（为什么这么改）

| 位置 | 原示例 | 本项目 | 原因 |
|------|--------|--------|------|
| LLM | 默认 OpenAI | DashScope / 通义千问（`llm_config.py`） | 你已有 `DASHSCOPE_API_KEY` |
| 搜索工具 | Serper(`SERPER_API_KEY`) | Tavily(`TAVILY_API_KEY`) | 你已有 Tavily key，无需再注册 Serper |
| 网页工具 | Browserless + unstructured | requests + BeautifulSoup | 免注册、少一个重依赖 |
| 环境加载 | `load_dotenv()`（当前目录） | 根目录绝对路径 + `NO_PROXY='*'` | 与仓库现有规范一致，防止国内 API 走代理报错 |

代码组织方式（`trip_agents.py` / `trip_tasks.py` / `main.py` / `tools/`）
与原示例保持一致，方便你对照学习。

---

## 四、如何运行

### 1. 准备密钥
确认仓库根目录的 `ai-agent-lab/.env` 中已有（本项目会自动读取它）：
```
DASHSCOPE_API_KEY=你的通义千问密钥
TAVILY_API_KEY=你的Tavily密钥
```

### 2. 安装依赖
在 `LangChainCode` conda 环境下（crewai 0.79.4 已就绪）：
```bash
conda run -n LangChainCode pip install -r crewai-ai/trip_planner/requirements.txt
```

### 3. 启动（务必先进入项目目录，保证 `from tools...` 能正确导入）
```bash
cd crewai-ai/trip_planner
```

**⚠️ 关于交互式输入**：`conda run python main.py` 不会把键盘输入(stdin)转发给脚本，
会让 `input()` 抛 `EOFError`。因此有两种正确跑法：

**方式一 · 交互式**（先激活环境，再用真实终端运行，可直接敲键盘输入）：
```bash
conda activate LangChainCode
python main.py
```

**方式二 · 命令行传参**（无需交互，适合脚本 / IDE 运行）：
```bash
conda run --no-capture-output -n LangChainCode python main.py \
    --origin 北京 --cities "东京,大阪" \
    --date-range "10.1-10.7" --interests 美食,购物
```

> 更推荐直接用环境里的 python，日志会实时刷出：
> `/Users/zhangyu/miniconda3/envs/LangChainCode/bin/python main.py ...`

**⚠️ 重要**：`conda run` 默认会**捕获子进程的 stdout**，导致 CrewAI 的
`verbose` 日志不实时输出，看起来像“卡死几分钟没反应”（其实际在正常跑）。
因此必须加 `--no-capture-output`，或干脆用上面环境的 python 直连跑。
另外：本任务 3 个 Agent 串行 + 多次 LLM/联网调用，**跑 3~8 分钟属正常**。

两种方式都会依次驱动三个 Agent 协作，最终打印行程并保存为 `trip_plan.md`。

---

## 五、学习提示

- `verbose=True` 会把每个 Agent 的思考/工具调用过程打印出来，是理解
  CrewAI 协作机制最好的窗口。
- 顺序执行下任务间的“接力”（前一个任务输出自动进后一个任务上下文），
  是本项目能“基于攻略再排行程”的关键。
- 想改成用别的大模型：设置环境变量 `CREWAI_MODEL`，例如
  `CREWAI_MODEL=openai/qwen-plus`。
