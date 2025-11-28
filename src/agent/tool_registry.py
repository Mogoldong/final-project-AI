
from typing import Any, Callable, Dict, List
from pydantic import BaseModel
import json

from src.rag.retriever import search_recipe, RecipeSearchInput
from src.tools.memory_tools import read_memory, write_memory, ReadMemoryInput, WriteMemoryInput
from src.tools.search_tool import search_google, SearchInput
from src.tools.weather_tool import get_current_weather
from src.tools.weather_tool import GetWeatherInput
from src.tools.time_tool import get_current_time, GetTimeInput
from src.tools.calculator_tool import calculate, CalculatorInput
from src.rag.pdf_retriever import search_food_knowledge, KnowledgeSearchInput

class ToolSpec(BaseModel):
    name: str
    description: str
    input_model: Any
    handler: Callable[[Any], Dict[str, Any]]

def as_openai_tool_spec(spec: ToolSpec) -> Dict[str, Any]:
    schema = spec.input_model.model_json_schema()
    
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": schema,
        },
    }

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}

    def register_tool(self, spec: ToolSpec):
        self._tools[spec.name] = spec

    def list_openai_tools(self) -> List[Dict[str, Any]]:
        return [as_openai_tool_spec(spec) for spec in self._tools.values()]

    def call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._tools:
            return {"error": f"Tool {name} not found"}
        
        spec = self._tools[name]
        try:
            input_data = spec.input_model(**args)
    
            return spec.handler(input_data)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
        

def register_default_tools() -> ToolRegistry:
    reg = ToolRegistry()

    reg.register_tool(ToolSpec(
        name="search_recipe",
        description="사용자의 상황, 기분, 재료 등을 고려하여 적절한 레시피를 검색합니다.",
        input_model=RecipeSearchInput,
        handler=lambda input_data: {"results": search_recipe(input_data)}
    ))

    reg.register_tool(ToolSpec(
        name="read_memory",
        description="사용자의 취향, 과거 대화, 특정 지식 등 저장된 기억을 검색합니다.",
        input_model=ReadMemoryInput,
        handler=read_memory
    ))

    reg.register_tool(ToolSpec(
        name="write_memory",
        description="사용자에 대한 정보나 중요한 대화 내용을 장기 기억에 저장합니다.",
        input_model=WriteMemoryInput,
        handler=write_memory
    ))

    reg.register_tool(ToolSpec(
        name="search_google",
        description="Google 검색을 통해 최신 정보, 재료 시세, 대체 재료, 요리 팁 등을 찾아줍니다. RAG에 없는 정보를 찾을 때 유용합니다.",
        input_model=SearchInput,
        handler=search_google
    ))

    # 은기님 여기다가 툴 추가해주시면 됩니다
    
    reg.register_tool(ToolSpec(
        name="get_weather",
        description="현재 날씨 정보 조회",
        input_model=GetWeatherInput,
        handler=get_current_weather,
    ))

    reg.register_tool(ToolSpec(
        name="get_current_time",
        description="현재 날짜와 시간을 알려줍니다.",
        input_model=GetTimeInput,
        handler=get_current_time,
    ))

    reg.register_tool(ToolSpec(
        name="calculate",
        description="간단한 사칙연산(+, -, *, /)을 수행합니다. 예: '10 + 5'",
        input_model=CalculatorInput,
        handler=calculate,
    ))

    reg.register_tool(ToolSpec(
        name="search_food_knowledge",
        description="요리 재료의 효능, 영양 성분, 요리 용어 등 '지식'적인 내용이 궁금할 때 PDF 문서를 검색합니다.",
        input_model=KnowledgeSearchInput,
        handler=lambda input_data: {"results": search_food_knowledge(input_data)}
    ))
    
    # # 레시피 추천 도구
    # reg.register_tool(ToolSpec(
    #     name="recommend_recipe",
    #     description="기분과 날씨에 따른 레시피 추천",
    #     input_model=RecommendRecipeInput,
    #     handler=lambda args: recommend_recipe(RecommendRecipeInput(**args)),
    # ))
    return reg
