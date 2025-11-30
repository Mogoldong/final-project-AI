"""
기분 + 날씨 기반 레시피 추천
"""
"""
기분 + 날씨 기반 레시피 추천
"""
from typing import Any, Dict
from pydantic import BaseModel, Field


class RecommendRecipeInput(BaseModel):
    """레시피 추천 입력 스키마"""
    mood: str = Field(..., description="사용자의 기분")
    weather: Dict[str, Any] = Field(..., description="날씨 정보")


def recommend_recipe(input: RecommendRecipeInput) -> Dict[str, Any]:
    print(f"[Tool] recommend_recipe: mood={input.mood}")
    mood = input.mood.lower()
    weather = input.weather
    
    # 날씨 정보 추출
    temp_str = weather.get('temperature', '20°C')
    precipitation = weather.get('precipitation', '없음')
    
    # 온도 파싱
    try:
        temp = float(temp_str.replace('°C', ''))
    except:
        temp = 20
    
    # 레시피 데이터베이스
    recipes = {
        # 추운 날 (15도 미만)
        ("추움", "행복"): {
            "name": "따뜻한 핫초코",
            "ingredients": ["우유", "초콜릿", "마시멜로"],
            "description": "추운 날 기분 좋을 때 즐기는 달콤한 음료",
            "time": "10분"
        },
        ("추움", "우울"): {
            "name": "따뜻한 미역국",
            "ingredients": ["미역", "소고기", "참기름", "마늘"],
            "description": "마음을 따뜻하게 해주는 국물 요리",
            "time": "40분"
        },
        ("추움", "피곤"): {
            "name": "보양 삼계탕",
            "ingredients": ["닭", "인삼", "대추", "마늘", "찹쌀"],
            "description": "피로 회복에 좋은 보양식",
            "time": "90분"
        },
        
        # 따뜻한 날 (15-25도)
        ("따뜻", "행복"): {
            "name": "신선한 포케볼",
            "ingredients": ["연어", "아보카도", "밥", "망고"],
            "description": "상큼한 하와이안 요리",
            "time": "25분"
        },
        ("따뜻", "피곤"): {
            "name": "영양 비빔밥",
            "ingredients": ["밥", "시금치", "콩나물", "고사리", "계란"],
            "description": "영양 가득한 한 그릇",
            "time": "35분"
        },
        
        # 더운 날 (25도 이상)
        ("더움", "행복"): {
            "name": "과일 샐러드",
            "ingredients": ["수박", "파인애플", "블루베리", "민트"],
            "description": "시원하고 상큼한 디저트",
            "time": "15분"
        },
        ("더움", "피곤"): {
            "name": "시원한 콩국수",
            "ingredients": ["소면", "콩국물", "오이", "토마토"],
            "description": "더위를 이기는 여름 별미",
            "time": "20분"
        },
        
        # 비 오는 날
        ("비", "우울"): {
            "name": "따뜻한 토마토 수프",
            "ingredients": ["토마토", "양파", "마늘", "바질", "크림"],
            "description": "비 오는 날 우울함을 달래는 수프",
            "time": "35분"
        },
        ("비", "default"): {
            "name": "바삭한 파전",
            "ingredients": ["부침가루", "파", "해물", "계란"],
            "description": "비 오는 날의 정석",
            "time": "25분"
        }
    }
    
    # 날씨 카테고리 결정
    if "비" in precipitation or "비" in weather.get('sky_status', ''):
        weather_category = "비"
    elif temp < 15:
        weather_category = "추움"
    elif temp < 25:
        weather_category = "따뜻"
    else:
        weather_category = "더움"
    
    # 기분 매칭
    mood_map = {
        "행복": ["행복", "기쁨", "즐거움"],
        "우울": ["우울", "슬픔"],
        "피곤": ["피곤", "지침"],
        "스트레스": ["스트레스", "긴장"]
    }
    
    matched_mood = "default"
    for key, keywords in mood_map.items():
        if any(k in mood for k in keywords):
            matched_mood = key
            break
    
    # 레시피 선택
    recipe_key = (weather_category, matched_mood)
    if recipe_key in recipes:
        recipe = recipes[recipe_key]
    elif (weather_category, "default") in recipes:
        recipe = recipes[(weather_category, "default")]
    else:
        recipe = {
            "name": "건강한 야채 볶음",
            "ingredients": ["브로콜리", "당근", "파프리카"],
            "description": "언제나 좋은 건강 요리",
            "time": "20분"
        }
    
    return {
        "status": "success",
        "recipe": recipe,
        "reasoning": f"{weather_category} + {matched_mood} → {recipe['name']}"
    }
