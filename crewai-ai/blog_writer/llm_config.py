"""LLM 与运行环境的集中配置。

导入本模块即会加载仓库根目录的 .env 并绕过本地代理，
使无论从哪个工作目录启动，密钥与网络都已就绪。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from crewai.llm import LLM

# DashScope 为国内接口，直连即可；绕过本地代理以避免连接中断
os.environ["NO_PROXY"] = "*"

# 仓库根目录：blog_writer -> crewai-ai -> ai-agent-lab
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)

# 默认模型可用环境变量 CREWAI_MODEL 覆盖，如 CREWAI_MODEL=openai/qwen-plus
DEFAULT_MODEL = os.getenv("CREWAI_MODEL", "openai/qwen3.7-max")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def get_llm(temperature: float = 0.7) -> LLM:
    """构造接入 DashScope（通义千问）的 CrewAI LLM 实例。"""
    return LLM(
        model=DEFAULT_MODEL,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base=DASHSCOPE_BASE_URL,
        temperature=temperature,
    )
