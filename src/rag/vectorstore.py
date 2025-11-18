"""
벡터 스토어 생성 및 관리
ChromaDB를 사용한 레시피 임베딩 저장
"""

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from typing import List


class RecipeVectorStore:
    """레시피 벡터 스토어 관리 클래스"""

    def __init__(self, persist_directory="./data/chromaDB"):
        """
        벡터 스토어 초기화

        Args:
            persist_directory: 벡터 스토어 저장 경로
        """
        self.persist_directory = persist_directory
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

        # 임베딩 모델 초기화
        self.embeddings = OpenAIEmbeddings(api_key=self.api_key)

        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    def create_vectorstore_from_documents(self, documents: List[Document]):
        """
        문서 리스트로부터 벡터 스토어 생성

        Args:
            documents: Document 객체 리스트

        Returns:
            vectorstore: 생성된 벡터 스토어
        """
        try:
            print(f"📄 총 {len(documents)}개의 문서를 처리합니다...")

            # 문서 분할
            split_docs = self.text_splitter.split_documents(documents)
            print(f"✂️ {len(split_docs)}개의 청크로 분할되었습니다.")

            # 벡터 스토어 생성
            print("🔄 벡터 임베딩을 생성하고 있습니다...")
            vectorstore = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )

            print(f"✅ 벡터 스토어가 {self.persist_directory}에 저장되었습니다.")
            return vectorstore

        except Exception as e:
            print(f"❌ 벡터 스토어 생성 중 오류 발생: {e}")
            raise

    def load_vectorstore(self):
        """
        기존 벡터 스토어 로드

        Returns:
            vectorstore: 로드된 벡터 스토어
        """
        try:
            if not os.path.exists(self.persist_directory):
                raise FileNotFoundError(f"벡터 스토어가 {self.persist_directory}에 존재하지 않습니다.")

            vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

            print(f"✅ 벡터 스토어를 {self.persist_directory}에서 로드했습니다.")
            return vectorstore

        except Exception as e:
            print(f"❌ 벡터 스토어 로드 중 오류 발생: {e}")
            raise

    def add_documents(self, documents: List[Document]):
        """
        기존 벡터 스토어에 문서 추가

        Args:
            documents: 추가할 Document 객체 리스트
        """
        try:
            vectorstore = self.load_vectorstore()

            # 문서 분할
            split_docs = self.text_splitter.split_documents(documents)

            # 문서 추가
            vectorstore.add_documents(split_docs)

            print(f"✅ {len(split_docs)}개의 청크가 벡터 스토어에 추가되었습니다.")

        except Exception as e:
            print(f"❌ 문서 추가 중 오류 발생: {e}")
            raise

    def search_similar_recipes(self, query: str, k: int = 5):
        """
        유사한 레시피 검색

        Args:
            query: 검색 쿼리
            k: 반환할 결과 개수

        Returns:
            검색 결과 리스트
        """
        try:
            vectorstore = self.load_vectorstore()
            results = vectorstore.similarity_search(query, k=k)

            print(f"🔍 '{query}'에 대한 검색 결과 {len(results)}개를 찾았습니다.")
            return results

        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")
            raise

    def delete_vectorstore(self):
        """벡터 스토어 삭제"""
        import shutil

        try:
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                print(f"🗑️ 벡터 스토어가 삭제되었습니다: {self.persist_directory}")
            else:
                print("⚠️ 삭제할 벡터 스토어가 없습니다.")

        except Exception as e:
            print(f"❌ 벡터 스토어 삭제 중 오류 발생: {e}")
            raise
