from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "data/chroma_db/"
COLLECTION_NAME = "food_knowledge"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

try:
    print(f"[Knowledge Retriever] '{COLLECTION_NAME}' 컬렉션 로드 중...")
    vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
except Exception as e:
    print(f"DB load failed: {e}")
    retriever = None

class KnowledgeSearchInput(BaseModel):
    query: str = Field(description="요리 상식, 영양 정보, 식재료 효능 등에 대한 질문")

def search_food_knowledge(input: KnowledgeSearchInput) -> List[Dict[str, Any]]:
    if not retriever:
        return [{"error": "Knowledge DB not available"}]

    print(f"[Tool] search_food_knowledge: {input.query}")
    
    docs = retriever.invoke(input.query)
    
    return [{"content": doc.page_content, "source": doc.metadata.get("source")} for doc in docs]
