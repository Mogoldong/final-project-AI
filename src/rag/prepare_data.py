"""
레시피 데이터 준비 스크립트
벡터 스토어를 생성하고 레시피 데이터를 로드
"""

from data_loader import RecipeDataLoader
from vectorstore import RecipeVectorStore
import os
from dotenv import load_dotenv
import argparse


def prepare_vectorstore(use_sample=False, data_dir="./data/raw"):
    """
    벡터 스토어 준비

    Args:
        use_sample: True이면 샘플 데이터 사용, False이면 실제 데이터 사용
        data_dir: 데이터 디렉토리 경로
    """
    # 환경 변수 로드
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("💡 .env 파일에 OPENAI_API_KEY=your-api-key 를 추가하세요.")
        return

    print("=" * 60)
    print("🍳 AI Chef Bot - 레시피 데이터 준비")
    print("=" * 60)

    # 데이터 로더 초기화
    loader = RecipeDataLoader(data_dir=data_dir)

    # 레시피 데이터 로드
    if use_sample:
        print("\n📝 샘플 레시피 데이터를 사용합니다...")
        documents = loader.create_sample_recipes()
    else:
        print(f"\n📁 {data_dir}에서 레시피 데이터를 로드합니다...")
        documents = loader.load_all_recipes()

        if not documents:
            print("⚠️ 로드된 레시피가 없습니다. 샘플 데이터를 사용합니다.")
            documents = loader.create_sample_recipes()

    if not documents:
        print("❌ 레시피 데이터를 로드할 수 없습니다.")
        return

    # 벡터 스토어 생성
    print("\n🔧 벡터 스토어를 생성합니다...")
    vectorstore_manager = RecipeVectorStore()

    # 기존 벡터 스토어 삭제 (있다면)
    if os.path.exists(vectorstore_manager.persist_directory):
        response = input("기존 벡터 스토어가 존재합니다. 삭제하고 새로 만들까요? (y/n): ")
        if response.lower() == 'y':
            vectorstore_manager.delete_vectorstore()
        else:
            print("기존 벡터 스토어에 문서를 추가합니다.")
            vectorstore_manager.add_documents(documents)
            print("\n✅ 벡터 스토어 준비가 완료되었습니다!")
            return

    # 새 벡터 스토어 생성
    vectorstore = vectorstore_manager.create_vectorstore_from_documents(documents)

    print("\n✅ 벡터 스토어 준비가 완료되었습니다!")
    print(f"📍 위치: {vectorstore_manager.persist_directory}")
    print(f"📊 총 문서 수: {len(documents)}")

    # 테스트 검색
    print("\n🔍 테스트 검색을 수행합니다...")
    test_queries = [
        "닭가슴살로 만들 수 있는 요리",
        "30분 안에 만들 수 있는 한식",
        "다이어트 식단"
    ]

    for query in test_queries:
        print(f"\n쿼리: '{query}'")
        results = vectorstore_manager.search_similar_recipes(query, k=2)
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.metadata.get('title', '제목 없음')} ({doc.metadata.get('cuisine_type', '정보 없음')})")

    print("\n" + "=" * 60)
    print("🎉 준비 완료! 이제 AI Chef Bot을 실행할 수 있습니다.")
    print("💡 실행 명령: python src/app.py")
    print("=" * 60)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="AI Chef Bot 데이터 준비")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="샘플 데이터 사용 (기본값: False)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data/raw",
        help="데이터 디렉토리 경로 (기본값: ./data/raw)"
    )

    args = parser.parse_args()

    prepare_vectorstore(use_sample=args.sample, data_dir=args.data_dir)


if __name__ == "__main__":
    main()
