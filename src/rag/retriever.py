from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

CHROMA_PATH = "data/chromaDB/" 
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

try:
    vector_db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    print(f"Total {vector_db._collection.count()} documents indexed")

except Exception as e:
    print(e)
    retriever = None

class RecipeSearchInput(BaseModel):
    query: str = Field(description="사용자가 레시피를 찾기 위해 입력한 자연어 질문 (예: '오늘 비오는데 얼큰한 국물 요리')")


def search_recipe(input: RecipeSearchInput) -> List[Dict[str, Any]]:
    if retriever is None:
        return [{"error": "RAG Retriever not loaded"}]
        
    print(f"[Tool] search_recipe: {input.query}")
    
    results_docs = retriever.invoke(input.query)
    
    results_list = []
    for doc in results_docs:
        results_list.append({
            "content": doc.page_content,
            "metadata": doc.metadata 
        })
        
    return results_list