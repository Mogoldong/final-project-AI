import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "data/chromaDB"
COLLECTION_NAME = "memory_store"

embeddings = OpenAIEmbeddings()

vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings
)

class WriteMemoryInput(BaseModel):
    content: str = Field(description="저장할 메모리의 내용")
    memory_type: Literal["profile", "episodic", "knowledge"] = Field(description="메모리 타입")
    importance: int = Field(description="중요도 (1~5)")
    tags: List[str] = Field(default=[], description="관련 태그")

class ReadMemoryInput(BaseModel):
    query: str = Field(description="기억에서 검색할 키워드나 질문")
    top_k: int = Field(default=3, description="반환할 기억 개수")

def write_memory(input: WriteMemoryInput) -> str:
    print(f"[Tool] write_memory: {input.content[:30]}...")
    memory_id = str(uuid.uuid4())
    
    metadata = {
        "type": input.memory_type,
        "importance": input.importance,
        "tags": ", ".join(input.tags)
    }
    
    vector_store.add_texts(
        texts=[input.content],
        metadatas=[metadata],
        ids=[memory_id]
    )
    
    return f"Memory saved. (ID: {memory_id})"

def read_memory(input: ReadMemoryInput) -> str:
    print(f"[Tool] read_memory: {input.query}")
    results = vector_store.similarity_search(input.query, k=input.top_k)
    
    if not results:
        return "No related memories found."
    
    memory_list = []
    for doc in results:
        memory_list.append({
            "content": doc.page_content,
            "type": doc.metadata.get("type"),
            "tags": doc.metadata.get("tags"),
            "importance": doc.metadata.get("importance")
        })
        
    import json
    return json.dumps(memory_list, ensure_ascii=False)