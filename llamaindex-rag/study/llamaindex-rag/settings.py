import os
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.dashscope import DashScope
from llama_index.embeddings.dashscope import DashScopeEmbedding


def _find_project_root() -> Path:
    """优先寻找 ai-agent-lab 根目录的 .env / .git。"""
    current = Path(__file__).resolve().parent
    for candidate in [current, *current.parents]:
        if (candidate / ".env").exists() or (candidate / ".git").exists():
            return candidate
    return current


PROJECT_ROOT = _find_project_root()
load_dotenv(PROJECT_ROOT / ".env", override=False)


def setup_llamaindex() -> None:
    """统一初始化 LlamaIndex 的 LLM 与 Embedding 模型。"""
    # DashScope LLM 类不会自动读取 DASHSCOPE_API_KEY 环境变量，
    # 必须显式传入 api_key，否则抛 pydantic ValidationError。
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未找到 DASHSCOPE_API_KEY。请在 ai-agent-lab 根目录 .env 中配置，"
            "或复制本目录 .env.example 为 .env。"
        )

    llm_model = os.getenv("LLM_MODEL", "qwen-max")
    embed_model = os.getenv("EMBED_MODEL", "text-embedding-v4")

    Settings.llm = DashScope(model_name=llm_model, api_key=api_key)
    Settings.embed_model = DashScopeEmbedding(model_name=embed_model, api_key=api_key)
