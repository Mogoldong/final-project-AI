import os
import json
from typing import TypedDict, Annotated, List, Literal, Generator, Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from src.agent.tool_registry import ToolRegistry, register_default_tools
from src.agent.memory_extractor import extract_and_save_memory

load_dotenv()

class BaseMessage:
    """기본 메시지 클래스"""
    def __init__(self, content: str = "", **kwargs):
        self.content = content
        self.additional_kwargs = kwargs
    
    def __repr__(self):
        return f"{self.__class__.__name__}(content='{self.content}')"


class SystemMessage(BaseMessage):
    """시스템 메시지"""
    type: str = "system"


class HumanMessage(BaseMessage):
    """사용자 메시지"""
    type: str = "human"


class AIMessage(BaseMessage):
    """AI 응답 메시지"""
    type: str = "ai"
    
    def __init__(self, content: str = "", tool_calls: List[Dict] = None, **kwargs):
        super().__init__(content, **kwargs)
        self.tool_calls = tool_calls or []


class ToolMessage(BaseMessage):
    """도구 실행 결과 메시지"""
    type: str = "tool"
    
    def __init__(self, content: str = "", tool_call_id: str = "", name: str = "", **kwargs):
        super().__init__(content, **kwargs)
        self.tool_call_id = tool_call_id
        self.name = name

# LangGraph의 상태를 정의한다. messages는 대화 기록을, google_search_count는 구글 검색 툴 사용 횟수를 추적한다.
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    google_search_count: int

class LangGraphAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.registry = register_default_tools()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model, api_key=self.api_key, temperature=0, streaming=True) # Streaming 기능 활성화
        self.tools_schema = self.registry.list_openai_tools() # LLM이 외부 도구를 사용할 수 있도록 도구 스키마를 가져옴
        self.llm_with_tools = self.llm.bind_tools(self.tools_schema)

        self.system_prompt = """
        당신은 사용자의 상황과 기분에 맞춰 요리를 추천해주는 AI 셰프봇입니다.
        - 사용자의 취향이나 알레르기 정보를 기억(read_memory)하고 활용하세요.
        - RAG(레시피/지식 검색)에 정보가 없거나, 재료 대체법 등 모르는 내용이 있으면 '구글 검색' 툴을 적극적으로 사용하세요.
        - 항상 친절하고 구체적으로 답변하세요.

        ** 중요: Google 검색 횟수가 3회를 초과하면, 시스템이 경고 메시지를 보냅니다. 
        이때 사용자가 '네', '계속', 'yes' 등으로 답변하면 검색을 계속 진행하고,
        그 외의 답변이면 검색 없이 현재 정보로만 답변하세요.
        """
        
        self.graph = self._build_graph()

    # Agent 노드로 현재 상태에서 메세지를 LLM에 전달하고 응답(response)을 받는다.
    def call_model(self, state: AgentState):
        messages = state["messages"]
        
        if not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_prompt)] + messages
            
        response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}

    # LLM이 요청한 툴에서 name, args, id를 추출하여 실행하고 ToolMessage 형태로 반환한다. 이 과정에서 google_search_count도 업데이트한다.
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

    # Agent 노드의 다음을 결정한다. 인터럽트 발생이나 tool 호출 여부에 따라 분기한다. 
    def should_continue(self, state: AgentState) -> Literal["tools", END]:
        last_message = state["messages"][-1]

        if isinstance(last_message, SystemMessage) and "인터럽트 발생" in last_message.content:
            return END
        
        if last_message.tool_calls:
            return "tools"
        return END
    
    # chkeck_interrupt 노드의 다음을 결정한다. 인터럽트 메세지가 있다면 종료하고 아니라면 계속 진행한다.
    def should_loop(self, state: AgentState) -> Literal["loop", END]:
        last_message = state["messages"][-1]
        
        if isinstance(last_message, SystemMessage) and "인터럽트 발생" in last_message.content:
            return END
        
        return "loop"

    # 그래프 구축
    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # 추론, 도구실행, 인터럽트 확인 3가지 노드 구현
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.run_tools)
        workflow.add_node("check_interrupt", self.check_interrupt)

        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {"tools": "tools", END: END}
        ) # LLM이 도구 호출을 했느냐에 따라 tools 노드로 갈지 END로 갈지 결정하는 분기 로직
        
        workflow.add_edge("tools", "check_interrupt")

        workflow.add_conditional_edges(
            "check_interrupt",
            self.should_loop,
            {
                "loop": "agent",
                END: END,
            } # 인터럽트 발생 후 계속할지 종료할지 결정하는 분기 로직
        )

        memory = MemorySaver() # 체크포인터로 설정하여 messages와 google_search_count 를 thread id 별로 저장
        
        return workflow.compile(checkpointer=memory)

    # 기존 버전
    def chat(self, user_text: str, thread_id: str = "default_thread") -> str:
        config = {"configurable": {"thread_id": thread_id}}
        
        events = self.graph.stream(
            {"messages": [HumanMessage(content=user_text)]},
            config, 
            stream_mode="values"
        )
        
        final_response = ""
        for event in events:
            if "messages" in event:
                last_msg = event["messages"][-1]
                if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
                    final_response = last_msg.content
                elif isinstance(last_msg, SystemMessage) and "인터럽트 발생" in last_msg.content:
                    final_response = last_msg.content
        
        extract_and_save_memory(user_text, final_response)
        
        return final_response
    
    # app.py의 handle_message_stream에서 요구하는 실시간 응답을 제공하는 메서드
    def chat_stream(self, user_text: str, thread_id: str = "default_thread") -> Generator[Dict[str, Any], None, None]:
        """
        스트리밍 버전 - 각 노드의 실행 결과를 실시간으로 반환
        
        Returns:
            Generator yielding dictionaries with:
            - node: 노드 이름
            - type: 메시지 타입 (ai_message, tool_call, system_message 등)
            - content: 메시지 내용
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        final_response = ""
        
        # stream_mode="updates"로 각 노드의 업데이트를 받음
        for event in self.graph.stream(
            {"messages": [HumanMessage(content=user_text)]},
            config,
            stream_mode="updates"
        ):
            # event는 {node_name: update_value} 형태의 딕셔너리
            for node_name, update_value in event.items():
                
                # messages가 업데이트된 경우
                if "messages" in update_value:
                    messages = update_value["messages"]
                    
                    for msg in messages:
                        # AIMessage 처리
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                # 도구 호출
                                for tool_call in msg.tool_calls:
                                    yield {
                                        "node": node_name,
                                        "type": "tool_call",
                                        "tool_name": tool_call["name"],
                                        "tool_args": tool_call["args"]
                                    }
                            elif msg.content:
                                # 일반 AI 응답
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
                        
                        # SystemMessage 처리 (인터럽트 메시지)
                        elif isinstance(msg, SystemMessage):
                            if "인터럽트 발생" in msg.content or "알림" in msg.content:
                                yield {
                                    "node": node_name,
                                    "type": "system_message",
                                    "content": msg.content
                                }
                                final_response = msg.content
                
                # google_search_count 업데이트
                if "google_search_count" in update_value:
                    yield {
                        "node": node_name,
                        "type": "search_count",
                        "count": update_value["google_search_count"]
                    }
        
        # 메모리 저장
        if final_response:
            extract_and_save_memory(user_text, final_response)
    
    def check_interrupt(self, state: AgentState):
        current_count = state.get("google_search_count", 0)
        
        if current_count >= 4:
            interrupt_message = SystemMessage(
                content=f"🚨 [알림] Google 검색 툴을 권장 한도(3회)를 초과하여 사용했습니다. "
                    f"하루 API 호출 한도는 100회입니다. (현재 {current_count}회 사용)\n\n"
                    f"그래도 계속 검색을 진행하시겠습니까? "
                    f"계속하려면 '네' 또는 '계속'이라고 입력해주세요. "
                    f"중단하려면 다른 질문을 해주세요."
            )
            return {"messages": [interrupt_message]}
    
        return {"messages": []}


def make_agent(model: str = "gpt-4o-mini") -> LangGraphAgent:
    return LangGraphAgent(model=model)