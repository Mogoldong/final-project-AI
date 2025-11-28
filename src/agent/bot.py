import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from typing import Any, Dict, List

from src.agent.tool_registry import ToolRegistry, register_default_tools
from src.agent.memory_extractor import extract_and_save_memory

load_dotenv()

class RealLLMAgent:
    def __init__(self, registry: ToolRegistry, model: str = "gpt-4o-mini", api_key: str = None):
        self.registry = registry
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = """
        당신은 사용자의 상황과 기분에 맞춰 요리를 추천해주는 AI 셰프봇입니다.
        - 사용자의 취향이나 알레르기 정보를 기억하고 활용하세요.
        - RAG(레시피 검색)에 정보가 없거나, 재료 대체법 등 모르는 내용이 있으면 '구글 검색' 툴을 적극적으로 사용하세요.
        - 항상 친절하고 구체적으로 답변하세요.
        """
        self.history = []

    def chat(self, user_text: str) -> str:
        tools = self.registry.list_openai_tools()
        
        self.history.append({"role": "user", "content": user_text})

        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.history

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            print(f"[Tool Call 감지] {len(msg.tool_calls)}개의 툴을 호출합니다.")
            self.history.append(msg)
            messages.append(msg)

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments or "{}")

                print(f"Tool 실행: {tool_name}({tool_args})")

                tool_result = self.registry.call(tool_name, tool_args)
                
                result_str = json.dumps(tool_result, ensure_ascii=False)

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tool_name,
                    "content": result_str,
                }
                self.history.append(tool_msg)
                messages.append(tool_msg)

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            final_answer = final_response.choices[0].message.content

            self.history.append({"role": "assistant", "content": final_answer})
            
            extract_and_save_memory(user_text, final_answer)
            return final_answer
        final_answer = msg.content
        self.history.append({"role": "assistant", "content": final_answer})
        extract_and_save_memory(user_text, final_answer)
        
        return final_answer

def make_agent(model: str = "gpt-4o-mini") -> RealLLMAgent:
    reg = register_default_tools()
    
    api_key = os.getenv("OPENAI_API_KEY")
    return RealLLMAgent(reg, model=model, api_key=api_key)

if __name__ == "__main__":
    agent = make_agent()
    
    # 시나리오 테스트
    input_text = "나 요즘 다이어트 중이라 저녁은 샐러드만 먹고 있어. 추천해줘." # "오늘 명절이라 가족들이랑 먹을건데 소고기 들어간 국물 요리 추천해줘"
    response = agent.chat(input_text)
    
    print(f"답변: {response}")