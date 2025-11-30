from datetime import datetime
from pydantic import BaseModel

class GetTimeInput(BaseModel):
    pass

def get_current_time(inp: GetTimeInput) -> dict[str, str]:
    print("[Tool] get_current_time")
    now = datetime.now()
    return {"current_time": now.strftime("%Y-%m-%d %H:%M:%S")}