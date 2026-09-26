from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from settings import setup_llamaindex

setup_llamaindex()
DATA_DIR = Path(__file__).parent / "data" / "quickstart"

documents = SimpleDirectoryReader(input_dir=str(DATA_DIR)).load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=3)

question = "AuroraDesk 的退款期限是多少天？"
response = query_engine.query(question)

print("\n=== Question ===")
print(question)
print("\n=== Answer ===")
print(response)
print("\n=== Sources ===")
for source in response.source_nodes:
    print("score:", source.score)
    print("file:", source.metadata.get("file_name"))
    print("text:", source.text)
    print("-" * 50)
