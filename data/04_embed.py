import json
import os
from tqdm import tqdm
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# --- 설정 ---
INPUT_FILE = "step3_complete.json"
PERSIST_DIR = "./chroma_db_top100"
MODEL_NAME = "jhgan/ko-sbert-nli"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} 파일이 없습니다. 03_crawl.py를 먼저 실행하세요.")
        return

    print(f"4단계: 벡터 DB 구축 시작")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    for item in tqdm(data, desc="문서 변환"):
        # 조리 순서 텍스트화
        steps_str = ""
        if isinstance(item.get('instructions'), list):
            steps_str = "\n".join([f"{i+1}. {s}" for i, s in enumerate(item['instructions'])])
        elif isinstance(item.get('instructions'), str):
            steps_str = item['instructions']

        # 재료/키워드 텍스트화
        ing_str = ", ".join([f"{ing['name']} {ing['amount']}" for ing in item['ingredients']])
        kw_str = ", ".join(item.get('keywords', []))

        # 검색에 쓰일 핵심 텍스트 구성
        page_content = (
            f"요리명: {item['name']}\n"
            f"설명: {item['description']}\n"
            f"난이도: {item['difficulty']}\n"
            f"조리시간: {item['cook_time_minutes']}분\n"
            f"재료: {ing_str}\n"
            f"특징: {kw_str}\n"
            f"--- 조리순서 ---\n{steps_str}"
        )

        metadata = {
            "recipe_id": item['recipe_id'],
            "name": item['name'],
            "views": item.get('views', 0)
        }
        documents.append(Document(page_content=page_content, metadata=metadata))

    print("임베딩 모델 로드 및 DB 저장 중...")
    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs={'device': 'cuda' if os.path.exists('/dev/nvidia0') else 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name="recipe_top100"
    )

    print(f"4단계 완료! 저장 경로: {PERSIST_DIR}")
    print(f"총 문서 수: {vectorstore._collection.count()}개")

if __name__ == "__main__":
    main()