from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# 임베딩 모델 및 경로 설정
CHROMA_PATH = "data/chromaDB/" 
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'}, # mps, cuda, cpu
    encode_kwargs={'normalize_embeddings': True}
)

# ChromaDB 인스턴스 로드
try:
    vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    # 유사한 문서 3개만 검색하도록 설정
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    print(f"Total {vector_db._collection.count()} documents indexed")

except Exception as e:
    print(e)
    retriever = None

# LLM이 Tool을 호출할 때 (query) 항상 문자열로 받도록 정의
class RecipeSearchInput(BaseModel):
    query: str = Field(description="사용자가 레시피를 찾기 위해 입력한 자연어 질문 (예: '오늘 비오는데 얼큰한 국물 요리')")

# 실제 검색 함수 구현
def search_recipe(input: RecipeSearchInput) -> List[Dict[str, Any]]:
    if retriever is None:
        return [{"error": "RAG Retriever not loaded"}]
    
    results_docs = retriever.invoke(input.query) # invoke가 실행되면 사용자 질의는 벡터화되어 ChromaDB에서 유사한 문서 3개를 검색
    
    results_list = []
    for doc in results_docs:
        results_list.append({
            "content": doc.page_content, # e.g., recipe text
            "metadata": doc.metadata # e.g., source, recipe_id
        }) # 문서의 내용과 메타데이터가 포함된 딕셔너리 생성
        
    return results_list