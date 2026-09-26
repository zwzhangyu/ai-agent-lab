"""索引服务：配置 DashScope 模型，管理 Chroma 向量库索引的加载与重建。"""
from __future__ import annotations

import os

import chromadb
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.llms.dashscope import DashScope
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.config import CHROMA_DIR, EMBED_BATCH_SIZE, LLM_MODEL, EMBED_MODEL
from app.models import AppSettings
from app.services.document_service import load_documents


COLLECTION_NAME = "rag_knowledge_chat"


def _require_api_key() -> str:
    # DashScope LLM 类不会自动读取 DASHSCOPE_API_KEY 环境变量，
    # 必须显式传入 api_key，否则抛 pydantic ValidationError。
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("未找到 DASHSCOPE_API_KEY，请在本目录 .env 中配置。")
    return api_key


def build_llm(model_name: str) -> DashScope:
    """按模型名创建 DashScope LLM 实例。"""
    return DashScope(model_name=model_name, api_key=_require_api_key())


def configure_models(llm_model: str | None = None) -> None:
    """把 LLM 与嵌入模型写入 LlamaIndex 全局 Settings。"""
    api_key = _require_api_key()

    Settings.llm = DashScope(model_name=llm_model or LLM_MODEL, api_key=api_key)
    # 必须显式指定批大小，默认值 25 会被 text-embedding-v4 拒绝。
    Settings.embed_model = DashScopeEmbedding(
        model_name=EMBED_MODEL,
        api_key=api_key,
        embed_batch_size=EMBED_BATCH_SIZE,
    )


def get_client():
    """创建指向本地持久化目录的 Chroma 客户端。"""
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection():
    """获取（不存在则创建）索引使用的向量集合。"""
    return get_client().get_or_create_collection(COLLECTION_NAME)


def load_index(llm_model: str | None = None) -> VectorStoreIndex:
    """从已有向量库加载索引，不触发重新解析与嵌入。"""
    configure_models(llm_model)

    vector_store = ChromaVectorStore(
        chroma_collection=get_collection()
    )

    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
    )


def rebuild_index(settings: AppSettings) -> dict:
    """清空集合后重新解析全部文件、切块并生成向量，返回文档与片段数。"""
    configure_models()

    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)

    documents = load_documents()
    if not documents:
        return {"documents": 0, "nodes": 0}

    splitter = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    nodes = splitter.get_nodes_from_documents(documents)

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
    )

    return {
        "documents": len(documents),
        "nodes": len(nodes),
    }


def collection_stats() -> dict:
    """返回向量库中的 chunk 数量，用于界面上的索引概览。"""
    try:
        count = get_collection().count()
    except Exception:
        count = 0

    return {"chunks": count}
