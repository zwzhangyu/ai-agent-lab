from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from settings import setup_llamaindex

setup_llamaindex()
DATA_DIR = Path(__file__).parent / "data" / "chunking"

documents = SimpleDirectoryReader(input_dir=str(DATA_DIR)).load_data()
splitter = SentenceSplitter(chunk_size=128, chunk_overlap=20)
nodes = splitter.get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes)
retriever = index.as_retriever(similarity_top_k=3)

question = "我一年可以休多少天带薪年假？"
results = retriever.retrieve(question)

print("\n=== Question ===")
print(question)
for i, result in enumerate(results, start=1):
    print(f"\n===== Top {i} =====")
    print("Score:", result.score)
    print("Text:")
    print(result.text)
    print("Metadata:")
    print(result.metadata)
