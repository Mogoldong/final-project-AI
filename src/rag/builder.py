import json
from pydantic import ValidationError
from typing import List

from src.rag.schema import Recipe 
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

RECIPE_DATA_PATH = "data/raw/recipes.json"

CHROMA_PATH = "data/chromaDB/" 

embeddings = OpenAIEmbeddings()

def load_recipes() -> List[Recipe]:
    print(f"'{RECIPE_DATA_PATH}'에서 레시피 원본 JSON 파일 로드")
    try:
        with open(RECIPE_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            recipes = [Recipe(**recipe) for recipe in data]
            print(f"✅ 성공: {len(recipes)}개의 레시피 로드 및 검증")
            return recipes
    except FileNotFoundError:
        print(f"오류: '{RECIPE_DATA_PATH}' 파일을 찾을 수 없습니다.")
        return []
    except ValidationError as e:
        print(f"오류: JSON 데이터가 'Recipe' 스키마와 일치하지 않습니다.\n{e}")
        return []

def format_recipe_to_text(recipe: Recipe) -> str:
    ingredients_list = "\n".join(f"- {ing.name}: {ing.amount}" for ing in recipe.ingredients)
    instructions_list = "\n".join(recipe.instructions)
    keywords_list = ", ".join(recipe.keywords)

    return f"""
요리명: {recipe.name} (ID: {recipe.recipe_id})
태그: {keywords_list}
난이도: {recipe.difficulty} (조리 시간: {recipe.cook_time_minutes}분)

[소개]
{recipe.description}

[재료]
{ingredients_list}

[조리법]
{instructions_list}
"""

def build_vector_db():
    recipes = load_recipes()
    if not recipes:
        print("레시피가 없음")
        return

    documents = [format_recipe_to_text(recipe) for recipe in recipes]
    
    metadatas = [{"recipe_id": recipe.recipe_id, "source": RECIPE_DATA_PATH} for recipe in recipes]

    print("\nChromaDB에 벡터 데이터 저장 시작...")
    
    vector_db = Chroma.from_texts(
        texts=documents,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=CHROMA_PATH
    )
    
    print("="*30)
    print("ChromaDB 구축 완료")
    print(f"저장 경로: {CHROMA_PATH}")
    print(f"총 {len(documents)}개의 레시피 색인")
    print("="*30)

if __name__ == "__main__":
    build_vector_db()