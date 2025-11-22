import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from typing import Any, Dict, List

from src.agent.tool_registry import ToolRegistry, register_default_tools

load_dotenv()

class RealLLMAgent:
    def __init__(self, registry: ToolRegistry, model: str = "gpt-4o-mini", api_key: str = None):
        self.registry = registry
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = "당신은 사용자의 상황과 기분에 맞춰 요리를 추천해주는 AI 셰프봇입니다."

    def chat(self, user_text: str) -> str:
        tools = self.registry.list_openai_tools()
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_text},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments or "{}")

                tool_result = self.registry.call(tool_name, tool_args)
                
                result_str = json.dumps(tool_result, ensure_ascii=False)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tool_name,
                    "content": result_str,
                })

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return final_response.choices[0].message.content

        return msg.content

def make_agent(model: str = "gpt-4o-mini") -> RealLLMAgent:
    reg = register_default_tools()
    
    api_key = os.getenv("OPENAI_API_KEY")
    return RealLLMAgent(reg, model=model, api_key=api_key)

if __name__ == "__main__":
    agent = make_agent()
    
    # 시나리오 테스트
    input_text = "오늘 명절이라 가족들이랑 먹을건데 소고기 들어간 국물 요리 추천해줘"
    response = agent.chat(input_text)
    
    print(f"답변: {response}")