"""
웹 스크래핑 도구
레시피 웹사이트에서 데이터를 수집 (선택사항)
"""

from bs4 import BeautifulSoup
import requests
from typing import List, Dict
import time


class RecipeScraper:
    """레시피 웹 스크래퍼 클래스"""

    def __init__(self):
        """스크래퍼 초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def scrape_recipe(self, url: str) -> Dict:
        """
        단일 레시피 페이지 스크래핑

        Args:
            url: 레시피 페이지 URL

        Returns:
            레시피 데이터 딕셔너리
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 기본 레시피 구조 (사이트마다 다를 수 있음)
            recipe = {
                "title": self._extract_title(soup),
                "ingredients": self._extract_ingredients(soup),
                "steps": self._extract_steps(soup),
                "cooking_time": self._extract_cooking_time(soup),
                "difficulty": self._extract_difficulty(soup),
                "cuisine_type": "정보 없음",
                "servings": self._extract_servings(soup),
                "calories": "정보 없음",
                "source_url": url
            }

            return recipe

        except Exception as e:
            print(f"❌ 스크래핑 중 오류 발생: {e}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """제목 추출"""
        # 일반적인 제목 태그들을 시도
        title_tags = soup.find_all(['h1', 'h2'], class_=['title', 'recipe-title', 'heading'])
        if title_tags:
            return title_tags[0].get_text(strip=True)
        return "제목 없음"

    def _extract_ingredients(self, soup: BeautifulSoup) -> List[str]:
        """재료 목록 추출"""
        ingredients = []

        # 일반적인 재료 목록 패턴
        ingredient_sections = soup.find_all(['ul', 'ol'], class_=['ingredients', 'ingredient-list'])

        for section in ingredient_sections:
            items = section.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                if text:
                    ingredients.append(text)

        return ingredients

    def _extract_steps(self, soup: BeautifulSoup) -> List[str]:
        """조리 단계 추출"""
        steps = []

        # 일반적인 조리 단계 패턴
        step_sections = soup.find_all(['ol', 'ul'], class_=['steps', 'instructions', 'directions'])

        for section in step_sections:
            items = section.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                if text:
                    steps.append(text)

        return steps

    def _extract_cooking_time(self, soup: BeautifulSoup) -> str:
        """조리 시간 추출"""
        time_tags = soup.find_all(['span', 'div'], class_=['time', 'cooking-time', 'prep-time'])
        if time_tags:
            return time_tags[0].get_text(strip=True)
        return "정보 없음"

    def _extract_difficulty(self, soup: BeautifulSoup) -> str:
        """난이도 추출"""
        difficulty_tags = soup.find_all(['span', 'div'], class_=['difficulty', 'level'])
        if difficulty_tags:
            return difficulty_tags[0].get_text(strip=True)
        return "정보 없음"

    def _extract_servings(self, soup: BeautifulSoup) -> str:
        """인분 수 추출"""
        serving_tags = soup.find_all(['span', 'div'], class_=['servings', 'yield'])
        if serving_tags:
            return serving_tags[0].get_text(strip=True)
        return "정보 없음"

    def scrape_multiple_recipes(self, urls: List[str], delay: float = 1.0) -> List[Dict]:
        """
        여러 레시피 페이지 스크래핑

        Args:
            urls: 레시피 페이지 URL 리스트
            delay: 요청 간 대기 시간 (초)

        Returns:
            레시피 데이터 리스트
        """
        recipes = []

        for i, url in enumerate(urls, 1):
            print(f"🔍 스크래핑 중... ({i}/{len(urls)}): {url}")

            recipe = self.scrape_recipe(url)

            if recipe:
                recipes.append(recipe)

            # 서버 부하 방지를 위한 대기
            if i < len(urls):
                time.sleep(delay)

        print(f"✅ 총 {len(recipes)}개의 레시피를 스크래핑했습니다.")
        return recipes

    def save_to_json(self, recipes: List[Dict], output_file: str):
        """
        스크래핑한 레시피를 JSON 파일로 저장

        Args:
            recipes: 레시피 데이터 리스트
            output_file: 저장할 파일 경로
        """
        import json

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(recipes, f, ensure_ascii=False, indent=2)

            print(f"💾 레시피가 {output_file}에 저장되었습니다.")

        except Exception as e:
            print(f"❌ 파일 저장 중 오류 발생: {e}")


# 사용 예시
if __name__ == "__main__":
    """
    사용 예시:

    scraper = RecipeScraper()

    # 단일 레시피 스크래핑
    recipe = scraper.scrape_recipe("https://example.com/recipe/kimchi-jjigae")

    # 여러 레시피 스크래핑
    urls = [
        "https://example.com/recipe/1",
        "https://example.com/recipe/2",
    ]
    recipes = scraper.scrape_multiple_recipes(urls)

    # JSON 파일로 저장
    scraper.save_to_json(recipes, "./data/raw/scraped_recipes.json")
    """
    print("RecipeScraper 클래스를 임포트하여 사용하세요.")
    print("자세한 사용법은 주석을 참고하세요.")
