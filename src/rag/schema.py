from pydantic import BaseModel, Field
from typing import List, Literal

class Ingredient(BaseModel):
    # 개별 재료의 스키마
    name: str = Field(description="재료명 (예: '돼지고기')")
    amount: str = Field(description="필요한 양 (예: '300g', '1/2개')")

class Recipe(BaseModel):
    # 레시피 데이터 전체 스키마
    recipe_id: str = Field(
        description="레시피 고유 ID (예: 'R_001')",
        examples=["R_001"]
    )
    
    name: str = Field(
        description="요리 이름 (예: '돼지고기 김치찌개')",
        examples=["돼지고기 김치찌개"]
    )
    
    description: str = Field(
        description="요리 소개. ChromaDB가 '의미'로 검색할 핵심 텍스트입니다.",
        examples=["한국인의 소울 푸드. 얼큰하고 칼칼한 맛이 일품인..."]
    )
    
    keywords: List[str] = Field(
        description="검색용 키워드 리스트 (RAG 검색 품질을 높여줌)",
        examples=[["#한식", "#국물", "#스트레스해소", "#비오는날"]]
    )
    
    ingredients: List[Ingredient] = Field(
        description="이 요리에 필요한 'Ingredient' 객체의 리스트"
    )
    
    instructions: List[str] = Field(
        description="조리법 단계 리스트",
        examples=[
            "1. 돼지고기와 김치를 냄비에 넣고 볶습니다.",
            "2. 물을 붓고 20분간 끓입니다."
        ]
    )
    
    cook_time_minutes: int = Field(
        description="총 조리 시간 (분 단위)",
        examples=[30]
    )
    
    difficulty: Literal["하", "중", "상"] = Field(
        description="요리 난이도",
        examples=["중"]
    )
    
    views: int = Field(
        description="조회수",
        examples=[2943433]
    )

class RecipeDatabase(BaseModel):
    recipes: List[Recipe]