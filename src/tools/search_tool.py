import os
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

class SearchInput(BaseModel):
    query: str = Field(description="검색할 키워드 (예: '버터 대체 재료', '오늘 서울 날씨')")

def search_google(input: SearchInput) -> str:
    print(f"[Tool] search_google: {input.query}")
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return "Error: Google API key not configured."

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": input.query,
        "num": 3
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        search_results = []
        if "items" in data:
            for item in data["items"]:
                title = item.get("title")
                snippet = item.get("snippet")
                
                search_results.append(f"- {title}: {snippet}")
        
        if not search_results:
            return "No search results found."
            
        return "\n\n".join(search_results)

    except Exception as e:
        return f"Search error: {str(e)}"