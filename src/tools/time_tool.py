from datetime import datetime
from pydantic import BaseModel

class GetTimeInput(BaseModel):
    pass

def get_current_time(inp: GetTimeInput) -> dict[str, str]:
    """현재 날짜와 시간을 반환합니다."""
    now = datetime.now()
    return {"current_time": now.strftime("%Y-%m-%d %H:%M:%S")}

if __name__ == "__main__":
    time_input = GetTimeInput()
    time_result = get_current_time(time_input)
    print(time_result)
