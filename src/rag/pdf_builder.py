import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = "data/knowledge/"
CHROMA_PATH = "data/chromaDB/"
COLLECTION_NAME = "food_knowledge"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

def build_pdf_db():
    print(f"'{DATA_PATH}' 폴더에서 지식용 PDF 문서를 스캔")

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"'{DATA_PATH}' 폴더가 없어 생성했습니다. PDF 파일을 넣어주세요.")
        return

    loader = PyPDFDirectoryLoader(DATA_PATH)
    documents = loader.load()
    
    if not documents:
        print("경고: PDF 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(documents)}페이지를 로드")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"문서를 {len(chunks)}개의 청크로 분할")

    print(f"'{COLLECTION_NAME}' 컬렉션에 저장 중")
    
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
        collection_name=COLLECTION_NAME
    )
    
    print("="*40)
    print(f"지식 DB (PDF) 구축 완료!")
    print("="*40)

if __name__ == "__main__":
    build_pdf_db()
