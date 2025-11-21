from tools.weather_tool import GetWeatherInput, get_current_weather
from tools.recipe_tool import RecommendRecipeInput, recommend_recipe

def register_default_tools() -> ToolRegistry:
    registry = ToolRegistry()
    
    # 날씨 도구
    registry.register_tool(ToolSpec(
        name="get_weather",
        description="현재 날씨 정보 조회",
        input_model=GetWeatherInput,
        handler=lambda args: get_current_weather(GetWeatherInput(**args)),
    ))
    
    # 레시피 추천 도구
    registry.register_tool(ToolSpec(
        name="recommend_recipe",
        description="기분과 날씨에 따른 레시피 추천",
        input_model=RecommendRecipeInput,
        handler=lambda args: recommend_recipe(RecommendRecipeInput(**args)),
    ))
    
    return registry
