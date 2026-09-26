from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, get_response_synthesizer
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from settings import setup_llamaindex

setup_llamaindex()
DATA_DIR = Path(__file__).parent / "data" / "chunking"

documents = SimpleDirectoryReader(input_dir=str(DATA_DIR)).load_data()
splitter = SentenceSplitter(chunk_size=128, chunk_overlap=20)
nodes = splitter.get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes)
retriever = index.as_retriever(similarity_top_k=3)
response_synthesizer = get_response_synthesizer()
query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=response_synthesizer,
)

question = "如果我要连续休 7 天年假，需要做什么？"
response = query_engine.query(question)

print("\n===== Question =====")
print(question)
print("\n===== Answer =====")
print(response)
print("\n===== Sources =====")
for i, source in enumerate(response.source_nodes, start=1):
    print(f"\n--- Source {i} ---")
    print("Score:", source.score)
    print(source.text)
