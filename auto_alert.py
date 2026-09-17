import requests
import pandas as pd

# 설정 정보
BOT_TOKEN = "8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
CHAT_ID = "8796285923"

# 스캔할 종목 데이터 (추후 자유롭게 수정 가능)
stocks = [
    {"종목명": "KB금융", "AI점수": 100},
    {"종목명": "한화에어로스페이스", "AI점수": 100},
    {"종목명": "신한지주", "AI점수": 100},
    {"종목명": "SK하이닉스", "AI점수": 95},
    {"종목명": "LG에너지솔루션", "AI점수": 75},
    {"종목명": "삼성전자", "AI점수": 55}
]

df = pd.DataFrame(stocks)
top_stocks = df[df["AI점수"] >= 90]["종목명"].tolist()

if top_stocks:
    message = f"🚨 <b>[실시간 AI 주식 자동 알림]</b>\n\n현재 강력 추천(90점 이상) 종목:\n👉 <b>{', '.join(top_stocks)}</b>\n\n대시보드에서 실시간 목표가를 확인하세요!"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})
    print("알림 전송 성공!")