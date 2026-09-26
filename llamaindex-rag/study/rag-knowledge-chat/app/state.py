"""基于 st.session_state 的多会话状态管理。"""
from __future__ import annotations

import time
import uuid

import streamlit as st

from app.models import AppSettings

NAV_CHAT = "对话"
NAV_KB = "知识库"
NAV_FILES = "文件管理"
NAV_MODELS = "模型设置"

DEFAULT_TITLE = "新对话"


def init_state() -> None:
    """初始化会话级状态；活跃会话失效时自动新建一个。"""
    ss = st.session_state
    ss.setdefault("conversations", {})
    ss.setdefault("rag_settings", AppSettings())
    ss.setdefault("nav", NAV_CHAT)
    # pending_*：跨 rerun 传递的待处理任务（提问 / 附件入库 / 入库通知）
    ss.setdefault("pending_question", None)
    ss.setdefault("pending_ingest", None)
    ss.setdefault("pending_ingest_notice", False)

    if (
        not ss.get("active_conversation_id")
        or ss.active_conversation_id not in ss.conversations
    ):
        new_conversation()


def new_conversation() -> str:
    """新建一个空会话并设为活跃，返回会话 id。"""
    cid = uuid.uuid4().hex[:10]
    st.session_state.conversations[cid] = {
        "title": DEFAULT_TITLE,
        "messages": [],
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    st.session_state.active_conversation_id = cid
    return cid


def get_active_conversation() -> dict:
    """返回当前活跃会话的完整数据字典。"""
    return st.session_state.conversations[st.session_state.active_conversation_id]


def conversation_list() -> list[tuple[str, dict]]:
    """按最近活跃排序的 (conversation_id, conversation) 列表。"""
    items = st.session_state.conversations.items()
    return sorted(items, key=lambda kv: kv[1]["updated_at"], reverse=True)


def add_message(conv: dict, role: str, content: str, **extra) -> dict:
    """追加一条消息；首条用户消息会自动成为会话标题。"""
    if role == "user" and conv["title"] == DEFAULT_TITLE:
        first_line = content.strip().splitlines()[0] if content.strip() else ""
        if first_line:
            conv["title"] = first_line[:18] + ("…" if len(first_line) > 18 else "")

    message = {"role": role, "content": content, "ts": time.time(), **extra}
    conv["messages"].append(message)
    conv["updated_at"] = time.time()
    return message
