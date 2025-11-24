"""
기상청 초단기실황 API - 현재 날씨 조회
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import requests
from datetime import datetime
import os

class GetWeatherInput(BaseModel):
    """날씨 조회 입력 스키마"""
    location: str = Field(default="서울", description="지역명")
    nx: int = Field(default=60, description="격자 X 좌표")
    ny: int = Field(default=127, description="격자 Y 좌표")


def get_current_weather(input: GetWeatherInput) -> Dict[str, Any]:
    """
    기상청 초단기실황 API로 현재 날씨 정보를 가져옵니다.
    
    Args:
        input: GetWeatherInput 스키마
    
    Returns:
        현재 날씨 정보 딕셔너리
    """
    api_key = os.getenv("WEATHER_API_KEY", "fca9276cce6d40fcae13687aed00a004fa87354fd41d093c5d66c10de2667020")
    
    # API 키가 없으면 Mock 데이터 반환
    if not api_key:
        return {
            "status": "mock",
            "location": input.location,
            "temperature": "15°C",
            "humidity": "60%",
            "precipitation": "없음",
            "wind_speed": "2.5m/s",
            "sky_status": "맑음"
        }
    
    # 현재 시간 기준 설정
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")  # 정시 기준
    
    # API 호출
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    
    params = {
        'serviceKey': api_key,
        'pageNo': 1,
        'numOfRows': 10,
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': input.nx,
        'ny': input.ny
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # 응답 파싱
        if response.status_code == 200:
            items = data['response']['body']['items']['item']
            
            weather_info = {
                "status": "success",
                "location": input.location,
                "temperature": None,
                "humidity": None,
                "precipitation": None,
                "wind_speed": None,
                "sky_status": "맑음"
            }
            # 카테고리별 데이터 추출
            for item in items:
                category = item.get('category')
                value = item.get('obsrValue')
                
                if category == 'T1H':  # 기온
                    weather_info['temperature'] = f"{value}°C"
                elif category == 'REH':  # 습도
                    weather_info['humidity'] = f"{value}%"
                elif category == 'RN1':  # 1시간 강수량
                    weather_info['precipitation'] = "비" if float(value) > 0 else "없음"
                elif category == 'WSD':  # 풍속
                    weather_info['wind_speed'] = f"{value}m/s"
                elif category == 'PTY':  # 강수형태
                    if value == '1':
                        weather_info['sky_status'] = "비"
                    elif value == '2':
                        weather_info['sky_status'] = "비/눈"
                    elif value == '3':
                        weather_info['sky_status'] = "눈"
            
            return weather_info
        else:
            # API 오류 시 Mock 데이터
            return {
                "status": "error_fallback",
                "location": input.location,
                "temperature": "15°C",
                "humidity": "60%",
                "precipitation": "없음",
                "wind_speed": "2.5m/s",
                "sky_status": "맑음"
            }
    
    except Exception as e:
        # 예외 발생 시 Mock 데이터
        return {
            "status": "exception_fallback",
            "location": input.location,
            "temperature": "15°C",
            "humidity": "60%",
            "precipitation": "없음",
            "wind_speed": "2.5m/s",
            "sky_status": "맑음",
            "error": str(e)
        }


# 주요 지역 좌표
LOCATION_COORDS = {
    "서울": (60, 127),
    "부산": (98, 76),
    "대구": (89, 90),
    "인천": (55, 124),
    "광주": (58, 74),
    "대전": (67, 100),
    "울산": (102, 84),
    "수원": (60, 121),
    "제주": (52, 38)
}


def get_weather_by_city(city: str) -> Dict[str, Any]:
    """
    도시 이름으로 날씨 조회
    
    Args:
        city: 도시명 (예: "서울")
    
    Returns:
        날씨 정보
    """
    coords = LOCATION_COORDS.get(city, (60, 127))
    return get_current_weather(GetWeatherInput(
        location=city,
        nx=coords[0],
        ny=coords[1]
    ))


# 독립 테스트
if __name__ == "__main__":
    print("="*60)
    print("현재 날씨 조회 테스트")
    print("="*60)
    
    result = get_weather_by_city("서울")
    print(f"\n📍 위치: {result['location']}")
    print(f"🌡️  온도: {result['temperature']}")
    print(f"💧 습도: {result['humidity']}")
    print(f"☔ 강수: {result['precipitation']}")
    print(f"🌤️  하늘: {result['sky_status']}")
    print(f"💨 풍속: {result['wind_speed']}")
