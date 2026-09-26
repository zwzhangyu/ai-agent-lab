"""应用内的可配置项定义。"""
from dataclasses import dataclass

from app.config import LLM_MODEL


@dataclass
class AppSettings:
    """会话内生效的检索与回答设置，由各视图中的控件直接读写。"""

    # 检索参数
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 3
    similarity_cutoff: float = 0.3
    # 模型与回答方式
    llm_model: str = LLM_MODEL
    deep_thinking: bool = False
    web_search: bool = False
