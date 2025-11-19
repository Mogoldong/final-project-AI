### 작업 시 참고사항
1. 작업 위치
- Tool 에 관련된 파일은 모두 src/tools 디렉토리에 작성해주세요.

2. 코드 작성 규칙
- Pydantic 라이브러리를 사용해 입출력 데이터를 검증합니다. 
- src/tools/schema.py 이런식으로 파일 만들고 정의하면 됩니다.
- src/rag/schema.py 파일을 참고해주세요.
- ChromaDB를 사용하는(RAG) 툴이라면 src/rag/.. 에 넣어주시고 아니라면 src/tools/.. 에 넣어주세요.

3. 에이전트에 Tool 등록
- Tool 함수 작성이 끝나면 ToolRegistry에 등록해야합니다. (파일 경로 src/agent/tool_registry.py)
'''
from src.tools.(새로운 파일 이름) import (Tool 이름)

def register_default_tools() -> ToolRegistry:
    # ... (기존 코드들) ...

    # 2. 툴 등록 (이 부분에 추가)
    reg.register_tool(ToolSpec(
        name="",  # 에이전트가 부를 이름
        description="", # AI가 이해할 설명
        input_model= ... ,     # 정의한 Input 스키마
        handler= ...  # 정의한 함수 이름
    ))
    
    return reg
'''

4. 독립 테스트
- 툴을 만든 후 에이전트 등록 전 툴이 작동하는지 확인하고 싶다면 해당 파일 하단에 if __name__ == "__main__": 블록을 만들어 함수가 잘 동작하는지 먼저 테스트해보면 됩니다.
