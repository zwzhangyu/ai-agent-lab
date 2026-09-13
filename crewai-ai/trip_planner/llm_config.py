"""统一的 LLM 与环境配置。

被 trip_agents.py 与 tools/ 下的模块共同导入：
只要 import 本模块，就会自动完成 .env 加载与代理绕过，
从而保证无论从哪个目录运行，密钥都能正确读到。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from crewai.llm import LLM

# 绕过本地代理，国内 API（DashScope）直连，避免 RemoteDisconnected
os.environ["NO_PROXY"] = "*"

# 加载项目根目录（ai-agent-lab/）下的 .env 文件
# 本文件位于 crewai-ai/trip_planner/llm_config.py
# parents[0]=trip_planner  parents[1]=crewai-ai  parents[2]=ai-agent-lab（根目录）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)

# 默认使用通义千问 qwen-max（DashScope 的 OpenAI 兼容接口）
# 可通过环境变量 CREWAI_MODEL 覆盖，例如：CREWAI_MODEL=openai/qwen-plus
DEFAULT_MODEL = os.getenv("CREWAI_MODEL", "openai/qwen3.7-max")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def get_llm(temperature: float = 0.7) -> LLM:
    """返回一个配置好 DashScope / 通义千问 的 CrewAI LLM 实例。"""
    return LLM(
        model=DEFAULT_MODEL,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base=DASHSCOPE_BASE_URL,
        temperature=temperature,
    )
