import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 봇 토큰 및 채팅 ID 설정
BOT_TOKEN = "8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
CHAT_ID = "8796285923"

# 관심 종목 리스트
tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "KB금융": "105560.KS",
    "한화에어로스페이스": "012450.KS",
    "LG에너지솔루션": "373220.KS"
}

def analyze_stock(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty:
            return None
        
        # 20일 이동평균선 및 RSI 계산
        df['MA20'] = df['Close'].rolling(window=20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        price = int(latest['Close'].item())
        target_price = int(price * 1.06)  # 6% 목표가
        stop_price = int(price * 0.98)    # -2% 손절가
        
        buy_signal = False
        reason = ""
        
        # 매수 조건
        if latest['RSI'].item() < 30:
            buy_signal = True
            reason = "RSI 30 이하 (과대낙폭 반등 자리)"
        elif latest['Close'].item() > latest['MA20'].item() and prev['Close'].item() <= prev['MA20'].item():
            buy_signal = True
            reason = "20일선 상향 돌파 (상승 추세 전환)"

        return {
            "price": price,
            "target_price": target_price,
            "stop_price": stop_price,
            "rsi": round(latest['RSI'].item(), 1),
            "signal": buy_signal,
            "reason": reason
        }
    except Exception as e:
        print(f"{ticker} 분석 오류: {e}")
        return None

# 전체 종목 스캔
report_lines = []
for name, ticker in tickers.items():
    res = analyze_stock(ticker)
    if res and res['signal']:
        item_msg = (
            f"📌 <b>{name}</b>\n"
            f"• 기준 종가: {res['price']:,}원\n"
            f"• <b>⏰ 추천 매수 시간</b>: <b>오전 09:00 ~ 09:15</b>\n"
            f"• <b>🎯 6% 목표 매도가</b>: <b>{res['target_price']:,}원</b>\n"
            f"• <b>⏱️ 매도 타이밍 전략</b>: 장중 {res['target_price']:,}원 도달 즉시 전량 매도\n"
            f"• <b>🛡️ 손절 가이드(-2%)</b>: {res['stop_price']:,}원 이탈 시 매도\n"
            f"• 포착 사유: {res['reason']}"
        )
        report_lines.append(item_msg)

# 조건 만족 종목이 없을 때 텔레그램 작동 확인용 샘플 리포트 생성
if not report_lines:
    report_lines.append(
        "📌 <b>[시스템 테스트] 삼성전자</b>\n"
        "• 기준 종가: 70,000원\n"
        "• <b>⏰ 추천 매수 시간</b>: <b>오전 09:00 ~ 09:15</b>\n"
        "• <b>🎯 6% 목표 매도가</b>: <b>74,200원</b>\n"
        "• <b>⏱️ 매도 타이밍 전략</b>: 장중 74,200원 도달 즉시 전량 매도\n"
        "• <b>🛡️ 손절 가이드(-2%)</b>: 68,600원 이탈 시 매도\n"
        "• 포착 사유: (현재 조건 만족 종목이 없어 작동 테스트용 예시로 발송됨)"
    )

# 텔레그램 메세지 전송
kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일')
message = (
    f"🚨 <b>[AI 주식 매수/매도 타이밍 리포트 - {kst}]</b>\n\n"
    f"오늘 실행할 정확한 매수 시간 및 6% 익절 매도 타점입니다:\n\n"
    + "\n\n".join(report_lines)
)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})
print("전송 결과 코드:", res.status_code)