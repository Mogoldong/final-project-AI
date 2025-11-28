from tools.weather_tool import get_weather_by_city
from tools.recipe_tool import recommend_recipe, RecommendRecipeInput

# 1. 현재 날씨 가져오기
weather = get_weather_by_city("서울")
print(f"현재 {weather['location']} 날씨: {weather['temperature']}, {weather['sky_status']}")

# 2. 레시피 추천
recipe_input = RecommendRecipeInput(
    mood="피곤",
    weather=weather
)

result = recommend_recipe(recipe_input)
print(f"\n추천 레시피: {result['recipe']['name']}")
print(f"재료: {', '.join(result['recipe']['ingredients'])}")
