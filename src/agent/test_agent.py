from dotenv import load_dotenv
import os
from src.agent.bot import make_agent

# 환경 변수 로드
load_dotenv()

def main():
    try:
        agent = make_agent()
        print("에이전트: (종료하려면 'q' 또는 'exit' 입력)")
        print("-" * 50)
    except Exception as e:
        print(f"에이전트 로드 실패: {e}")
        return

    while True:
        try:
            user_input = input("\n사용자: ")
            
            if user_input.lower() in ["q", "exit", "quit", "종료"]:
                print("종료")
                break
            
            if not user_input.strip():
                continue

            response = agent.chat(user_input)
            
            print(f"\n셰프봇: {response}")
            print("-" * 50)

        except KeyboardInterrupt:
            print("강제 종료")
            break
        except Exception as e:
            print(f"에러 발생: {e}")

if __name__ == "__main__":
    main()