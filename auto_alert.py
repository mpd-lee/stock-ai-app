import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 봇 토큰 및 채팅 ID 설정
BOT_TOKEN = "8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
CHAT_ID = "8796285923"

# 코스피(KS) 및 코스닥(KQ) 주요 관심 종목 확대
tickers = {
    # KOSPI (우량 및 주도주)
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "한화에어로스페이스": "012450.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "KB금융": "105560.KS",
    
    # KOSDAQ (변동성이 좋아 6% 달성에 유리한 주도주)
    "에코프로비엠": "247540.KQ",
    "알테오젠": "196170.KQ",
    "HLB": "028300.KQ",
    "리노공업": "058470.KQ",
    "HPSP": "403870.KQ"
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
        target_price = int(price * 1.06)  # 🎯 6% 익절가
        stop_price = int(price * 0.98)    # 🛡️ -2% 손절가
        
        buy_signal = False
        reason = ""
        
        if latest['RSI'].item() < 30:
            buy_signal = True
            reason = "RSI 30 이하 (과대낙폭 반등 유력)"
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
    except Exception:
        return None

# 전체 종목 스캔
report_lines = []
for name, ticker in tickers.items():
    res = analyze_stock(ticker)
    if res and res['signal']:
        item_msg = (
            f"📌 <b>{name}</b>\n"
            f"• 전일 종가: {res['price']:,}원\n"
            f"• <b>⏰ 매수 시간</b>: <b>오전 09:00 ~ 09:15</b> (시초가 변동성 활용)\n"
            f"• <b>🎯 6% 목표가</b>: <b>{res['target_price']:,}원</b>\n"
            f"• <b>⏱️ 매도 전략</b>: 매수 직후 증권사 앱 <b>[자동 감시 주문]</b>에 {res['target_price']:,}원을 걸어두세요. 도달 즉시 기계적으로 자동 매도됩니다.\n"
            f"• <b>🛡️ 손절가(-2%)</b>: {res['stop_price']:,}원\n"
            f"• 포착 사유: {res['reason']}"
        )
        report_lines.append(item_msg)

# 조건 만족 종목이 없을 경우
if not report_lines:
    report_lines.append("오늘은 6% 수익 전략에 부합하는 KOSPI/KOSDAQ 매수 신호가 없습니다. 억지로 매매하지 않고 현금을 보유하는 것도 훌륭한 전략입니다.")

# 텔레그램 메세지 전송
kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일')
message = (
    f"🚨 <b>[KOSPI/KOSDAQ 통합 6% AI 브리핑 - {kst}]</b>\n\n"
    + "\n\n".join(report_lines)
)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})