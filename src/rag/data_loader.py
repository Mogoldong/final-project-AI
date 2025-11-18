"""
레시피 데이터 로더
다양한 형식의 레시피 데이터를 로드하고 Document 객체로 변환
"""

from langchain.schema import Document
from typing import List
import json
import os


class RecipeDataLoader:
    """레시피 데이터 로더 클래스"""

    def __init__(self, data_dir="./data/raw"):
        """
        데이터 로더 초기화

        Args:
            data_dir: 레시피 데이터 디렉토리 경로
        """
        self.data_dir = data_dir

    def load_json_recipes(self, file_path: str) -> List[Document]:
        """
        JSON 형식의 레시피 데이터 로드

        Args:
            file_path: JSON 파일 경로

        Returns:
            Document 객체 리스트

        JSON 형식 예시:
        [
            {
                "title": "김치찌개",
                "ingredients": ["돼지고기", "김치", "두부", "양파"],
                "steps": ["1. 재료 준비", "2. 김치 볶기", ...],
                "cooking_time": "30분",
                "difficulty": "쉬움",
                "cuisine_type": "한식",
                "servings": "2인분",
                "calories": "450kcal"
            },
            ...
        ]
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                recipes = json.load(f)

            documents = []

            for recipe in recipes:
                # 레시피 내용 구성
                content = self._format_recipe_content(recipe)

                # 메타데이터 구성
                metadata = {
                    "title": recipe.get("title", "제목 없음"),
                    "difficulty": recipe.get("difficulty", "정보 없음"),
                    "cooking_time": recipe.get("cooking_time", "정보 없음"),
                    "cuisine_type": recipe.get("cuisine_type", "정보 없음"),
                    "servings": recipe.get("servings", "정보 없음"),
                    "calories": recipe.get("calories", "정보 없음"),
                    "source": file_path
                }

                # Document 객체 생성
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)

            print(f"✅ {len(documents)}개의 레시피를 로드했습니다: {file_path}")
            return documents

        except Exception as e:
            print(f"❌ JSON 파일 로드 중 오류 발생: {e}")
            return []

    def _format_recipe_content(self, recipe: dict) -> str:
        """
        레시피 딕셔너리를 텍스트 형식으로 변환

        Args:
            recipe: 레시피 딕셔너리

        Returns:
            포맷팅된 레시피 텍스트
        """
        content = f"# {recipe.get('title', '제목 없음')}\n\n"

        # 기본 정보
        content += f"**난이도:** {recipe.get('difficulty', '정보 없음')}\n"
        content += f"**조리 시간:** {recipe.get('cooking_time', '정보 없음')}\n"
        content += f"**인분:** {recipe.get('servings', '정보 없음')}\n"
        content += f"**칼로리:** {recipe.get('calories', '정보 없음')}\n"
        content += f"**요리 종류:** {recipe.get('cuisine_type', '정보 없음')}\n\n"

        # 재료
        if "ingredients" in recipe:
            content += "## 재료\n"
            for ingredient in recipe["ingredients"]:
                content += f"- {ingredient}\n"
            content += "\n"

        # 조리 방법
        if "steps" in recipe:
            content += "## 조리 방법\n"
            for i, step in enumerate(recipe["steps"], 1):
                content += f"{i}. {step}\n"
            content += "\n"

        # 팁
        if "tips" in recipe:
            content += "## 조리 팁\n"
            content += recipe["tips"] + "\n\n"

        # 영양 정보
        if "nutrition" in recipe:
            content += "## 영양 정보\n"
            for key, value in recipe["nutrition"].items():
                content += f"- {key}: {value}\n"

        return content

    def load_text_recipes(self, file_path: str) -> List[Document]:
        """
        텍스트 형식의 레시피 데이터 로드

        Args:
            file_path: 텍스트 파일 경로

        Returns:
            Document 객체 리스트
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 간단히 전체 내용을 하나의 Document로 변환
            doc = Document(
                page_content=content,
                metadata={"source": file_path}
            )

            print(f"✅ 텍스트 파일을 로드했습니다: {file_path}")
            return [doc]

        except Exception as e:
            print(f"❌ 텍스트 파일 로드 중 오류 발생: {e}")
            return []

    def load_all_recipes(self) -> List[Document]:
        """
        데이터 디렉토리의 모든 레시피 파일 로드

        Returns:
            모든 Document 객체 리스트
        """
        documents = []

        if not os.path.exists(self.data_dir):
            print(f"⚠️ 데이터 디렉토리가 존재하지 않습니다: {self.data_dir}")
            return documents

        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)

            if filename.endswith(".json"):
                docs = self.load_json_recipes(file_path)
                documents.extend(docs)
            elif filename.endswith(".txt"):
                docs = self.load_text_recipes(file_path)
                documents.extend(docs)

        print(f"📚 총 {len(documents)}개의 레시피 문서를 로드했습니다.")
        return documents

    def create_sample_recipes(self) -> List[Document]:
        """
        샘플 레시피 데이터 생성 (테스트용)

        Returns:
            샘플 Document 객체 리스트
        """
        sample_recipes = [
            {
                "title": "김치찌개",
                "ingredients": [
                    "돼지고기 200g",
                    "김치 300g",
                    "두부 1/2모",
                    "양파 1/2개",
                    "대파 1대",
                    "고춧가루 1큰술",
                    "다진 마늘 1큰술",
                    "물 3컵"
                ],
                "steps": [
                    "김치는 한입 크기로 썰고, 돼지고기도 먹기 좋게 썬다",
                    "냄비에 기름을 두르고 김치를 볶는다",
                    "돼지고기를 넣고 함께 볶는다",
                    "물을 붓고 끓인다",
                    "두부와 양파, 대파를 넣고 10분간 더 끓인다",
                    "마지막으로 간을 맞춘다"
                ],
                "cooking_time": "30분",
                "difficulty": "쉬움",
                "cuisine_type": "한식",
                "servings": "2-3인분",
                "calories": "450kcal",
                "tips": "김치는 잘 익은 것을 사용하면 더 맛있습니다. 참치액이나 멸치액젓을 넣으면 감칠맛이 살아납니다."
            },
            {
                "title": "토마토 파스타",
                "ingredients": [
                    "파스타면 200g",
                    "토마토 소스 1컵",
                    "양파 1/2개",
                    "마늘 3쪽",
                    "올리브오일 2큰술",
                    "바질 약간",
                    "파마산 치즈 약간",
                    "소금, 후추 약간"
                ],
                "steps": [
                    "끓는 물에 소금을 넣고 파스타를 삶는다",
                    "팬에 올리브오일을 두르고 다진 마늘을 볶는다",
                    "양파를 넣고 투명해질 때까지 볶는다",
                    "토마토 소스를 넣고 끓인다",
                    "삶은 파스타를 소스에 넣고 버무린다",
                    "바질과 파마산 치즈를 뿌려 완성"
                ],
                "cooking_time": "20분",
                "difficulty": "쉬움",
                "cuisine_type": "양식",
                "servings": "2인분",
                "calories": "520kcal",
                "tips": "파스타를 삶을 때 면수를 조금 남겨두었다가 소스에 넣으면 더 부드럽고 맛있습니다."
            },
            {
                "title": "닭가슴살 샐러드",
                "ingredients": [
                    "닭가슴살 200g",
                    "양상추 100g",
                    "방울토마토 10개",
                    "오이 1/2개",
                    "올리브오일 2큰술",
                    "발사믹 식초 1큰술",
                    "소금, 후추 약간"
                ],
                "steps": [
                    "닭가슴살을 삶아서 한입 크기로 찢는다",
                    "양상추는 씻어서 물기를 뺀다",
                    "방울토마토는 반으로 자르고, 오이는 슬라이스한다",
                    "모든 재료를 볼에 담는다",
                    "올리브오일, 발사믹 식초, 소금, 후추를 섞어 드레싱을 만든다",
                    "드레싱을 뿌려 완성"
                ],
                "cooking_time": "15분",
                "difficulty": "쉬움",
                "cuisine_type": "양식",
                "servings": "1인분",
                "calories": "280kcal",
                "tips": "닭가슴살은 삶을 때 월계수잎과 통후추를 넣으면 누린내를 제거할 수 있습니다."
            }
        ]

        documents = []
        for recipe in sample_recipes:
            content = self._format_recipe_content(recipe)
            metadata = {
                "title": recipe["title"],
                "difficulty": recipe["difficulty"],
                "cooking_time": recipe["cooking_time"],
                "cuisine_type": recipe["cuisine_type"],
                "servings": recipe["servings"],
                "calories": recipe["calories"],
                "source": "sample_data"
            }
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

        print(f"✅ {len(documents)}개의 샘플 레시피를 생성했습니다.")
        return documents
