import os
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from dotenv import load_dotenv

from src.tools.memory_tools import write_memory, WriteMemoryInput

load_dotenv()

class MemoryExtractionResult(BaseModel):
    should_write_memory: bool = Field(description="메모리에 저장할 가치가 있는지 여부")
    memory_type: Optional[Literal["profile", "episodic", "knowledge"]] = Field(description="메모리 타입")
    importance: Optional[int] = Field(description="중요도 (1~5)")
    content: Optional[str] = Field(description="저장할 핵심 내용 요약")
    tags: Optional[List[str]] = Field(description="관련 태그")

EXTRACTOR_SYSTEM_PROMPT = """
당신은 메모리 추출 어시스턴트입니다.
역할:
사용자와 어시스턴트 간의 대화를 읽고, 장기 기억에 저장할 정보가 있는지 판단하세요.

장기 기억에 저장해야 할 정보:
- 사용자의 안정적인 선호도 (예: 매운 음식을 좋아함, 땅콩 알레르기 있음)
- 장기 프로젝트 또는 목표 (예: 다이어트 중)
- 향후 대화에서 유용할 만한 중요한 사실

저장하지 말아야 할 정보:
- 일시적이거나 사소한 사실 (예: "안녕", "감사합니다")
- 재사용될 가능성이 낮은 상세한 로그

출력:
MemoryExtractionResult 스키마와 일치하는 JSON 객체를 반환하세요.
"""

def extract_and_save_memory(user_input: str, final_answer: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    conversation_snippet = f"User: {user_input}\nAssistant: {final_answer}"
    
    print("[Memory] Analyzing conversation...")

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
                {"role": "user", "content": f"[CONVERSATION]\n{conversation_snippet}"}
            ],
            response_format=MemoryExtractionResult,
        )
        
        result = completion.choices[0].message.parsed
        
        if result.should_write_memory:
            print(f"Content: {result.content}")
            
            write_input = WriteMemoryInput(
                content=result.content,
                memory_type=result.memory_type,
                importance=result.importance,
                tags=result.tags
            )
            
            save_result = write_memory(write_input)
            print(f"  -> {save_result}")
            
        else:
            print("No important information to save")
            
    except Exception as e:
        print(f"Error: {e}")