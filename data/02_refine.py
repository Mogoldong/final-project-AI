import json
import re
import os

# --- 설정 ---
INPUT_FILE = "step1_recipes.json"
OUTPUT_FILE = "step2_refined.json"

def split_name_amount(name, amount):
    if amount and amount.strip():
        return name, amount

    # 이름 뒤에 붙은 수량 패턴 분리 (예: 당근1/2개 -> 당근, 1/2개)
    pattern = r'(\d+(?:/\d+|\.\d+)?(?:~\d+(?:/\d+|\.\d+)?)?)\s*([가-힣a-zA-Z]+)?$'
    match = re.search(pattern, name)
    if match:
        quantity_part = match.group(0)
        new_name = name[:match.start()].strip()
        new_amount = quantity_part.strip()
        if not new_name:
            return name, amount
        return new_name, new_amount
    return name, amount

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} 파일이 없습니다. 01_extract.py를 먼저 실행하세요.")
        return

    print(f"2단계: 재료 데이터 정제 중")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    processed_count = 0
    for recipe in data:
        new_ingredients = []
        for ing in recipe['ingredients']:
            new_name, new_amount = split_name_amount(ing['name'], ing['amount'])
            if new_name != ing['name']:
                processed_count += 1
            new_ingredients.append({"name": new_name, "amount": new_amount})
        recipe['ingredients'] = new_ingredients

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"2단계 완료: {processed_count}개 재료 수정됨 -> {OUTPUT_FILE}")

if __name__ == "__main__":
    main()