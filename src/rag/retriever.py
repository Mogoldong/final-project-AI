from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "data/chromaDB/" 
embeddings = OpenAIEmbeddings()

print("[RAG Retriever] 기존 ChromaDB 로드 중")
try:
    vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    print(f"ChromaDB 로드 완료. 총 {vector_db._collection.count()}개 문서 색인")

except Exception as e:
    print(f"오류: ChromaDB 로드 실패. '{CHROMA_PATH}' 경로를 확인")
    print(e)
    retriever = None

class RecipeSearchInput(BaseModel):
    query: str = Field(description="사용자가 레시피를 찾기 위해 입력한 자연어 질문 (예: '오늘 비오는데 얼큰한 국물 요리')")


def search_recipe(input: RecipeSearchInput) -> List[Dict[str, Any]]:
    """
    (툴 1: search_recipe)
    사용자의 자연어 질문을 받아 ChromaDB(벡터 DB)에서 
    가장 유사한 레시피 텍스트 조각(chunk) 3개를 검색하여 반환합니다.
    """
    if retriever is None:
        return [{"error": "RAG Retriever가 로드되지 않았습니다."}]
        
    print(f"[Tool Call] search_recipe 호출됨. 쿼리: {input.query}")
    
    # LangChain Retriever 실행 (Document 객체 리스트 반환)
    results_docs = retriever.invoke(input.query)
    
    # AI가 쉽게 이해하도록 Document 객체를 dict로 변환
    results_list = []
    for doc in results_docs:
        results_list.append({
            "content": doc.page_content, # RAG가 찾은 텍스트
            "metadata": doc.metadata   # 'recipe_id' 등이 포함된 메타데이터
        })
        
    return results_list

# --- 5. 독립 실행 테스트 ---
if __name__ == "__main__":
    if retriever:
        print("\n--- 'search_recipe' 툴 독립 테스트 ---")
        
        # '소고기떡국' (명절, 국/탕)과 유사한 쿼리로 테스트
        test_input = RecipeSearchInput(query="명절에 끓여먹는 소고기 국물 요리")
        search_results = search_recipe(test_input)
        
        print(f"\n[검색 결과 (총 {len(search_results)}개)]")
        for i, result in enumerate(search_results):
            print(f"\n--- 결과 {i+1} (ID: {result['metadata'].get('recipe_id')}) ---")
            # 내용이 너무 기니 150자만 출력
            print(result['content'][:150] + "...")
            
    else:
        print("Retriever 로드 실패로 테스트를 실행할 수 없습니다.")