"""问答编排：检索知识库 → 可选联网搜索 → 生成带引用的回答。"""
from __future__ import annotations

from typing import Any

from llama_index.core import PromptTemplate
from llama_index.core.schema import NodeWithScore, TextNode

from app.models import AppSettings
from app.services import web_search
from app.services.index_service import build_llm, load_index

QA_TEMPLATE = PromptTemplate(
    """
你是一个严谨的知识库问答助手。

请只依据下面提供的【参考资料】回答问题，资料可能来自本地知识库或联网搜索。

规则：
1. 不要把模型自身记忆当成知识库事实，不要虚构来源。
2. 如果资料不足以支持答案，请明确回答：
   “当前知识库中没有足够信息回答这个问题。”
3. 如果可以回答，先给出直接结论，再分点补充关键细节，保持清晰、简洁。
4. 回答中的关键信息都应能在参考资料中找到依据。

---------------------
参考资料：
{context_str}
---------------------

用户问题：
{query_str}

回答：
"""
)

WEB_TEXT_PREFIX = "[联网搜索结果] "


def retrieve(question: str, settings: AppSettings) -> list[NodeWithScore]:
    """按当前设置检索知识库，并过滤低于相似度阈值的片段。"""
    index = load_index(settings.llm_model)
    retriever = index.as_retriever(similarity_top_k=settings.top_k)
    nodes = retriever.retrieve(question)

    # 该版本的 VectorIndexRetriever 不识别 similarity_cutoff，手动过滤。
    cutoff = settings.similarity_cutoff
    if cutoff and cutoff > 0:
        nodes = [node for node in nodes if node.score is None or node.score >= cutoff]
    return nodes


def search_web(question: str, settings: AppSettings) -> list[dict]:
    """联网搜索（受设置开关控制）。"""
    if not settings.web_search:
        return []
    return web_search.search(question)


def _web_nodes(results: list[dict]) -> list[NodeWithScore]:
    """把联网结果包装成带元数据的节点，与知识库片段共用引用与提示词流程。"""
    nodes = []
    for item in results:
        node = TextNode(
            text=WEB_TEXT_PREFIX + (item.get("content") or ""),
            metadata={
                "file_name": item.get("title") or "网页结果",
                "url": item.get("url"),
                "source_type": "web",
            },
        )
        nodes.append(NodeWithScore(node=node, score=None))
    return nodes


def _to_source(node_with_score: NodeWithScore) -> dict:
    """把检索节点转为界面引用来源所需的扁平字典。"""
    metadata = node_with_score.metadata or {}
    text = node_with_score.text or ""

    if metadata.get("source_type") == "web" and text.startswith(WEB_TEXT_PREFIX):
        text = text[len(WEB_TEXT_PREFIX):]

    return {
        "score": node_with_score.score,
        "file_name": metadata.get("file_name", "unknown"),
        "file_path": metadata.get("file_path", ""),
        "page_label": metadata.get("page_label"),
        "sheet_name": metadata.get("sheet_name"),
        "url": metadata.get("url"),
        "text": text,
    }


def _extract_thinking(response) -> str | None:
    """从 DashScope 原始响应中取出模型思考过程（reasoning_content）。"""
    try:
        message = response.raw["output"]["choices"][0]["message"]
        return message.get("reasoning_content") or None
    except Exception:
        return None


def synthesize(
    question: str,
    settings: AppSettings,
    kb_nodes: list[NodeWithScore],
    web_results: list[dict],
) -> dict[str, Any]:
    """把知识库片段与网页结果一起交给 LLM 生成带引用的回答。"""
    nodes = list(kb_nodes) + _web_nodes(web_results)
    if not nodes:
        return {
            "answer": "当前知识库中没有足够信息回答这个问题。",
            "sources": [],
            "thinking": None,
        }

    context_str = "\n\n".join(node.text or "" for node in nodes)
    prompt = QA_TEMPLATE.format(context_str=context_str, query_str=question)

    llm = build_llm(settings.llm_model)
    try:
        # 深度思考 = 模型原生思考开关（DashScope enable_thinking）。
        # 关闭时必须显式传 False：qwen3.7-max 等模型默认开启思考。
        response = llm.complete(
            prompt, enable_thinking=settings.deep_thinking
        )
    except Exception as exc:
        # 当前模型不支持该参数时自动降级为默认调用。
        if "enable_thinking" not in str(exc):
            raise
        response = llm.complete(prompt)

    answer = response.text or ""
    if not answer:
        raise RuntimeError("模型返回了空回答，请重试或检查模型配置。")

    return {
        "answer": answer,
        "thinking": _extract_thinking(response),
        "sources": [_to_source(item) for item in nodes],
    }
