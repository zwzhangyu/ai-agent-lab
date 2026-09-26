"""全局配置：从 .env 读取模型与路径参数，并确保数据目录存在。"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)

APP_TITLE = os.getenv("APP_TITLE", "HomeRag")
APP_SUBTITLE = os.getenv("APP_SUBTITLE", "你的个人知识库助手")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.7-max")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-v4")

# 底部输入框可快速切换的大语言模型（DashScope）
LLM_OPTIONS = ["qwen3.7-max", "qwen-max", "qwen-plus", "qwen-turbo"]
if LLM_MODEL not in LLM_OPTIONS:
    LLM_OPTIONS.insert(0, LLM_MODEL)

# text-embedding-v3/v4 单次请求最多 10 条文本，
# 而 DashScopeEmbedding 默认批大小 25 基于 v1/v2 限制，必须显式调小。
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "10"))

UPLOAD_DIR = ROOT_DIR / "data" / "uploads"
CHROMA_DIR = ROOT_DIR / "storage" / "chroma"
META_DIR = ROOT_DIR / "storage" / "meta"

for d in (UPLOAD_DIR, CHROMA_DIR, META_DIR):
    d.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".txt", ".md"
}

# 供 st.file_uploader 使用的扩展名列表（不带点）
UPLOAD_FILE_TYPES = [ext.lstrip(".") for ext in sorted(SUPPORTED_EXTENSIONS)]
