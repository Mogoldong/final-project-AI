from pathlib import Path
from typing import List, Optional, Tuple, Any
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


def _ensure_agent(agent_state: Any) -> Any:
    """세션마다 하나의 에이전트를 유지한다."""
    return agent_state or make_agent()


def handle_message(
    user_message: str, history: ChatHistory, agent_state: Optional[Any]
) -> Tuple[ChatHistory, Any, str]:
    """사용자 입력을 받아 LLM 에이전트와 대화한다."""
    if not user_message or not user_message.strip():
        raise gr.Error("메시지를 입력해주세요.")

    history = history or []
    agent = _ensure_agent(agent_state)

    try:
        answer = agent.chat(user_message.strip())
    except Exception as exc:  # pragma: no cover - 오류 슬롯
        raise gr.Error(f"응답 생성 중 문제가 발생했습니다: {exc}") from exc

    updated_history = history + [(user_message, answer)]
    return updated_history, agent, ""


def reset_conversation() -> Tuple[ChatHistory, None, str]:
    """대화와 에이전트를 초기화한다."""
    return [], None, ""


def build_interface() -> gr.Blocks:
    """대화형 Gradio Blocks UI를 구성한다."""
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
            fn=handle_message,
            inputs=[user_input, chatbot, agent_state],
            outputs=[chatbot, agent_state, user_input],
        )
        user_input.submit(
            fn=handle_message,
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