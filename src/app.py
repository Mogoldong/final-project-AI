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
## 셰프봇 레시피 추천기 - 생레응(생성형 레시피 응용)
셰프봇은 날씨, 시간, 레시피 RAG, 구글 검색, 메모리 등 다양한 도구를 스스로 호출해 가장 알맞은 답을 찾아드립니다.
"""

# 전역 interrupt 상태 관리
interrupt_state = {
    "active": False,
    "thread_id": "default_thread"
}


# 에이전트 객체 확인 및 생성
def _ensure_agent(agent_state: Any) -> Any:
    return agent_state or make_agent()


# 스트리밍 메시지 처리 함수
def handle_message_stream(
    user_message: str, history: ChatHistory, agent_state: Optional[Any]
) -> Generator[Tuple[ChatHistory, Any, str], None, None]:
    
    global interrupt_state
    
    if not user_message or not user_message.strip():
        raise gr.Error("메시지를 입력해주세요.")

    history = history or []
    agent = _ensure_agent(agent_state)

    # interrupt 상태에서 사용자 응답 처리
    if interrupt_state["active"]:
        interrupt_state["active"] = False
        
        # 사용자 메시지 추가
        history = history + [(user_message, "")]
        
        print(f"[DEBUG] Resuming with: {user_message.strip()}")

        # 재개
        accumulated_response = ""
        try:
            for chunk in agent.stream_resume(user_message.strip(), interrupt_state["thread_id"]):
                if chunk["type"] == "ai_message":
                    accumulated_response = chunk["content"]
                    updated_history = history[:-1] + [(user_message, accumulated_response)]
                    yield updated_history, agent, ""
                
                elif chunk["type"] == "tool_call":
                    tool_name = chunk["tool_name"]
                    tool_info = f"\n\n🔧 [{tool_name} 실행 중...]"
                    updated_history = history[:-1] + [(user_message, accumulated_response + tool_info)]
                    yield updated_history, agent, ""
            
            # 최종 응답
            final_history = history[:-1] + [(user_message, accumulated_response)]
            yield final_history, agent, ""
            return
            
        except Exception as exc:
            error_msg = f"❌ 재개 중 문제가 발생했습니다: {exc}"
            error_history = history[:-1] + [(user_message, error_msg)]
            yield error_history, agent, ""
            return

    # 일반 대화 처리
    history = history + [(user_message, "")]
    
    try:
        accumulated_response = ""
        tool_info = ""
        
        for chunk in agent.chat_stream(user_message.strip(), interrupt_state["thread_id"]):
            
            # interrupt 발생 체크
            if chunk["type"] == "interrupt":
                interrupt_state["active"] = True
                
                # interrupt 메시지 표시
                interrupt_msg = chunk["content"].get("message", "검색 한도에 도달했습니다.")
                accumulated_response = f"⚠️ {interrupt_msg}\n\n('응' 또는 '아니'로 답변해주세요)"
                updated_history = history[:-1] + [(user_message, accumulated_response)]
                yield updated_history, agent, ""
                return
            
            # AI 메시지 스트리밍
            elif chunk["type"] == "ai_message":
                accumulated_response = chunk["content"]
                updated_history = history[:-1] + [(user_message, accumulated_response)]
                yield updated_history, agent, ""
            
            # 도구 호출 표시
            elif chunk["type"] == "tool_call":
                tool_name = chunk["tool_name"]
                tool_info = f"\n\n🔧 [{tool_name} 실행 중...]"
                updated_history = history[:-1] + [(user_message, accumulated_response + tool_info)]
                yield updated_history, agent, ""
            
            # 시스템 메시지
            elif chunk["type"] == "system_message":
                system_msg = chunk["content"]
                pass
            
            # 검색 횟수 표시 
            # elif chunk["type"] == "search_count":
            #     count_info = f"\n\n_📊 검색 횟수: {chunk['count']}회_"
            #     updated_history = history[:-1] + [(user_message, accumulated_response + count_info)]
            #     yield updated_history, agent, ""
        
        # 최종 응답
        final_history = history[:-1] + [(user_message, accumulated_response)]
        yield final_history, agent, ""
        
    except Exception as exc:
        error_msg = f"❌ 응답 생성 중 문제가 발생했습니다: {exc}"
        error_history = history[:-1] + [(user_message, error_msg)]
        yield error_history, agent, ""


# 대화 초기화 함수
def reset_conversation() -> Tuple[ChatHistory, None, str]:
    global interrupt_state
    interrupt_state["active"] = False
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
    build_interface().queue().launch(share=True)