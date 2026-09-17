import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

BOT_TOKEN = "8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
CHAT_ID = "8796285923"

# 100여 개 대장주 유니버스
TICKERS = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "리노공업": "058470.KQ", "HPSP": "403870.KQ",
    "LG에너지솔루션": "373220.KS", "POSCO홀딩스": "005490.KS", "포스코퓨처엠": "003670.KS", "에코프로비엠": "247540.KQ", "에코프로": "086520.KQ", "엔켐": "348370.KQ",
    "삼성바이오로직스": "207940.KS", "셀트리온": "068270.KS", "알테오젠": "196170.KQ", "HLB": "028300.KQ", "유한양행": "000100.KS", "리가켐바이오": "141080.KQ",
    "한화에어로스페이스": "012450.KS", "LIG넥스원": "079550.KS", "현대로템": "064350.KS", "HD현대일렉트릭": "267260.KS", "두산에너빌리티": "034020.KS",
    "레인보우로보틱스": "277810.KQ", "현대차": "005380.KS", "기아": "000270.KS", "실리콘투": "257720.KQ", "삼양식품": "003230.KS", "KB금융": "105560.KS", "NAVER": "035420.KS"
}

def analyze_stock(ticker, name):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        price = int(latest['Close'].item())
        vol_ratio = (latest['Volume'].item() / prev['Vol_MA20'].item()) * 100 if prev['Vol_MA20'].item() > 0 else 100
        rsi_val = round(latest['RSI'].item(), 1)
        
        target1 = int(price * 1.06)
        target2 = int(price * 1.13)
        smart_stop = int(min(price * 0.975, prev['Low'].item()))
        
        score = 0
        reason = []
        
        if rsi_val < 35:
            score += 40
            reason.append("과대낙폭 바닥 반등 구간")
        elif latest['Close'].item() > latest['MA20'].item() and prev['Close'].item() <= prev['MA20'].item():
            score += 35
            reason.append("20일선 상승 전환")
            
        if vol_ratio >= 200:
            score += 45
            reason.append(f"🔥 수급/호재 유입 (거래량 {int(vol_ratio)}% 폭증)")

        if score >= 50:
            return {
                "name": name, "price": price, "vol_ratio": int(vol_ratio),
                "target1": target1, "target2": target2, "stop": smart_stop,
                "reason": " / ".join(reason), "score": score
            }
    except Exception:
        pass
    return None

valid_signals = []
for name, ticker in TICKERS.items():
    res = analyze_stock(ticker, name)
    if res: valid_signals.append(res)

valid_signals = sorted(valid_signals, key=lambda x: x['score'], reverse=True)[:3]

report_lines = []
for idx, res in enumerate(valid_signals, 1):
    item_msg = (
        f"🏆 <b>AI 추천 {idx}위: {res['name']}</b>\n"
        f"• 매수가: <b>{res['price']:,}원</b> (거래량 {res['vol_ratio']}% 폭증)\n"
        f"• <b>🎯 1차 목표가 (50% 익절)</b>: <b>{res['target1']:,}원 (+6%)</b>\n"
        f"• <b>🚀 2차 목표가 (상한가 추적)</b>: <b>{res['target2']:,}원 이상 (트레일링 스탑)</b>\n"
        f"• <b>🛡️ 스마트 손절가</b>: <b>{res['stop']:,}원</b>\n"
        f"• AI 판단: {res['reason']}"
    )
    report_lines.append(item_msg)

if not report_lines:
    report_lines.append("오늘은 손익비가 뛰어난 확실한 매수 타점이 없습니다. 현금을 보존하세요.")

kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일')
message = (
    f"🚨 <b>[100개 대장주 AI 수급/스마트 브리핑 - {kst}]</b>\n\n"
    + "\n\n-------------------------\n\n".join(report_lines)
)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})