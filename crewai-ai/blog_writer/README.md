# 【CrewAI实践】多智能体技术博客生成工具

## 一、为什么要让两个 Agent 协作

让单个大模型「写一篇 Python 数据清洗的技术博客」，输出往往不太稳定：可能缺一段能跑的代码，可能结构松散，也可能夹带过时的写法。问题在于它得同时扮演两个角色——既要把资料查准，又要把文章写顺，两头很难兼顾。

CrewAI 的思路是把这两个目标拆开，交给两个角色：

- 技术研究员：只负责把主题研究透，给出分类清晰、带可运行代码的研究报告；
- 技术博客作家：不关心资料从哪来，只负责把研究报告改写成一篇适合初学者阅读的文章。

两个角色接力：研究员先把主题研究透，作家再拿着报告动笔，跑完就得到一篇 Markdown 博客。把它写成代码而不是每次手敲提示词，好处是流程固化了下来，换个主题照样能跑。

CrewAI 把多 Agent 协作里最繁琐的部分——谁先谁后、上一个任务的输出怎么传给下一个、每一步的上下文怎么维护——都封装好了，几十行就能搭起一条完整的协作链。下面从上到下把它拆开看。

## 二、CrewAI 的几个核心概念

动手前先把四个名词对齐，后面的代码无非是它们的组合：

- **LLM**：一个 Agent 用哪个大模型。CrewAI 基于 LiteLLM，只要给个兼容 OpenAI 协议的 `model` + `api_base` 就能接各种模型。
- **Agent**：一个角色。由 `role`（头衔）、`goal`（目标）、`backstory`（行事风格）三段文本定义，再挂上一个 LLM 和若干工具。
- **Task**：一项工作。由 `description`（要做什么）、`expected_output`（要交付什么）定义，指定交给哪个 Agent，还能声明依赖哪些前置任务的产出（`context`）。
- **Crew**：团队。把若干 Agent 和若干 Task 装进去，选一种执行流程（`process`），`kickoff()` 开跑。

执行流程用的是默认的 `Process.sequential`：任务按列表顺序依次执行，前一个任务的输出会自动带进后一个任务的上下文。研究员写完报告、作家接着拿报告动笔，靠的就是这个机制。

## 三、项目结构

```
blog_writer/
├── main.py            # 入口：解析参数 → 组装 Crew → 运行并保存结果
├── blog_agents.py     # Agent 定义（技术研究员 / 技术博客作家）
├── blog_tasks.py      # Task 定义（研究 / 写作）
├── llm_config.py      # LLM 与运行环境配置（.env 加载、代理绕过）
├── requirements.txt   # 依赖
└── .env.example       # 所需密钥模板
```

仓库地址：https://github.com/zwzhangyu/ai-agent-lab

当前项目目录：crewai-ai/blog_writer

结构上分得很清楚：Agent、Task、LLM 配置各占一个文件，`main.py` 只负责组装和运行。LLM 和环境配置单独抽到 `llm_config.py`，是因为密钥加载、代理绕过这些细节容易出错，写一遍就够；`blog_agents.py` 要用模型时一句 `from llm_config import get_llm` 就行，不用到处翻 `os.getenv`。

## 四、最小版本：一个 Crew 到底怎么跑

先抛开分层，用一个单文件的最小版本看清协作的骨架（模型走 DashScope 的 OpenAI 兼容接口）：

```python
from crewai import Agent, Task, Crew
from crewai.llm import LLM

llm = LLM(
    model="openai/qwen3.7-max",
    api_key="...",                                          # DASHSCOPE_API_KEY
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

researcher = Agent(
    role="技术研究员", goal="调研主题并给出可运行代码",
    backstory="注重事实与可复现性", llm=llm,
)
writer = Agent(
    role="技术博客作家", goal="把研究结果写成入门文章",
    backstory="擅长拆解复杂概念", llm=llm,
)

research = Task(
    description="深入研究：Python 数据清洗（缺失值、重复值、格式不一致）",
    agent=researcher, expected_output="一份含可运行代码的研究报告",
)
write = Task(
    description="基于研究报告撰写入门级技术博客",
    agent=writer, context=[research],                       # 关键：报告喂给作家
    expected_output="不少于 800 字的 Markdown 技术博客",
)

result = Crew(agents=[researcher, writer], tasks=[research, write]).kickoff()
print(result.raw)
```

整个协作的核心就是 `context=[research]` 这一行：作家任务声明了依赖研究任务的产出，CrewAI 就会在轮到 `write` 之前，把 `research` 的最终输出拼进它的上下文。两个 Agent 之间传递的就是这份报告，彼此都看不到对方的提示词和中间过程。

`Crew` 不显式指定 `process` 时默认就是 `sequential`，任务顺序即列表顺序。

## 五、完整实现

### 5.1 LLM 与环境配置：把坑收敛到一处

`llm_config.py` 干两件事：加载密钥、绕过代理。

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from crewai.llm import LLM

# DashScope 为国内接口，直连即可；绕过本地代理以避免连接中断
os.environ["NO_PROXY"] = "*"

# 仓库根目录：blog_writer -> crewai-ai -> ai-agent-lab
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)

DEFAULT_MODEL = os.getenv("CREWAI_MODEL", "openai/qwen3.7-max")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def get_llm(temperature: float = 0.7) -> LLM:
    return LLM(
        model=DEFAULT_MODEL,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base=DASHSCOPE_BASE_URL,
        temperature=temperature,
    )
```

有两处细节容易被忽略。

第一处是密钥加载的路径。`load_dotenv()` 不带参数时只会到当前工作目录找 `.env`，而项目必须在 `blog_writer/` 下运行（不然 `from blog_agents import ...` 导不进来），密钥却统一放在仓库根目录。解决办法是用 `Path(__file__).resolve().parents[2]` 从文件自己的位置回溯到根目录，这样不管从哪启动，读到的都是同一份 `.env`。`override=True` 让 `.env` 里的值盖掉系统中可能残留的同名变量。

第二处是 `NO_PROXY="*"`。本地挂着 HTTP 代理（比如 7890 端口）时，请求 DashScope 会被代理绕一圈，经常直接 `RemoteDisconnected`。绕过代理直连就行。这段逻辑只在模块导入时执行一次，`blog_agents.py` 里完全感觉不到。

### 5.2 两个 Agent：区别只在 allow_delegation

```python
from crewai import Agent
from llm_config import get_llm

class BlogAgents:
    def researcher(self):
        return Agent(
            role="技术研究员",
            goal="寻找最新、准确、可验证的技术资料，并给出代码证明。",
            backstory="擅长系统性分析技术问题，注重事实和可复现性。",
            llm=get_llm(), verbose=True, allow_delegation=False,
        )

    def writer(self):
        return Agent(
            role="技术博客作家",
            goal="将研究成果整理成适合初学者阅读的技术文章。",
            backstory="擅长将复杂概念拆解为清晰步骤，并提供完整示例。",
            llm=get_llm(), verbose=True, allow_delegation=True,
        )
```

三个文本字段 `role` / `goal` / `backstory` 会拼进这个 Agent 每一轮的系统提示，模型「知道自己是干嘛的」全靠它们。想调行为，改这几句话比改代码更有效。

`allow_delegation` 决定一个 Agent 能不能把子任务交给团队里的其他 Agent。研究员设成 `False`，只能自己完成；作家设成 `True`，遇到拿不准的技术细节可以回头找研究员确认。这个开关主要在 `Process.hierarchical` 或明确开启协作时才起作用，本项目走的是顺序流程，给作家开 `True` 更多是留个余地。两个 Agent 各自 `get_llm()` 出一个实例，温度都是默认的 0.7。

### 5.3 两个 Task：description 与 expected_output 的分工

```python
from textwrap import dedent
from crewai import Task

class BlogTasks:
    def research_task(self, agent, topic):
        return Task(
            description=dedent(f"""
                深入研究主题：{topic}。
                覆盖该主题的常见痛点、核心概念与最佳实践，
                并给出完整、可运行的代码示例佐证结论。
            """),
            agent=agent,
            expected_output="一份研究报告，包含问题分类、解决方案代码和完整落地流程。",
        )

    def write_task(self, agent, topic, title, context):
        return Task(
            description=dedent(f"""
                基于研究团队提供的报告，围绕主题「{topic}」撰写一篇入门级技术博客。
                文章标题：《{title}》。
                要求结构清晰、示例完整，适合初学者阅读。
            """),
            agent=agent, context=context,
            expected_output="不少于 800 字的 Markdown 技术博客。",
        )
```

`description` 说明任务怎么做，`expected_output` 说明交付物长什么样，两者都会进入模型上下文。主题（`topic`）和标题（`title`）做成参数而不是写死在提示词里，是为了复用：同一个 Crew，换个 topic 就能产出另一主题的博客，默认用的是「Python 数据清洗」。

`context` 由调用方传入（`main.py` 里是 `[research_task]`），把研究任务显式声明成写作任务的前置依赖。顺序流程里这本来就是默认行为，但还是写了出来：读者一眼能看到数据从哪来，将来真要换执行流程，这条依赖也不会莫名其妙断掉。

### 5.4 组装 Crew 与入口

`main.py` 把上面三块拼起来，再套一层命令行。`BlogCrew` 只负责组装和运行：

```python
class BlogCrew:
    def __init__(self, topic, title):
        self.topic = topic
        self.title = title

    def run(self):
        agents, tasks = BlogAgents(), BlogTasks()
        researcher, writer = agents.researcher(), agents.writer()

        research_task = tasks.research_task(researcher, self.topic)
        write_task = tasks.write_task(writer, self.topic, self.title, context=[research_task])

        crew = Crew(
            agents=[researcher, writer],
            tasks=[research_task, write_task],
            process=Process.sequential, verbose=True,
        )
        return crew.kickoff()
```

入口支持交互式输入，也支持命令行传参，命令行优先：

```python
def _ask(prompt, value=None, default=None):
    if value:                                   # 命令行已传参，直接用
        return value
    try:
        answer = input(prompt).strip()
    except EOFError:                            # 无 tty 时回退默认值
        if default is not None:
            return default
        raise SystemExit("无法读取标准输入，请改用命令行参数")
    return answer or default
```

`except EOFError` 这个兜底是被环境逼出来的。用 `conda run` 跑脚本时，conda 不会把键盘输入（stdin）转发给子进程，`input()` 会直接抛 `EOFError`。所以拿不到输入时就用默认主题，保证在脚本、IDE 这类无交互场景里也不会崩。想要真正的交互输入，就先激活环境再 `python main.py`。

## 六、运行方式

先在仓库根目录 `.env` 里配好密钥（`llm_config.py` 会自动向上查找加载）：

```
DASHSCOPE_API_KEY=你的通义千问密钥
```

装依赖，然后在项目目录下运行（务必 `cd` 进来，保证 `from blog_agents ...` 能导入）：

```bash
cd crewai-ai/blog_writer
pip install -r requirements.txt

python main.py                                  # 交互式，直接回车用默认主题
python main.py --topic "Redis 持久化机制" \
    --title "Redis 持久化入门" --output redis_blog.md   # 命令行传参
```

`verbose=True` 会把每个 Agent 的思考和产出都打印出来，方便观察整条链。两个 Agent 串行、多次调用大模型，跑几分钟是正常的。换模型只需设 `CREWAI_MODEL`，例如 `CREWAI_MODEL=openai/qwen-plus`。

## 七、运行示例

开着 `verbose` 跑，终端里能看到两个 Agent 依次接力的过程（示意，具体文字以模型输出为准）：

```
# Agent: 技术研究员
## Task: 深入研究主题：使用 Python 进行自动化数据清洗……
[研究员输出] 一份研究报告：
  一、缺失值：df.isna().sum() 统计，dropna()/fillna(中位数) 处理……
  二、重复值：df.drop_duplicates(subset=['emp_id'], keep='first')……
  （附完整可运行的 DataCleaner 清洗流水线代码）

# Agent: 技术博客作家
## Task: 基于研究报告撰写入门级技术博客《Python 数据清洗入门……》
[作家输出] # Python 数据清洗入门：用 pandas 告别脏数据
  ……把研究报告改写成面向初学者的文章，保留可运行代码……
```

作家这段的内容来自研究员上一轮的报告：框架在轮到 `write` 之前把报告作为 context 塞了进去，作家只管写，不用自己再查资料。最终结果会打印到终端，同时存成 `python_data_cleaning_blog.md`。

同一个 `blog_writer`，换个 `--topic` 就能得到另一篇博客。Agent 和 Task 的骨架没动，变的只是传进去的主题和标题。写一次、之后反复套用，这就是把流程固化成代码的价值。

---

仓库地址：https://github.com/zwzhangyu/ai-agent-lab

当前项目目录：crewai-ai/blog_writer
