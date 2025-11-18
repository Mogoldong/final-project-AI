#!/bin/bash

# AI Chef Bot 실행 스크립트

echo "🍳 AI Chef Bot 시작 중..."
echo ""

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "💡 .env.example을 복사하여 .env 파일을 만들고 OPENAI_API_KEY를 설정하세요."
    echo ""
    echo "실행: cp .env.example .env"
    echo "그런 다음 .env 파일을 열어 API Key를 입력하세요."
    exit 1
fi

# 벡터 스토어 확인
if [ ! -d "./data/chromaDB" ]; then
    echo "⚠️  벡터 스토어가 없습니다."
    echo "💡 먼저 레시피 데이터를 준비하세요."
    echo ""
    read -p "샘플 데이터로 벡터 스토어를 생성할까요? (y/n): " choice

    if [ "$choice" = "y" ]; then
        echo ""
        echo "📝 샘플 데이터로 벡터 스토어를 생성합니다..."
        python src/rag/prepare_data.py --sample
        echo ""
    else
        echo ""
        echo "실행: python src/rag/prepare_data.py --sample"
        exit 1
    fi
fi

# Gradio 앱 실행
echo "🚀 Gradio GUI를 시작합니다..."
echo "🌐 브라우저에서 http://localhost:7860 으로 접속하세요"
echo ""
python src/app.py
