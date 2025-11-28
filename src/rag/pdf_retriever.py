from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "data/chroma_db/"
COLLECTION_NAME = "food_knowledge"
embeddings = OpenAIEmbeddings()

try:
    vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
except Exception as e:
    print(f"DB 로드 실패: {e}")
    retriever = None

class KnowledgeSearchInput(BaseModel):
    query: str = Field(description="요리 상식, 영양 정보, 식재료 효능 등에 대한 질문")

def search_food_knowledge(input: KnowledgeSearchInput) -> List[Dict[str, Any]]:
    """
    (Tool) 요리 백과사전(PDF)에서 영양 정보나 식재료 상식을 검색합니다.
    레시피(만드는 법)가 아니라 '지식(What/Why)'을 물어볼 때 사용하세요.
    """
    if not retriever:
        return [{"error": "지식 DB가 없습니다."}]

    print(f"[Tool Call] 지식 검색: {input.query}")
    
    docs = retriever.invoke(input.query)
    
    return [{"content": doc.page_content, "source": doc.metadata.get("source")} for doc in docs]

if __name__ == "__main__":
    print(search_food_knowledge(KnowledgeSearchInput(query="다이어트에 좋은 음식")))