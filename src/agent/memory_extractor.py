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
You are a memory extraction assistant.
Your task:
Read the given conversation between a user and an assistant.
Decide whether there is any information that should be stored as long-term memory.

Long-term memories include:
- User's stable preferences (e.g., likes spicy food, has peanut allergy).
- Long-term projects or goals (e.g., on a diet).
- Important facts that will likely be useful in future conversations.

Do NOT store:
- Short-lived or trivial facts (e.g., "hello", "thank you").
- Very detailed logs that are unlikely to be reused.

Output:
Return a JSON object matching the MemoryExtractionResult schema.
"""

def extract_and_save_memory(user_input: str, final_answer: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    conversation_snippet = f"User: {user_input}\nAssistant: {final_answer}"
    
    print("\n🧠 [Memory Extractor] 대화 분석 중...")

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
            print(f"내용: {result.content}")
            
            write_input = WriteMemoryInput(
                content=result.content,
                memory_type=result.memory_type,
                importance=result.importance,
                tags=result.tags
            )
            
            save_result = write_memory(write_input)
            print(f"  -> {save_result}")
            
        else:
            print("저장할 중요 정보 없음.")
            
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    extract_and_save_memory(
        user_input="나 요즘 다이어트 중이라 저녁은 샐러드만 먹고 있어.",
        final_answer="네, 알겠습니다. 저칼로리 샐러드 레시피를 찾아드릴게요."
    )