import os
import json
from typing import TypedDict, Annotated, List, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from src.agent.tool_registry import ToolRegistry, register_default_tools
from src.agent.memory_extractor import extract_and_save_memory

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

class LangGraphAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.registry = register_default_tools()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model, api_key=self.api_key, temperature=0)
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
        
        if not isinstance(messages[0], SystemMessage):
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
            
        return {"messages": results}

    def should_continue(self, state: AgentState) -> Literal["tools", END]:
        last_message = state["messages"][-1]
        
        if last_message.tool_calls:
            return "tools"
        return END

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.run_tools)
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {"tools": "tools", END: END}
        )
        
        workflow.add_edge("tools", "agent")

        memory = MemorySaver()
        
        return workflow.compile(checkpointer=memory)

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
        
        extract_and_save_memory(user_text, final_response)
        
        return final_response


def make_agent(model: str = "gpt-4o-mini") -> LangGraphAgent:
    return LangGraphAgent(model=model)