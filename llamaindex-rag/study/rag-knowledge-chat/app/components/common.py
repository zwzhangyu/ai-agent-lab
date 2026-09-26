"""跨视图复用的 UI 组件。"""
from __future__ import annotations

import streamlit as st

from app.config import EMBED_MODEL, LLM_OPTIONS
from app.models import AppSettings
from app.services.document_service import delete_file
from app.services.index_service import rebuild_index
from app.utils.formatting import file_icon, format_bytes, relative_time, short_date


def rebuild_current_index(settings: AppSettings) -> None:
    """重建索引并提示结果（toast 可跨 rerun 显示）。"""
    with st.spinner("解析文件、切块并生成向量…"):
        result = rebuild_index(settings)

    if result["documents"] == 0:
        st.toast("当前没有文件可索引", icon=":material/info:")
    else:
        st.toast(
            f"索引重建完成：{result['documents']} 份文档 / {result['nodes']} 个片段",
            icon=":material/check_circle:",
        )
    st.rerun()


def render_stat_cards(
    files: list[dict],
    *,
    extra: list[tuple[str, str, str]] | None = None,
) -> None:
    """文件数量 / 总大小 / 最近更新，可追加自定义指标卡片。"""
    total_size = sum(item["size"] for item in files)
    latest = max((item["mtime"] for item in files), default=None)

    cards: list[tuple[str, str, str]] = [
        ("文件数量", str(len(files)), "知识库中的文件总数"),
        ("总大小", format_bytes(total_size) if files else "0B", f"共 {total_size} 字节"),
        (
            "最近更新",
            short_date(latest) if latest else "—",
            relative_time(latest) if latest else "暂无文件",
        ),
    ]
    if extra:
        cards.extend(extra)

    for column, (label, value, help_text) in zip(
        st.columns(len(cards), gap="small"), cards
    ):
        column.metric(label, value, border=True, help=help_text)


def render_file_row(
    item: dict,
    *,
    key_prefix: str,
    allow_download: bool = False,
) -> None:
    """文件行：图标 + 名称 + 大小时间 + （可选）下载 + 删除菜单。"""
    name = item["name"]
    widths = [10, 1, 1] if allow_download else [10, 1]
    columns = st.columns(widths, vertical_alignment="center")

    with columns[0]:
        st.markdown(f"{file_icon(name)} **{name}**")
        st.caption(f"{format_bytes(item['size'])} · {relative_time(item['mtime'])}")

    if allow_download:
        with columns[1]:
            with open(item["path"], "rb") as file:
                st.download_button(
                    "",
                    data=file.read(),
                    file_name=name,
                    icon=":material/download:",
                    help="下载原文件",
                    key=f"{key_prefix}-download-{name}",
                )

    with columns[-1]:
        action = st.menu_button(
            "",
            ["删除"],
            icon=":material/more_vert:",
            help="更多操作",
            key=f"{key_prefix}-menu-{name}",
        )
        if action == "删除":
            delete_file(name)
            st.toast(f"已删除 {name}，如需生效请重建索引", icon=":material/delete:")
            st.rerun()


def render_llm_select(
    settings: AppSettings,
    *,
    key: str = "cfg-llm",
    show_label: bool = True,
) -> None:
    """可编辑的大语言模型选择框。"""
    index = (
        LLM_OPTIONS.index(settings.llm_model)
        if settings.llm_model in LLM_OPTIONS
        else 0
    )
    settings.llm_model = st.selectbox(
        "大语言模型",
        LLM_OPTIONS,
        index=index,
        key=key,
        label_visibility="visible" if show_label else "collapsed",
        help="回答问题时使用的通义千问模型",
    )


def render_llm_display(settings: AppSettings) -> None:
    """只读的大语言模型展示。"""
    index = (
        LLM_OPTIONS.index(settings.llm_model)
        if settings.llm_model in LLM_OPTIONS
        else 0
    )
    st.selectbox("大语言模型", LLM_OPTIONS, index=index, disabled=True)


def render_embed_display() -> None:
    """只读的嵌入模型展示。"""
    st.selectbox(
        "嵌入模型",
        [EMBED_MODEL],
        disabled=True,
        help="切换嵌入模型需要重建全部索引，当前版本保持固定",
    )


def render_retrieval_controls(settings: AppSettings) -> None:
    """Top-K 与相似度阈值。"""
    settings.top_k = st.slider(
        "检索数量 Top-K",
        1,
        10,
        settings.top_k,
        key="cfg-top-k",
        help="每次提问从知识库取回的相关片段数量",
    )
    settings.similarity_cutoff = st.slider(
        "相似度阈值（可选）",
        0.0,
        1.0,
        settings.similarity_cutoff,
        step=0.05,
        key="cfg-cutoff",
        help="低于该阈值的片段不参与回答；0 表示不过滤",
    )


def render_chunk_controls(settings: AppSettings) -> None:
    """切块参数（重建索引后生效）。"""
    settings.chunk_size = st.slider(
        "chunk_size",
        128,
        2048,
        settings.chunk_size,
        step=128,
        key="cfg-chunk-size",
    )
    settings.chunk_overlap = st.slider(
        "chunk_overlap",
        0,
        300,
        settings.chunk_overlap,
        step=10,
        key="cfg-chunk-overlap",
    )


def render_rebuild_button(settings: AppSettings) -> None:
    """重建索引按钮，点击后走统一的 rebuild_current_index 流程。"""
    if st.button(
        "重建索引",
        type="primary",
        icon=":material/refresh:",
        width="stretch",
        key="rebuild-index",
    ):
        rebuild_current_index(settings)
