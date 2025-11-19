from typing import Any, Callable, Dict, List
from pydantic import BaseModel
import json

from src.rag.retriever import search_recipe, RecipeSearchInput

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

    # 은기님 여기다가 툴 추가해주시면 됩니다
    return reg