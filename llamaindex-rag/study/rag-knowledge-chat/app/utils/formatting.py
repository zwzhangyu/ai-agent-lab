"""UI 展示用的格式化工具。"""
from __future__ import annotations

from datetime import datetime, timedelta

_FILE_ICONS: dict[str, tuple[str, str]] = {
    ".pdf": (":material/picture_as_pdf:", "red"),
    ".doc": (":material/article:", "blue"),
    ".docx": (":material/article:", "blue"),
    ".ppt": (":material/slideshow:", "orange"),
    ".pptx": (":material/slideshow:", "orange"),
    ".xls": (":material/table_chart:", "green"),
    ".xlsx": (":material/table_chart:", "green"),
    ".csv": (":material/table_chart:", "green"),
    ".md": (":material/description:", "violet"),
    ".txt": (":material/description:", "gray"),
}


def file_icon(name: str) -> str:
    """按扩展名返回带颜色的 Material 图标（Markdown 短代码）。"""
    suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    icon, color = _FILE_ICONS.get(suffix, (":material/draft:", "gray"))
    return f":{color}[{icon}]"


def format_bytes(size: int) -> str:
    """字节数转换为 B / KB / MB 的可读文本。"""
    if size < 1024:
        return f"{size}B"
    if size < 1024 * 1024:
        return f"{size / 1024:.0f}KB"
    return f"{size / (1024 * 1024):.1f}MB"


def relative_time(ts: float) -> str:
    """“2 分钟前 / 今天 10:20 / 昨天 16:30 / 3 天前”风格的时间描述。"""
    now = datetime.now()
    dt = datetime.fromtimestamp(ts)
    delta = now - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{int(seconds // 60)} 分钟前"
    if dt.date() == now.date():
        return f"今天 {dt:%H:%M}"
    if dt.date() == now.date() - timedelta(days=1):
        return f"昨天 {dt:%H:%M}"
    if delta.days < 7:
        return f"{delta.days} 天前"
    if dt.year == now.year:
        return f"{dt:%m-%d}"
    return f"{dt:%Y-%m-%d}"


def short_date(ts: float) -> str:
    """统计卡片用的短描述：今天 / 昨天 / 3 天前 / 日期。"""
    now = datetime.now()
    dt = datetime.fromtimestamp(ts)

    if dt.date() == now.date():
        return "今天"
    if dt.date() == now.date() - timedelta(days=1):
        return "昨天"
    days = (now.date() - dt.date()).days
    if days < 7:
        return f"{days} 天前"
    if dt.year == now.year:
        return f"{dt:%m-%d}"
    return f"{dt:%Y-%m-%d}"
