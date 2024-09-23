import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

# 캐시 및 재시도 세션 설정
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)

# OpenMeteo API 클라이언트 생성
openmeteo = openmeteo_requests.Client(session=retry_session)

# API 요청을 위한 URL과 파라미터 설정
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 37.566,               # 서울의 위도
    "longitude": 126.9784,            # 서울의 경도
    "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"], # 일별 날씨 코드와 최대,최저 기온 요청
    "timezone": "Asia/Tokyo",          # 타임존을 아시아/도쿄로 설정
    "forecast_days": 16               # 16일간의 예보 요청
}

# OpenMeteo API로부터 날씨 데이터 요청
responses = openmeteo.weather_api(url, params=params)

# 첫 번째 응답 데이터를 선택 (서울 위치에 대한 데이터)
response = responses[0]

# 일별 날씨 데이터를 가져옴
daily = response.Daily()

# 날씨 코드와 최대, 최저 기온 데이터를 Numpy 배열로 추출
daily_weather_code = daily.Variables(0).ValuesAsNumpy()  # 일별 날씨 코드
daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()  # 일별 최대 기온
daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()  # 일별 최저 기온

# 날씨 코드 매핑: 숫자 코드에 대응하는 한국어 날씨 설명
weather_code_mapping = {
    0: "☀", # "맑은 하늘"
    1: "🌤", # "대체로 맑음"
    2: "🌥", # "약간 흐림"
    3: "☁", # "흐림"
    45: "🌫", # "안개와 쌓이는 서리 안개"
    48: "🌫", # "안개와 쌓이는 서리 안개"
    51: "🌦", # "이슬비: 가벼움"
    53: "🌦", # "이슬비: 보통"
    55: "🌦", # "이슬비: 짙은 강도"
    56: "🌦🧊", # "얼음 이슬비: 가볍고 짙은 강도"
    57: "🌦🧊", # "얼음 이슬비: 짙은 강도"
    61: "☔", # "비: 약간"
    63: "☔", # "비: 보통"
    65: "☔", # "비: 강함"
    66: "🌧🧊", # "빙우: 가볍고 강한 강도"
    67: "🌧🧊", # "빙우: 강한 강도"
    71: "❄", # "눈 내림: 약간"
    73: "❄", # "눈 내림: 보통"
    75: "❄", # "눈 내림: 강함"
    77: "❄", # "눈알"
    80: "🌧", # "소나기: 약간"
    81: "🌧", # "소나기: 보통"
    82: "🌧", # "소나기: 강렬"
    85: "🌨", # "눈소나기: 약간 내림"
    86: "🌨", # "눈소나기: 많이 내림"
    95: "🌩", # "뇌우: 약간 또는 중간"
    96: "🌩🧊", # "가벼운 우박과 강한 우박을 동반한 뇌우"
    99: "🌩🧊", # "가벼운 우박과 강한 우박을 동반한 뇌우"
}

# 일별 데이터를 DataFrame으로 변환
daily_data = {
    "날짜": pd.date_range(  # 날짜 범위를 생성
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),  # 시작 날짜 (초 단위, UTC)
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),  # 종료 날짜 (초 단위, UTC)
        freq=pd.Timedelta(seconds=daily.Interval()),  # 시간 간격을 초 단위로 설정
        inclusive="left"  # 시작일을 포함하고 종료일을 제외
    )
}

# 날씨 코드에 대한 한국어 설명 매핑, 일별 최대, 최저 기온 설정
daily_data["날씨"] = [weather_code_mapping.get(code, "알 수 없음") for code in daily_weather_code]  # 날씨 코드 매핑
daily_data["최고기온"] = daily_temperature_2m_max  # 최고기온 설정
daily_data["최저기온"] = daily_temperature_2m_min  # 최저기온 설정

# DataFrame으로 변환
daily_dataframe = pd.DataFrame(data=daily_data)

# DataFrame을 리스트로 변환한 후 한 줄씩 출력
daily_list = daily_dataframe.values.tolist()
weather_list = []
# for entry in daily_list:
#     # 날짜 형식을 문자열로 변환 (시간 부분 제외)
#     entry[0] = entry[0].strftime('%Y-%m-%d')  # 날짜를 'YYYY-MM-DD' 형식으로 변환
#     entry[2] = int(round(entry[2]))  # 최고 기온을 정수로 변환
#     entry[3] = int(round(entry[3]))  # 최저 기온을 정수로 변환
#     weather_list.append(entry)

for entry in daily_list:
    weather_entry = {
        "date": entry[0].strftime('%Y-%m-%d'),  # 'YYYY-MM-DD' format
        "weather": entry[1],  # Weather description
        "tempMax": int(round(entry[2])),  # Max temperature rounded to nearest integer
        "tempMin": int(round(entry[3]))   # Min temperature rounded to nearest integer
    }
    weather_list.append(weather_entry)
