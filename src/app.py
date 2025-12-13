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
    user_message: str, history: List[dict], agent_state: Optional[Any]
) -> Generator[Tuple[List[dict], Any, str], None, None]:
    
    global interrupt_state
    
    if not user_message or not user_message.strip():
        raise gr.Error("메시지를 입력해주세요.")

    # history가 None이면 빈 리스트로 초기화
    history = history or []
    agent = _ensure_agent(agent_state)

    # 1. 사용자 메시지 추가 (딕셔너리 형태)
    history.append({"role": "user", "content": user_message})
    
    # 2. AI 응답을 위한 빈 말풍선 미리 추가
    history.append({"role": "assistant", "content": ""})

    # ------------------------------------------------------------------
    # CASE A: Interrupt 상태에서 복귀 (사용자 응답 처리)
    # ------------------------------------------------------------------
    if interrupt_state["active"]:
        interrupt_state["active"] = False
        print(f"[DEBUG] Resuming with: {user_message.strip()}")

        try:
            accumulated_response = ""
            
            # stream_resume 호출
            for chunk in agent.stream_resume(user_message.strip(), interrupt_state["thread_id"]):
                
                if chunk["type"] == "ai_message":
                    accumulated_response = chunk["content"]
                    # 마지막 메시지(AI) 내용을 실시간 업데이트
                    history[-1]["content"] = accumulated_response
                    yield history, agent, ""
                
                elif chunk["type"] == "tool_call":
                    tool_name = chunk["tool_name"]
                    tool_info = f"\n\n🔧 [{tool_name} 실행 중...]"
                    # 도구 실행 정보를 기존 응답 뒤에 붙여서 표시
                    history[-1]["content"] = accumulated_response + tool_info
                    yield history, agent, ""
            
            # 최종 응답 확정
            history[-1]["content"] = accumulated_response
            yield history, agent, ""
            return
            
        except Exception as exc:
            error_msg = f"❌ 재개 중 문제가 발생했습니다: {exc}"
            history[-1]["content"] = error_msg
            yield history, agent, ""
            return

    # ------------------------------------------------------------------
    # CASE B: 일반 대화 처리
    # ------------------------------------------------------------------
    try:
        accumulated_response = ""
        
        for chunk in agent.chat_stream(user_message.strip(), interrupt_state["thread_id"]):
            
            # 1. Interrupt 발생 시 (검색 한도 초과 등)
            if chunk["type"] == "interrupt":
                interrupt_state["active"] = True
                
                interrupt_msg = chunk["content"].get("message", "검색 한도에 도달했습니다.")
                warning_msg = f"⚠️ {interrupt_msg}\n\n('응' 또는 '아니'로 답변해주세요)"
                
                history[-1]["content"] = warning_msg
                yield history, agent, ""
                return
            
            # 2. 일반 AI 메시지 스트리밍
            elif chunk["type"] == "ai_message":
                accumulated_response = chunk["content"]
                history[-1]["content"] = accumulated_response
                yield history, agent, ""
            
            # 3. 도구 호출 표시
            elif chunk["type"] == "tool_call":
                tool_name = chunk["tool_name"]
                tool_info = f"\n\n🔧 [{tool_name} 실행 중...]"
                history[-1]["content"] = accumulated_response + tool_info
                yield history, agent, ""
            
            # 4. 시스템 메시지 (무시)
            elif chunk["type"] == "system_message":
                pass
        
        # 최종 응답 확정
        history[-1]["content"] = accumulated_response
        yield history, agent, ""
        
    except Exception as exc:
        error_msg = f"❌ 응답 생성 중 문제가 발생했습니다: {exc}"
        history[-1]["content"] = error_msg
        yield history, agent, ""

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