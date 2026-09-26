"""左侧导航：品牌区、上传入口、视图切换与最近对话。"""
from __future__ import annotations

import streamlit as st

from app.config import APP_SUBTITLE, APP_TITLE, UPLOAD_FILE_TYPES
from app.services.document_service import save_uploaded_files
from app.services.index_service import rebuild_index
from app.state import (
    NAV_CHAT,
    NAV_FILES,
    NAV_KB,
    NAV_MODELS,
    conversation_list,
    new_conversation,
)
from app.utils.formatting import relative_time

NAV_ITEMS = [
    (NAV_CHAT, ":material/forum:"),
    (NAV_KB, ":material/menu_book:"),
    (NAV_FILES, ":material/folder_open:"),
    (NAV_MODELS, ":material/tune:"),
]


@st.dialog("上传文件")
def _upload_dialog() -> None:
    """上传弹窗：选择文件保存到知识库，可选立即重建索引。"""
    st.caption("支持 PDF / DOCX / PPTX / XLSX / CSV / TXT / MD")
    uploaded = st.file_uploader(
        "选择文件",
        type=UPLOAD_FILE_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    auto_rebuild = st.toggle("上传后立即重建索引", value=True)

    if st.button(
        "保存到知识库",
        type="primary",
        icon=":material/upload:",
        width="stretch",
        disabled=not uploaded,
    ):
        saved = save_uploaded_files(uploaded)
        if auto_rebuild and saved:
            with st.spinner("正在重建索引…"):
                rebuild_index(st.session_state.rag_settings)
            st.toast(
                f"已保存 {len(saved)} 个文件并重建索引",
                icon=":material/check_circle:",
            )
        else:
            st.toast(f"已保存 {len(saved)} 个文件", icon=":material/check_circle:")
            if saved:
                st.toast(
                    "文件尚未加入索引，可在“知识库”中重建",
                    icon=":material/info:",
                )
        st.rerun()


def render_sidebar() -> None:
    """渲染左侧导航栏：品牌区、上传入口、视图切换与最近对话。"""
    with st.sidebar:
        st.markdown(f"#### :blue[:material/auto_awesome:] {APP_TITLE}")
        st.caption(APP_SUBTITLE)

        if st.button(
            "上传文件",
            icon=":material/upload:",
            type="primary",
            width="stretch",
            key="sidebar-upload",
        ):
            _upload_dialog()

        st.space("small")

        for label, icon in NAV_ITEMS:
            active = st.session_state.nav == label
            if st.button(
                label,
                icon=icon,
                key=f"nav-{label}",
                type="primary" if active else "tertiary",
                width="stretch",
            ):
                st.session_state.nav = label
                st.rerun()

        st.space("small")

        header = st.columns([3, 1], vertical_alignment="center")
        with header[0]:
            st.markdown("**最近对话**")
        with header[1]:
            if st.button(
                "",
                icon=":material/add:",
                help="新建对话",
                key="new-conversation",
                width="stretch",
            ):
                new_conversation()
                st.session_state.nav = NAV_CHAT
                st.rerun()

        for cid, conv in conversation_list():
            active = cid == st.session_state.active_conversation_id
            if st.button(
                conv["title"],
                key=f"conversation-{cid}",
                type="primary" if active else "tertiary",
                width="stretch",
            ):
                st.session_state.active_conversation_id = cid
                st.session_state.nav = NAV_CHAT
                st.rerun()
            st.caption(relative_time(conv["updated_at"]))
