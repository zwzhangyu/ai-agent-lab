"""知识库 / 文件管理 / 模型设置 三个管理视图。"""
from __future__ import annotations

import streamlit as st

from app.components.common import (
    render_chunk_controls,
    render_embed_display,
    render_file_row,
    render_llm_select,
    render_rebuild_button,
    render_retrieval_controls,
    render_stat_cards,
)
from app.config import UPLOAD_FILE_TYPES
from app.models import AppSettings
from app.services.document_service import list_files, save_uploaded_files
from app.services.index_service import collection_stats, rebuild_index


def render_kb_view(settings: AppSettings) -> None:
    """知识库视图：统计卡片、重建索引入口与文件列表。"""
    st.subheader("知识库", icon=":material/menu_book:")

    files = list_files()
    stats = collection_stats()

    render_stat_cards(
        files,
        extra=[("索引片段", str(stats["chunks"]), "向量库中的 chunk 数量")],
    )

    st.space("small")

    button_col, settings_col = st.columns([1, 3], vertical_alignment="top")
    with button_col:
        render_rebuild_button(settings)
    with settings_col:
        with st.expander("高级切块参数", icon=":material/tune:"):
            render_chunk_controls(settings)

    st.markdown("**全部文件**")
    if files:
        for item in files:
            render_file_row(item, key_prefix="kb")
    else:
        st.caption("暂无文件，去“文件管理”上传资料吧。")


def render_files_view() -> None:
    """文件管理视图：搜索、上传与文件下载/删除。"""
    st.subheader("文件管理", icon=":material/folder_open:")

    query = st.text_input(
        "搜索文件",
        placeholder="搜索知识库中的文件…",
        label_visibility="collapsed",
    )

    uploaded = st.file_uploader(
        "上传文件",
        type=UPLOAD_FILE_TYPES,
        accept_multiple_files=True,
        help="支持 PDF / DOCX / PPTX / XLSX / CSV / TXT / MD",
    )
    rebuild_now = st.toggle("保存后立即重建索引", value=True)

    if uploaded and st.button(
        "保存上传文件",
        type="primary",
        icon=":material/upload:",
        key="files-save",
    ):
        saved = save_uploaded_files(uploaded)
        if rebuild_now and saved:
            with st.spinner("正在重建索引…"):
                rebuild_index(st.session_state.rag_settings)
            st.toast(
                f"已保存 {len(saved)} 个文件并重建索引",
                icon=":material/check_circle:",
            )
        else:
            st.toast(
                f"已保存 {len(saved)} 个文件，记得重建索引",
                icon=":material/check_circle:",
            )
        st.rerun()

    files = list_files()
    if query:
        files = [item for item in files if query.lower() in item["name"].lower()]

    st.markdown(f"**共 {len(files)} 个文件**")
    if files:
        for item in files:
            render_file_row(item, key_prefix="files", allow_download=True)
    else:
        st.caption("没有匹配的文件。")


def render_models_view(settings: AppSettings) -> None:
    """模型设置视图：模型选择、检索参数与切块参数。"""
    st.subheader("模型设置", icon=":material/tune:")
    st.caption("修改后对之后的提问生效；切块参数在重建索引后生效。")

    render_llm_select(settings)
    render_embed_display()
    render_retrieval_controls(settings)

    st.markdown("**切块参数**")
    render_chunk_controls(settings)

    st.space("small")
    render_rebuild_button(settings)
