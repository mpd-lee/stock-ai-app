import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 봇 토큰 및 채팅 ID 설정
BOT_TOKEN = "8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
CHAT_ID = "8796285923"

# 분석할 관심 종목 (한국 주식은 코드 뒤에 .KS(코스피) 또는 .KQ(코스닥) 부착)
tickers = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "KB금융": "105560.KS",
    "한화에어로스페이스": "012450.KS",
    "LG에너지솔루션": "373220.KS"
}

def analyze_stock(ticker):
    # 최근 6개월 데이터 수집
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty:
        return None
    
    # 기술적 분석 지표 계산 (20일 이동평균선)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # RSI(상대강도지수) 계산 로직
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 🎯 매수 조건 설정 (둘 중 하나라도 만족하면 추천)
    buy_signal = False
    reason = ""
    
    # 조건 1: RSI 30 이하 (주가가 단기적으로 과도하게 빠져 반등이 예상될 때)
    if latest['RSI'].item() < 30:
        buy_signal = True
        reason = "RSI 30 이하 (과대낙폭, 단기 반등 예상 🟢)"
        
    # 조건 2: 주가가 20일 이동평균선을 아래에서 위로 뚫고 올라갈 때 (상승 추세 전환)
    elif latest['Close'].item() > latest['MA20'].item() and prev['Close'].item() <= prev['MA20'].item():
        buy_signal = True
        reason = "20일선 상향 돌파 (상승 추세로 전환 🚀)"

    return {
        "price": latest['Close'].item(),
        "rsi": round(latest['RSI'].item(), 1),
        "signal": buy_signal,
        "reason": reason
    }

# 전체 종목 분석 실행
report_lines = []
for name, ticker in tickers.items():
    result = analyze_stock(ticker)
    if result and result['signal']:
        report_lines.append(f"✅ <b>{name}</b>\n- 전일 종가: {int(result['price']):,}원\n- RSI 지수: {result['rsi']}\n- 매수 타점: 장 시작 직후 시가 분할매수\n- 추천 사유: {result['reason']}")

# 추천 종목이 있을 경우 텔레그램 전송
if report_lines:
    kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일')
    message = f"🚨 <b>[장 시작 전 AI 매수 브리핑 - {kst}]</b>\n\n빅데이터 분석 결과, 오늘 장에서 주목해야 할 매수 추천 종목입니다:\n\n" + "\n\n".join(report_lines) + "\n\n💡 <i>오전 9시 장이 열리면 흐름을 보고 진입을 고려해 보세요!</i>"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})
    print("분석 리포트 전송 완료!")
else:
    print("오늘은 확실한 매수 신호가 잡힌 종목이 없습니다.")import requests
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
    target_price = int(price * 1.06)  # 🎯 정확한 6% 익절 목표가 계산
    stop_price = int(price * 0.98)    # 🛡️ -2% 리스크 손절가 계산
    
    buy_signal = False
    reason = ""
    
    # 매수 조건 판단
    if latest['RSI'].item() < 30:
        buy_signal = True
        reason = "RSI 30 이하 (단기 과대낙폭 반등 자리)"
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

# 전체 종목 스캔 및 리포트 작성
report_lines = []
for name, ticker in tickers.items():
    res = analyze_stock(ticker)
    if res and res['signal']:
        item_msg = (
            f"📌 <b>{name}</b>\n"
            f"• 기준 종가: {res['price']:,}원\n"
            f"• <b>⏰ 추천 매수 시간</b>: <b>오전 09:00 ~ 09:15</b> (장 시작 직후 시가 분할 매수)\n"
            f"• <b>🎯 6% 목표 매도가</b>: <b>{res['target_price']:,}원</b>\n"
            f"• <b>⏱️ 매도 타이밍 전략</b>: 장중 {res['target_price']:,}원 도달 즉시 전량 매도\n"
            f"• <b>🛡️ 손절 가이드(-2%)</b>: {res['stop_price']:,}원 이탈 시 매도\n"
            f"• 포착 사유: {res['reason']}"
        )
        report_lines.append(item_msg)

# 텔레그램 메세지 전송
if report_lines:
    kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일')
    message = (
        f"🚨 <b>[AI 주식 매수/매도 타이밍 리포트 - {kst}]</b>\n\n"
        f"오늘 실행할 정확한 매수 시간 및 6% 익절 매도 타점입니다:\n\n"
        + "\n\n".join(report_lines) +
        "\n\n💡 <b>실전 매매 팁</b>\n"
        "매수 성공 직후 증권사 앱(HTS/MTS)에서 <b>[지정가 감시/예약매도]</b>를 이용해 목표가에 미리 매도 주문을 걸어두시면, 일하는 중에도 차트를 보지 않고 6% 수익을 자동 체결할 수 있습니다!"
    )
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})
    print("타이밍 리포트 전송 완료!")
else:
    print("오늘 매수 조건에 맞는 종목이 없습니다.")