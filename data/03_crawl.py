import json
import requests
from bs4 import BeautifulSoup
import time
import random
import os
from tqdm import tqdm

# --- 설정 ---
INPUT_FILE = "step2_refined.json"
OUTPUT_FILE = "step3_complete.json"

def get_recipe_steps(recipe_id):
    url = f"https://www.10000recipe.com/recipe/{recipe_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200: return []
        soup = BeautifulSoup(response.text, 'html.parser')
        steps = []
        for div in soup.find_all('div', class_='view_step_cont'):
            media_body = div.find('div', class_='media-body')
            if media_body:
                steps.append(media_body.get_text(strip=True))
        return steps
    except Exception as e:
        print(f"Error {recipe_id}: {e}")
        return []

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} 파일이 없습니다. 02_refine.py를 먼저 실행하세요.")
        return

    print(f"3단계: 조리법 크롤링 시작")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    success_count = 0
    for item in tqdm(data, desc="크롤링 진행 중"):
        steps = get_recipe_steps(item['recipe_id'])
        if steps:
            item['instructions'] = steps
            success_count += 1
        else:
            item['instructions'] = ["상세 조리법을 가져오지 못했습니다."]
        time.sleep(random.uniform(0.5, 1.5))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"3단계 완료: {success_count}개 조리법 수집 -> {OUTPUT_FILE}")

if __name__ == "__main__":
    main()