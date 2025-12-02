import os
import json
from typing import TypedDict, Annotated, List, Literal, Generator, Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from src.agent.tool_registry import ToolRegistry, register_default_tools
from src.agent.memory_extractor import extract_and_save_memory

load_dotenv()


# LangGraph의 상태를 정의한다
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    google_search_count: int


class LangGraphAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.registry = register_default_tools()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model, api_key=self.api_key, temperature=0, streaming=True)
        self.tools_schema = self.registry.list_openai_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools_schema)

        self.system_prompt = """
        당신은 사용자의 상황과 기분에 맞춰 요리를 추천해주는 AI 셰프봇입니다.
        - 사용자의 취향이나 알레르기 정보를 기억(read_memory)하고 활용하세요.
        - RAG(레시피/지식 검색)에 정보가 없거나, 재료 대체법 등 모르는 내용이 있으면 '구글 검색' 툴을 적극적으로 사용하세요.
        - 항상 친절하고 구체적으로 답변하세요.
        """
        
        self.graph = self._build_graph()

    def call_model(self, state: AgentState):
        messages = state["messages"]
        
        # 시스템 프롬프트 추가
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_prompt)] + messages
            
        response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}

    def run_tools(self, state: AgentState):
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            try:
                tool_output = self.registry.call(tool_name, tool_args)
            except Exception as e:
                tool_output = f"Error: {str(e)}"

            content = json.dumps(tool_output, ensure_ascii=False)

            results.append(ToolMessage(
                tool_call_id=tool_id,
                name=tool_name,
                content=content
            ))
            
        google_search_count = state.get("google_search_count", 0)
        search_count_in_turn = sum(1 for msg in results if msg.name == 'search_google')
        
        return {"messages": results, "google_search_count": google_search_count + search_count_in_turn}

    def should_continue(self, state: AgentState) -> Literal["tools", END]:
        last_message = state["messages"][-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END
    
    def check_interrupt(self, state: AgentState):
        """
        인터럽트 체크 노드
        - 검색 횟수가 3회를 초과하면 interrupt() 호출
        """
        current_count = state.get("google_search_count", 0)
        
        # 검색 횟수가 3회를 초과하면 interrupt 발생
        if current_count > 3:
            # interrupt()를 호출하여 사용자 입력을 받음
            user_input = interrupt(
                f"🚨 Google 검색 한도 초과 알림\n\n"
                f"현재 {current_count}회의 검색을 사용했습니다. (권장: 3회)\n"
                f"하루 API 호출 한도는 100회입니다.\n\n"
                f"계속 검색하시겠습니까?"
            )
            
            # 사용자 응답이 있는 경우 처리
            if user_input:
                user_response = str(user_input).strip().lower()
                
                # 사용자가 계속 진행을 선택한 경우
                if user_response in ["continue", "yes", "네", "계속", "y", "ㅇㅇ", "응", "ok"]:
                    return {"messages": [SystemMessage(
                        content="[시스템] 사용자가 검색 계속 진행을 승인했습니다."
                    )]}
                else:
                    # 중단을 선택한 경우
                    return {"messages": [SystemMessage(
                        content="[시스템] 사용자가 검색 중단을 선택했습니다. 현재 정보로만 답변하세요."
                    )]}
        
        # 정상 진행
        return {"messages": []}

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # 노드 추가
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.run_tools)
        workflow.add_node("check_interrupt", self.check_interrupt)

        workflow.set_entry_point("agent")
        
        # agent → tools 또는 END
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        
        # tools → check_interrupt
        workflow.add_edge("tools", "check_interrupt")
        
        # check_interrupt → agent
        workflow.add_edge("check_interrupt", "agent")

        memory = MemorySaver()
        
        return workflow.compile(checkpointer=memory)

    def chat(self, user_text: str, thread_id: str = "default_thread") -> str:
        """
        일반 채팅 메서드
        
        Returns:
            str: AI의 응답 또는 interrupt 정보
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=user_text)]},
            config
        )
        
        # interrupt가 발생한 경우 확인
        if "__interrupt__" in result:
            interrupt_info = result["__interrupt__"][0].value
            return f"[INTERRUPT] {interrupt_info}"
        
        # 정상 응답
        final_response = ""
        if "messages" in result:
            last_msg = result["messages"][-1]
            if isinstance(last_msg, AIMessage):
                final_response = last_msg.content
        
        if final_response:
            extract_and_save_memory(user_text, final_response)
        
        return final_response
    
    def resume_chat(self, user_response: str, thread_id: str = "default_thread") -> str:
        """
        인터럽트 후 재개 메서드
        
        Args:
            user_response: 사용자의 응답 (continue 또는 stop)
            thread_id: 스레드 ID
            
        Returns:
            str: AI의 최종 응답
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        # Command(resume=...)로 재개
        result = self.graph.invoke(
            Command(resume=user_response),
            config
        )
        
        # 또 다른 interrupt가 발생한 경우
        if "__interrupt__" in result:
            interrupt_info = result["__interrupt__"][0].value
            return f"[INTERRUPT] {interrupt_info}"
        
        # 정상 응답
        final_response = ""
        if "messages" in result:
            last_msg = result["messages"][-1]
            if isinstance(last_msg, AIMessage):
                final_response = last_msg.content
        
        return final_response
    
    def chat_stream(self, user_text: str, thread_id: str = "default_thread") -> Generator[Dict[str, Any], None, None]:
        """
        스트리밍 버전
        
        Yields:
            dict: 각 노드의 실행 결과
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        final_response = ""
        interrupted = False
        
        for event in self.graph.stream(
            {"messages": [HumanMessage(content=user_text)]},
            config,
            stream_mode="updates"
        ):
            for node_name, update_value in event.items():
                
                # interrupt 체크
                if "__interrupt__" in update_value:
                    interrupted = True
                    interrupt_info = update_value["__interrupt__"][0].value
                    yield {
                        "node": node_name,
                        "type": "interrupt",
                        "content": interrupt_info
                    }
                    continue
                
                if "messages" in update_value:
                    messages = update_value["messages"]
                    
                    for msg in messages:
                        # AIMessage 처리
                        if isinstance(msg, AIMessage):
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    yield {
                                        "node": node_name,
                                        "type": "tool_call",
                                        "tool_name": tool_call["name"],
                                        "tool_args": tool_call["args"]
                                    }
                            elif msg.content:
                                yield {
                                    "node": node_name,
                                    "type": "ai_message",
                                    "content": msg.content
                                }
                                final_response = msg.content
                        
                        # ToolMessage 처리
                        elif isinstance(msg, ToolMessage):
                            try:
                                tool_result = json.loads(msg.content)
                            except:
                                tool_result = msg.content
                            
                            yield {
                                "node": node_name,
                                "type": "tool_result",
                                "tool_name": msg.name,
                                "result": tool_result
                            }
                        
                        # SystemMessage 처리
                        elif isinstance(msg, SystemMessage):
                            yield {
                                "node": node_name,
                                "type": "system_message",
                                "content": msg.content
                            }
                
                # google_search_count 업데이트
                if "google_search_count" in update_value:
                    yield {
                        "node": node_name,
                        "type": "search_count",
                        "count": update_value["google_search_count"]
                    }
        
        # interrupt가 아닌 경우에만 메모리 저장
        if final_response and not interrupted:
            extract_and_save_memory(user_text, final_response)
    
    def stream_resume(self, user_response: str, thread_id: str = "default_thread") -> Generator[Dict[str, Any], None, None]:
        """
        인터럽트 후 재개 스트리밍
        
        Args:
            user_response: 사용자의 응답
            thread_id: 스레드 ID
            
        Yields:
            dict: 각 노드의 실행 결과
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        for event in self.graph.stream(
            Command(resume=user_response),
            config,
            stream_mode="updates"
        ):
            for node_name, update_value in event.items():
                
                # interrupt 체크
                if "__interrupt__" in update_value:
                    interrupt_info = update_value["__interrupt__"][0].value
                    yield {
                        "node": node_name,
                        "type": "interrupt",
                        "content": interrupt_info
                    }
                    continue
                
                if "messages" in update_value:
                    messages = update_value["messages"]
                    
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    yield {
                                        "node": node_name,
                                        "type": "tool_call",
                                        "tool_name": tool_call["name"],
                                        "tool_args": tool_call["args"]
                                    }
                            elif msg.content:
                                yield {
                                    "node": node_name,
                                    "type": "ai_message",
                                    "content": msg.content
                                }
                        
                        elif isinstance(msg, ToolMessage):
                            try:
                                tool_result = json.loads(msg.content)
                            except:
                                tool_result = msg.content
                            
                            yield {
                                "node": node_name,
                                "type": "tool_result",
                                "tool_name": msg.name,
                                "result": tool_result
                            }
                        
                        elif isinstance(msg, SystemMessage):
                            yield {
                                "node": node_name,
                                "type": "system_message",
                                "content": msg.content
                            }


def make_agent(model: str = "gpt-4o-mini") -> LangGraphAgent:
    return LangGraphAgent(model=model)