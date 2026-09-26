"""HomeRag 应用入口：页面配置、全局样式与视图分发。"""
import os

import streamlit as st

from app.components.chat_view import render_chat_view, render_composer
from app.components.manage_views import (
    render_files_view,
    render_kb_view,
    render_models_view,
)
from app.components.right_panel import render_right_panel
from app.components.sidebar import render_sidebar
from app.config import APP_TITLE
from app.state import (
    NAV_CHAT,
    NAV_FILES,
    NAV_KB,
    NAV_MODELS,
    init_state,
)


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=":material/auto_awesome:",
    layout="wide",
)

# 全局样式：收紧顶部留白，并将用户消息改为靠右显示
st.markdown(
    """
<style>
.block-container { padding-top: 1.8rem; }

/* 原型图风格：用户消息靠右显示 */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    width: fit-content;
    margin-left: auto;
}
</style>
    """,
    unsafe_allow_html=True,
)


# 初始化会话状态并渲染侧边栏（须在任何视图渲染之前执行）
init_state()
render_sidebar()

if not os.getenv("DASHSCOPE_API_KEY"):
    st.error("请先在 .env 配置 DASHSCOPE_API_KEY", icon=":material/key:")

settings = st.session_state.rag_settings
nav = st.session_state.nav

# 按当前导航渲染对应视图；对话视图为左右两栏 + 底部固定输入区
if nav == NAV_CHAT:
    chat_col, right_col = st.columns([2.6, 1], gap="medium")
    with chat_col:
        render_chat_view()
    with right_col:
        render_right_panel(settings)
    # 固定在主区域底部的输入区，跨重跑始终可见
    render_composer()
elif nav == NAV_KB:
    render_kb_view(settings)
elif nav == NAV_FILES:
    render_files_view()
elif nav == NAV_MODELS:
    render_models_view(settings)
