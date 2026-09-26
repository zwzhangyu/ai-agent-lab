from pathlib import Path
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

DATA_DIR = Path(__file__).parent / "data" / "chunking"
documents = SimpleDirectoryReader(input_dir=str(DATA_DIR)).load_data()

splitter = SentenceSplitter(chunk_size=128, chunk_overlap=20)
nodes = splitter.get_nodes_from_documents(documents)

print("Document 数量:", len(documents))
print("Node 数量:", len(nodes))

for index, node in enumerate(nodes, start=1):
    print(f"\n===== Node {index} =====")
    print(node.text)
    print("\nmetadata:")
    print(node.metadata)
    print("\nrelationships:")
    print(node.relationships)
