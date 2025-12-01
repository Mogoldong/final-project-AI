from pathlib import Path
from typing import List, Optional, Tuple, Any, Generator
import sys

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.agent.bot import make_agent

ChatHistory = List[Tuple[str, str]]

INTRO_MD = """
## 셰프봇 레시피 추천기
이제 도시나 기분을 따로 입력하는 대신 자연어로 자유롭게 대화하세요.
셰프봇은 날씨, 시간, 레시피 RAG, 구글 검색, 메모리 등 다양한 도구를 스스로 호출해 가장 알맞은 답을 찾아드립니다.
"""


# 에이전트 객체 확인 및 생성
def _ensure_agent(agent_state: Any) -> Any:
    return agent_state or make_agent()


# 스트리밍 메시지 처리 함수
def handle_message_stream(
    user_message: str, history: ChatHistory, agent_state: Optional[Any]
) -> Generator[Tuple[ChatHistory, Any, str], None, None]:
    
    if not user_message or not user_message.strip():
        raise gr.Error("메시지를 입력해주세요.")

    history = history or []
    agent = _ensure_agent(agent_state)

    # 사용자 메시지 추가
    history = history + [(user_message, "")]
    
    try:
        accumulated_response = ""
        tool_info = ""
        
        for chunk in agent.chat_stream(user_message.strip()): # agent의 chat_stream에서 넘어오는 청크의 타입을 분석
            
            # AI 메시지 스트리밍
            if chunk["type"] == "ai_message": # 에이전트의 메세지로 accumulated_response에 누적되며 실시간으로 출력된다. 
                accumulated_response = chunk["content"]
                updated_history = history[:-1] + [(user_message, accumulated_response)]
                yield updated_history, agent, ""
            
            # 도구 호출 표시
            elif chunk["type"] == "tool_call": # 에이전트가 외부 도구를 호출했음을 알리며 내부 활동을 사용자에게 알린다. 
                tool_name = chunk["tool_name"]
                tool_info = f"\n\n🔧 [{tool_name} 실행 중...]"
                updated_history = history[:-1] + [(user_message, accumulated_response + tool_info)]
                yield updated_history, agent, ""
            
            # elif chunk["type"] == "tool_result":
            #     tool_name = chunk["tool_name"]
            #     tool_info = f"\n\n[{tool_name} 완료]"
            #     updated_history = history[:-1] + [(user_message, accumulated_response + tool_info)]
            #     yield updated_history, agent, ""
            
            # 시스템 메시지 (인터럽트)
            elif chunk["type"] == "system_message": # Google 검색 한도 초과와 같은 Interrupt 또는 시스템 메세지를 처리한다. 
                accumulated_response = chunk["content"]
                updated_history = history[:-1] + [(user_message, accumulated_response)]
                yield updated_history, agent, ""
            
            # 중요한 점은 return아 아니라 yield를 사용하여 스트리밍 방식으로 결과를 반환한다는 것임.
        
        # 최종 응답
        final_history = history[:-1] + [(user_message, accumulated_response)]
        yield final_history, agent, ""
        
    except Exception as exc:
        error_msg = f"❌ 응답 생성 중 문제가 발생했습니다: {exc}"
        error_history = history[:-1] + [(user_message, error_msg)]
        yield error_history, agent, ""


# 대화 초기화 함수
def reset_conversation() -> Tuple[ChatHistory, None, str]:
    return [], None, ""


def build_interface() -> gr.Blocks:
    with gr.Blocks(title="셰프봇 대화형 레시피 추천") as demo:
        gr.Markdown(INTRO_MD)

        chatbot = gr.Chatbot(
            label="셰프봇과의 대화",
            height=400,
            show_label=True,
        )
        user_input = gr.Textbox(
            label="메시지",
            placeholder="예) 오늘 비 오는데 따뜻한 국물 요리 추천해줘",
            lines=3,
        )
        agent_state = gr.State(None)

        with gr.Row():
            send_btn = gr.Button("전송", variant="primary")
            reset_btn = gr.Button("대화 초기화")

        send_btn.click(
            fn=handle_message_stream,
            inputs=[user_input, chatbot, agent_state],
            outputs=[chatbot, agent_state, user_input],
        )
        user_input.submit(
            fn=handle_message_stream,
            inputs=[user_input, chatbot, agent_state],
            outputs=[chatbot, agent_state, user_input],
        )
        reset_btn.click(
            fn=reset_conversation,
            inputs=None,
            outputs=[chatbot, agent_state, user_input],
        )

    return demo


if __name__ == "__main__":
    build_interface().queue().launch()