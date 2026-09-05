import os
from pathlib import Path
from dotenv import load_dotenv

# 绕过代理，国内 API 直连
os.environ["NO_PROXY"] = "*"

# 加载项目根目录下的 .env 文件
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / '.env', override=True)
