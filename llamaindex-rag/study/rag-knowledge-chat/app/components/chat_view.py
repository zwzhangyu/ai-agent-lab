"""对话视图：消息流、引用来源、消息操作与底部输入区。"""
from __future__ import annotations

import re
import time

import streamlit as st

from app.components.common import render_llm_select
from app.config import UPLOAD_FILE_TYPES
from app.models import AppSettings
from app.services import chat_service, web_search
from app.services.document_service import list_files, save_uploaded_files
from app.services.index_service import rebuild_index
from app.state import add_message, get_active_conversation
from app.utils.formatting import file_icon

ASSISTANT_AVATAR = ":material/auto_awesome:"

# 空会话时展示的推荐问题
SUGGESTIONS = [
    "总结一下知识库的核心内容",
    "这个知识库里有哪些关键概念？",
    "有哪些值得关注的要点？",
]


_MARKDOWN_SPECIALS = re.compile(r"([\\`*_{}\[\]<>#+\-.!|~$])")


def _plain_text(text: str) -> str:
    """转义 Markdown 特殊字符，避免片段被当作标题、列表等渲染。"""
    return _MARKDOWN_SPECIALS.sub(r"\\\1", text)


def _clean_snippet(text: str) -> str:
    """去掉行首的 Markdown 标题记号（如 ###）并压平空白，便于单行展示。"""
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    return " ".join(text.split())


def _source_location(source: dict) -> str:
    """拼出引用来源的位置描述（页码 / 工作表名）。"""
    parts = []
    if source.get("page_label"):
        parts.append(f"第 {source['page_label']} 页")
    if source.get("sheet_name"):
        parts.append(f"工作表 {source['sheet_name']}")
    return " · ".join(parts)


def _render_sources(sources: list[dict], *, expanded: bool) -> None:
    """渲染引用来源折叠区：文件名、匹配度/联网徽标与片段预览。"""
    with st.expander(
        f"引用来源 · {len(sources)}",
        icon=":material/format_quote:",
        expanded=expanded,
    ):
        for source in sources:
            with st.container(border=True):
                file_name = source.get("file_name", "unknown")

                if source.get("url"):
                    header = (
                        f"**[{_plain_text(file_name)}]({source['url']})**"
                        " :blue-badge[联网]"
                    )
                else:
                    score = source.get("score")
                    badge = (
                        f" :blue-badge[匹配度 {score:.2f}]"
                        if isinstance(score, (int, float))
                        else ""
                    )
                    header = f"**{_plain_text(file_name)}**{badge}"

                location = _source_location(source)
                if location:
                    header += f" · {location}"

                st.caption(f"{file_icon(file_name)} {header}", wrap=False)

                snippet = _clean_snippet(source.get("text") or "")
                if snippet:
                    st.caption(_plain_text(snippet), wrap=False)


def _regenerate(conv: dict, message_index: int) -> None:
    """重新生成回答：截断该回答及后续消息，并重新提交前面的问题。"""
    messages = conv["messages"]
    if message_index <= 0 or messages[message_index - 1]["role"] != "user":
        return

    question = messages[message_index - 1]["content"]
    del messages[message_index:]
    st.session_state.pending_question = question
    st.rerun()


def _render_actions(conv: dict, message_index: int, message: dict) -> None:
    """回答下方的操作栏：复制、反馈、重新生成与耗时/来源统计。"""
    left, right = st.columns([5, 4], vertical_alignment="center")

    with left:
        with st.container(horizontal=True, gap="small"):
            with st.popover("", icon=":material/content_copy:", help="复制回答"):
                st.code(message["content"], language=None, wrap_lines=True)

            if st.button(
                "",
                icon=":material/thumb_up:",
                help="有帮助",
                key=f"feedback-up-{message_index}",
            ):
                message["feedback"] = "up"
                st.toast("感谢反馈", icon=":material/favorite:")
                st.rerun()

            if st.button(
                "",
                icon=":material/thumb_down:",
                help="没帮助",
                key=f"feedback-down-{message_index}",
            ):
                message["feedback"] = "down"
                st.toast("收到，会继续改进", icon=":material/edit_note:")
                st.rerun()

            if st.button(
                "",
                icon=":material/refresh:",
                help="重新生成",
                key=f"regenerate-{message_index}",
            ):
                _regenerate(conv, message_index)

    with right:
        elapsed = message.get("elapsed")
        if elapsed is not None:
            sources_count = len(message.get("sources") or [])
            st.caption(
                f"{elapsed:.1f}s · 基于 {sources_count} 个来源",
                text_alignment="right",
            )


def _ingest_attachments(names: list[str]) -> str | None:
    """把附件加入知识库并重建索引；成功返回 None，失败返回错误信息。"""
    with st.status(
        f"正在把 {len(names)} 个附件加入知识库…",
        type="compact",
    ) as status:
        try:
            rebuild_index(st.session_state.rag_settings)
        except Exception as exc:
            status.update(label="附件入库失败", state="error")
            return f"{type(exc).__name__}: {exc}"
        status.update(
            label=f"已将 {len(names)} 个文件加入知识库并重建索引",
            state="complete",
        )
        return None


def _generate_answer(question: str, conv: dict) -> None:
    """执行一次完整问答（检索 → 可选联网 → 生成），逐步展示状态并写入会话。"""
    settings: AppSettings = st.session_state.rag_settings
    started = time.perf_counter()
    result: dict = {"answer": "", "sources": [], "thinking": None}

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.status(":shimmer[正在思考…]", type="compact") as status:
            try:
                with st.status("检索知识库", type="step") as kb_step:
                    try:
                        kb_nodes = chat_service.retrieve(question, settings)
                        st.write(
                            f"命中 {len(kb_nodes)} 个相关片段"
                            if kb_nodes
                            else "没有命中相关片段"
                        )
                    except Exception:
                        kb_step.update(state="error")
                        raise

                web_results: list[dict] = []
                if settings.web_search:
                    with st.status("联网搜索", type="step") as web_step:
                        try:
                            web_results = chat_service.search_web(question, settings)
                            st.write(
                                f"获得 {len(web_results)} 条网页结果"
                                if web_results
                                else "没有找到相关网页"
                            )
                        except Exception as exc:
                            st.write(f"搜索失败：{exc}")
                            web_step.update(state="error")

                step_label = (
                    "深度思考并生成回答" if settings.deep_thinking else "生成回答"
                )
                with st.status(step_label, type="step") as answer_step:
                    try:
                        result = chat_service.synthesize(
                            question, settings, kb_nodes, web_results
                        )
                    except Exception:
                        answer_step.update(state="error")
                        raise

                status.update(label="思考完成", state="complete")
            except Exception as exc:
                result = {
                    "answer": f"处理问题时发生错误：\n\n`{type(exc).__name__}: {exc}`",
                    "sources": [],
                    "thinking": None,
                }
                status.update(label="处理失败", state="error")

        elapsed = time.perf_counter() - started
        if result.get("thinking"):
            with st.expander("深度思考过程", icon=":material/psychology:"):
                st.markdown(result["thinking"])
        st.markdown(result["answer"])
        if result["sources"]:
            _render_sources(result["sources"], expanded=True)

        message = add_message(
            conv,
            "assistant",
            result["answer"],
            sources=result["sources"],
            elapsed=elapsed,
            thinking=result.get("thinking"),
        )
        _render_actions(conv, len(conv["messages"]) - 1, message)


def _handle_submission(submission, conv: dict) -> None:
    """处理提交：只更新状态并 rerun，渲染交给下一轮，保证消息顺序。"""
    text = (submission.text or "").strip()
    files = list(getattr(submission, "files", None) or [])

    attachment_names: list[str] = []
    if files:
        attachment_names = [path.name for path in save_uploaded_files(files)]

    if text:
        add_message(conv, "user", text, attachments=attachment_names)
        if attachment_names:
            st.session_state.pending_ingest = attachment_names
        st.session_state.pending_question = text
    elif attachment_names:
        st.session_state.pending_ingest = attachment_names
        st.session_state.pending_ingest_notice = True

    if text or attachment_names:
        st.rerun()


def _render_header(conv: dict) -> None:
    """渲染对话标题与重命名入口。"""
    title_col, edit_col = st.columns([10, 1], vertical_alignment="center")

    with title_col:
        st.markdown(f"##### {conv['title']}")

    with edit_col:
        with st.popover("", icon=":material/edit:", help="重命名对话"):
            new_title = st.text_input("会话名称", value=conv["title"])
            if st.button(
                "保存",
                type="primary",
                width="stretch",
                key="rename-save",
            ):
                if new_title.strip():
                    conv["title"] = new_title.strip()
                st.rerun()


def _render_empty_state(conv: dict) -> None:
    """空会话时的欢迎区：提示知识库状态并给出推荐问题。"""
    st.markdown("##### 向你的知识库提问")
    if list_files():
        st.caption("所有回答都基于你的知识库内容，并附带引用来源。")
    else:
        st.caption("知识库还是空的，先在左侧上传资料并重建索引。")

    selected = st.pills(
        "试试这些问题",
        SUGGESTIONS,
        label_visibility="collapsed",
    )
    if selected:
        add_message(conv, "user", selected)
        st.session_state.pending_question = selected
        st.rerun()


def _render_message(
    message: dict,
    message_index: int,
    conv: dict,
    *,
    expanded_sources: bool,
) -> None:
    """渲染单条消息：正文、思考过程、附件与引用来源。"""
    role = message["role"]
    avatar = ASSISTANT_AVATAR if role == "assistant" else None

    with st.chat_message(role, avatar=avatar):
        if role == "assistant" and message.get("thinking"):
            with st.expander("深度思考过程", icon=":material/psychology:"):
                st.markdown(message["thinking"])
        st.markdown(message["content"])

        attachments = message.get("attachments") or []
        if attachments:
            st.caption("📎 " + "、".join(attachments))

        if role == "assistant" and message.get("sources"):
            _render_sources(message["sources"], expanded=expanded_sources)

        if role == "assistant" and message.get("elapsed") is not None:
            _render_actions(conv, message_index, message)


def render_composer() -> None:
    """底部固定输入区：开关 + 模型选择 + 输入框，跨重跑始终可见。"""
    conv = get_active_conversation()
    settings: AppSettings = st.session_state.rag_settings

    with st.bottom:
        # 与主内容同比例分列，使输入区对齐中间对话列。
        composer_col, _ = st.columns([2.6, 1], gap="medium")

        with composer_col:
            deep_col, web_col, _, model_col = st.columns(
                [2.2, 2.2, 2.2, 3.4], vertical_alignment="center"
            )

            with deep_col:
                settings.deep_thinking = st.toggle(
                    "深度思考",
                    value=settings.deep_thinking,
                    key="cfg-deep",
                    help="开启模型原生深度思考（enable_thinking），先推理再回答，更慢但更深入",
                )

            with web_col:
                web_ready = web_search.is_configured()
                settings.web_search = st.toggle(
                    "联网搜索",
                    value=settings.web_search and web_ready,
                    key="cfg-web",
                    help=(
                        "用 Tavily 搜索网页，与知识库结果一起回答"
                        if web_ready
                        else "未配置 TAVILY_API_KEY，暂不可用"
                    ),
                    disabled=not web_ready,
                )

            with model_col:
                render_llm_select(settings, show_label=False)

            submission = st.chat_input(
                "输入你的问题，按 Enter 发送，Shift + Enter 换行",
                accept_file="multiple",
                file_type=UPLOAD_FILE_TYPES,
            )
            if submission:
                _handle_submission(submission, conv)


def render_chat_view() -> None:
    """渲染对话视图主体：消息流、附件入库与待答问题。"""
    conv = get_active_conversation()
    _render_header(conv)

    messages = conv["messages"]
    # 只有最新一条回答默认展开引用来源
    last_assistant_index = next(
        (
            i
            for i in range(len(messages) - 1, -1, -1)
            if messages[i]["role"] == "assistant"
        ),
        None,
    )

    for index, message in enumerate(messages):
        _render_message(
            message,
            index,
            conv,
            expanded_sources=index == last_assistant_index,
        )

    pending_names = st.session_state.get("pending_ingest")
    if pending_names:
        st.session_state.pending_ingest = None
        error = _ingest_attachments(pending_names)
        if st.session_state.get("pending_ingest_notice"):
            st.session_state.pending_ingest_notice = False
            add_message(
                conv,
                "assistant",
                (
                    f"已将 {len(pending_names)} 个文件加入知识库并重建索引，"
                    "现在可以直接提问了。"
                    if error is None
                    else f"附件入库失败：{error}"
                ),
                sources=[],
                elapsed=None,
            )
            st.rerun()

    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
        _generate_answer(question, conv)
    elif not messages:
        _render_empty_state(conv)
