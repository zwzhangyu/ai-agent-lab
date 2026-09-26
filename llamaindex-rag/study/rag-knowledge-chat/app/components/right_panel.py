"""对话视图右侧：知识库概览 + 最近上传 + 模型与配置。"""
from __future__ import annotations

import streamlit as st

from app.components.common import (
    render_chunk_controls,
    render_embed_display,
    render_file_row,
    render_llm_display,
    render_rebuild_button,
    render_retrieval_controls,
    render_stat_cards,
)
from app.models import AppSettings
from app.services.document_service import list_files
from app.state import NAV_KB, NAV_MODELS


def _switch_to(nav_label: str) -> None:
    """切换左侧导航并重跑页面。"""
    st.session_state.nav = nav_label
    st.rerun()


def _section_header(title: str, action_label: str, action_key: str, target_nav: str) -> None:
    """区块标题 + 右侧跳转按钮（如“查看全部 / 编辑”）。"""
    header = st.columns([2, 1.4], vertical_alignment="center")
    with header[0]:
        st.markdown(f"##### {title}")
    with header[1]:
        if st.button(
            action_label,
            icon=":material/arrow_forward:",
            icon_position="right",
            type="tertiary",
            key=action_key,
        ):
            _switch_to(target_nav)


def render_right_panel(settings: AppSettings) -> None:
    """渲染对话页右侧栏：知识库概览、最近上传与模型配置。"""
    files = list_files()

    _section_header("知识库", "查看全部", "kb-view-all", NAV_KB)
    render_stat_cards(files)

    st.markdown("**最近上传的文件**")
    recent = sorted(files, key=lambda item: item["mtime"], reverse=True)[:5]
    if recent:
        for item in recent:
            render_file_row(item, key_prefix="recent")
    else:
        st.caption("还没有文件，点左侧“上传文件”开始。")

    st.space("small")

    _section_header("模型与配置", "编辑", "model-edit", NAV_MODELS)
    render_llm_display(settings)
    render_embed_display()
    render_retrieval_controls(settings)

    with st.expander("更多高级设置", icon=":material/tune:"):
        render_chunk_controls(settings)
        render_rebuild_button(settings)
