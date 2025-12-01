"""
기상청 초단기실황 API - 현재 날씨 조회
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import requests
from datetime import datetime
import os

class GetWeatherInput(BaseModel):
    location: str = Field(default="Seoul", description="지역명")
    nx: int = Field(default=60, description="격자 X 좌표")
    ny: int = Field(default=127, description="격자 Y 좌표")


def get_current_weather(input: GetWeatherInput) -> Dict[str, Any]:
    print(f"[Tool] get_current_weather: {input.location}")
    api_key = os.getenv("WEATHER_API_KEY")
    
    if not api_key:
        return {
            "status": "mock",
            "location": input.location,
            "temperature": "15C",
            "humidity": "60%",
            "precipitation": "None",
            "wind_speed": "2.5m/s",
            "sky_status": "Clear"
        }
    
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")
    
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
        
        if response.status_code == 200:
            items = data['response']['body']['items']['item']
            
            weather_info = {
                "status": "success",
                "location": input.location,
                "temperature": None,
                "humidity": None,
                "precipitation": None,
                "wind_speed": None,
                "sky_status": "Clear"
            }
            for item in items:
                category = item.get('category')
                value = item.get('obsrValue')
                
                if category == 'T1H':
                    weather_info['temperature'] = f"{value}C"
                elif category == 'REH':
                    weather_info['humidity'] = f"{value}%"
                elif category == 'RN1':
                    weather_info['precipitation'] = "Rain" if float(value) > 0 else "None"
                elif category == 'WSD':
                    weather_info['wind_speed'] = f"{value}m/s"
                elif category == 'PTY':
                    if value == '1':
                        weather_info['sky_status'] = "Rain"
                    elif value == '2':
                        weather_info['sky_status'] = "Rain/Snow"
                    elif value == '3':
                        weather_info['sky_status'] = "Snow"
            
            return weather_info
        else:
            return {
                "status": "error_fallback",
                "location": input.location,
                "temperature": "15C",
                "humidity": "60%",
                "precipitation": "None",
                "wind_speed": "2.5m/s",
                "sky_status": "Clear"
            }
    
    except Exception as e:
        return {
            "status": "exception_fallback",
            "location": input.location,
            "temperature": "15C",
            "humidity": "60%",
            "precipitation": "None",
            "wind_speed": "2.5m/s",
            "sky_status": "Clear",
            "error": str(e)
        }


LOCATION_COORDS = {
    "Seoul": (60, 127),
    "Busan": (98, 76),
    "Daegu": (89, 90),
    "Incheon": (55, 124),
    "Gwangju": (58, 74),
    "Daejeon": (67, 100),
    "Ulsan": (102, 84),
    "Suwon": (60, 121),
    "Jeju": (52, 38)
}


def get_weather_by_city(city: str) -> Dict[str, Any]:
    coords = LOCATION_COORDS.get(city, (60, 127))
    return get_current_weather(GetWeatherInput(
        location=city,
        nx=coords[0],
        ny=coords[1]
    ))
