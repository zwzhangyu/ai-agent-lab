"""最小但完整的个人知识库 RAG。"""

import sys
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

LAB_DIR = Path(__file__).resolve().parents[2]
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from settings import setup_llamaindex  # noqa: E402

DATA_DIR = LAB_DIR / "data" / "personal"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
SIMILARITY_TOP_K = 3


def build_query_engine():
    setup_llamaindex()
    documents = SimpleDirectoryReader(
        input_dir=str(DATA_DIR),
        recursive=True,
    ).load_data()

    if not documents:
        raise RuntimeError(f"知识库为空，请先把 TXT / MD / PDF 放入：{DATA_DIR}")

    splitter = SentenceSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    nodes = splitter.get_nodes_from_documents(documents)
    index = VectorStoreIndex(nodes)
    query_engine = index.as_query_engine(similarity_top_k=SIMILARITY_TOP_K)

    print(f"Loaded documents: {len(documents)}")
    print(f"Generated nodes: {len(nodes)}")
    return query_engine


def print_response(question, response):
    print("\n" + "=" * 70)
    print("Question:")
    print(question)
    print("\nAnswer:")
    print(response)
    print("\nSources:")

    for i, source in enumerate(response.source_nodes, start=1):
        file_name = source.metadata.get("file_name", "unknown")
        text = source.text.replace("\n", " ").strip()
        if len(text) > 240:
            text = text[:240] + "..."
        print(f"\n[{i}] {file_name}")
        print(f"score: {source.score}")
        print(text)


def main():
    query_engine = build_query_engine()
    print("\n个人知识库 RAG 已启动。")
    print("输入 exit / quit / q 退出。\n")

    while True:
        question = input("You> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("Bye.")
            break
        response = query_engine.query(question)
        print_response(question, response)


if __name__ == "__main__":
    main()
