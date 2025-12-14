import pandas as pd
import json
import os
import re

# 사전 라이브러리 설치
# pip install pandas requests beautifulsoup4 tqdm langchain langchain-community langchain-huggingface langchain-chroma chromadb sentence-transformers

# --- 설정 ---
CSV_FILES = ["TB-2022.csv", "TB-2023.csv", "TB-2024.csv"]
OUTPUT_FILE = "step1_recipes.json"
TOP_N = 100

def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.replace('\\', '/').replace('"', "'")
    text = re.sub(r'[\x00-\x1f\x7f]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_ingredients(text):
    if not isinstance(text, str) or not text.strip(): return []
    text = clean_text(text)
    text = re.sub(r'\[.*?\]\s*', '', text)
    ingredients = []
    for part in text.split('|'):
        part = clean_text(part)
        if not part: continue
        split_idx = part.rfind(' ')
        if split_idx == -1:
            name, amt = part, ""
        else:
            name, amt = part[:split_idx].strip(), part[split_idx+1:].strip()
        ingredients.append({"name": name, "amount": amt})
    return ingredients

def parse_keywords(row):
    cols = ['CKG_MTH_ACTO_NM', 'CKG_STA_ACTO_NM', 'CKG_MTRL_ACTO_NM', 'CKG_KND_ACTO_NM']
    kws = []
    for c in cols:
        if c in row and pd.notna(row[c]):
            val = clean_text(str(row[c]))
            if val: kws.append(f"#{val}")
    return kws

def parse_cook_time(text):
    if not isinstance(text, str): return 0
    text = clean_text(text)
    m = 0
    h_match = re.search(r'(\d+)시간', text)
    if h_match: m += int(h_match.group(1)) * 60
    min_match = re.search(r'(\d+)분', text)
    if min_match: m += int(min_match.group(1))
    if m == 0:
        num_match = re.search(r'(\d+)', text)
        if num_match: m = int(num_match.group(1))
    return m

def main():
    print(f"1단계: CSV 로드 및 상위 {TOP_N}개 추출")
    all_dfs = []
    
    for file in CSV_FILES:
        if not os.path.exists(file):
            print(f"파일 없음: {file}")
            continue
            
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except:
            try:
                df = pd.read_csv(file, encoding='cp949', encoding_errors='ignore')
            except Exception as e:
                print(f"로드 실패 {file}: {e}")
                continue
        
        print(f"✅ {file} 로드 완료 ({len(df)}행)")
        all_dfs.append(df)

    if not all_dfs:
        return

    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df.drop_duplicates(subset=['RCP_SNO'], inplace=True)
    full_df['INQ_CNT'] = pd.to_numeric(full_df['INQ_CNT'], errors='coerce').fillna(0)

    top_df = full_df.sort_values(by='INQ_CNT', ascending=False).head(TOP_N)

    recipes_data = []
    for _, row in top_df.iterrows():
        recipe_json = {
            "recipe_id": str(row['RCP_SNO']),
            "name": clean_text(row['CKG_NM']),
            "description": clean_text(row['CKG_IPDC']),
            "keywords": parse_keywords(row),
            "ingredients": parse_ingredients(row['CKG_MTRL_CN']),
            "instructions": [], 
            "cook_time_minutes": parse_cook_time(row['CKG_TIME_NM']),
            "difficulty": clean_text(row['CKG_DODF_NM']),
            "views": int(row['INQ_CNT'])
        }
        recipes_data.append(recipe_json)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(recipes_data, f, ensure_ascii=False, indent=2)
    
    print(f"1단계 완료: {OUTPUT_FILE} 저장됨")

if __name__ == "__main__":
    main()