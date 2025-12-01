import json
import os
from pydantic import ValidationError
from typing import List

from src.rag.schema import Recipe 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

RECIPE_DATA_PATH = "data/raw/recipes.json"
CHROMA_PATH = "data/chromaDB/" 

# 임베딩 모델 지정
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# 원본 recipes.json 파일 로드 함수
def load_recipes() -> List[Recipe]:
    try:
        with open(RECIPE_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            recipes = [Recipe(**recipe) for recipe in data]
            return recipes
    except FileNotFoundError:
        print(f"Error: '{RECIPE_DATA_PATH}' 파일을 찾을 수 없습니다.")
        return []
    except ValidationError as e:
        print(f"Error: JSON 데이터가 'Recipe' 스키마와 일치하지 않습니다.\n{e}")
        return []

# 레시피 객체를 텍스트 형식으로 변환하는 함수
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

# 벡터 데이터베이스 구축 함수
def build_vector_db():
    recipes = load_recipes()
    if not recipes:
        print("No recipes found")
        return

    documents = [format_recipe_to_text(recipe) for recipe in recipes]
    
    metadatas = [{"recipe_id": recipe.recipe_id, "source": RECIPE_DATA_PATH} for recipe in recipes]
    
    vector_db = Chroma.from_texts(
        texts=documents,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=CHROMA_PATH
    )