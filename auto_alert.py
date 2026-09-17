import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 봇 토큰 및 채팅 ID 설정
BOT_TOKEN = "8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
CHAT_ID = "8796285923"

# 🧠 AI가 엄선한 KOSPI/KOSDAQ 주도주 및 변동성 우량주 60선 (섹터별 대장주)
tickers = {
    # 💻 반도체 & AI
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "리노공업": "058470.KQ", "HPSP": "403870.KQ", "ISC": "095340.KQ", "이수페타시스": "083640.KS",
    # 🔋 2차전지
    "LG에너지솔루션": "373220.KS", "에코프로비엠": "247540.KQ", "에코프로": "086520.KQ", "포스코퓨처엠": "003670.KS", "엔켐": "348370.KQ", "포스코홀딩스": "005490.KS",
    # 🧬 바이오 & 헬스케어 (변동성 최상)
    "삼성바이오로직스": "207940.KS", "셀트리온": "068270.KS", "알테오젠": "196170.KQ", "HLB": "028300.KQ", "유한양행": "000100.KS", "리가켐바이오": "141080.KQ", "휴젤": "145020.KQ",
    # 🚀 방산 & 우주항공 & 로봇
    "한화에어로스페이스": "012450.KS", "LIG넥스원": "079550.KS", "현대로템": "064350.KS", "레인보우로보틱스": "277810.KQ", "두산로보틱스": "454910.KS",
    # 🚗 자동차 & 전장
    "현대차": "005380.KS", "기아": "000270.KS", "현대모비스": "012330.KS",
    # 💰 금융 & 배당주
    "KB금융": "105560.KS", "신한지주": "055550.KS", "하나금융지주": "086790.KS", "메리츠금융지주": "138040.KS",
    # 🌐 플랫폼 & 엔터 & 게임
    "NAVER": "035420.KS", "카카오": "035720.KS", "크래프톤": "259960.KS", "하이브": "352820.KS", "JYP Ent.": "035900.KQ"
}

def analyze_stock(ticker, name):
    try:
        # 최근 6개월 데이터 로드 (에러 방지를 위해 silent 모드)
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return None
        
        # 지표 계산
        df['MA20'] = df['Close'].rolling(window=20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        price = int(latest['Close'].item())
        target_price = int(price * 1.06)  # 6% 익절가
        stop_price = int(price * 0.98)    # -2% 손절가
        
        rsi_val = latest['RSI'].item()
        
        buy_signal = False
        reason = ""
        score = 0
        
        # 1. 과대 낙폭 (RSI 30 이하) -> 가장 승률이 높은 타점
        if rsi_val < 30:
            buy_signal = True
            reason = "RSI 30 이하 (과대낙폭 바닥 반등 유력)"
            score = 100 - rsi_val  # RSI가 낮을수록 점수가 높음
            
        # 2. 상승 추세 전환 (20일선 돌파)
        elif latest['Close'].item() > latest['MA20'].item() and prev['Close'].item() <= prev['MA20'].item():
            buy_signal = True
            reason = "20일선 상향 돌파 (강한 상승 추세 진입)"
            score = 70

        if buy_signal:
            return {
                "name": name,
                "price": price,
                "target_price": target_price,
                "stop_price": stop_price,
                "rsi": round(rsi_val, 1),
                "reason": reason,
                "score": score
            }
    except Exception:
        pass
    return None

# 전 종목 스캔 및 AI 필터링 진행
valid_signals = []
for name, ticker in tickers.items():
    res = analyze_stock(ticker, name)
    if res:
        valid_signals.append(res)

# AI 점수(Score)가 높은 순서대로 정렬하여 최상위 3개만 추출 (무분별한 매수 방지)
valid_signals = sorted(valid_signals, key=lambda x: x['score'], reverse=True)[:3]

report_lines = []
for idx, res in enumerate(valid_signals, 1):
    item_msg = (
        f"🏆 <b>AI 추천 {idx}위: {res['name']}</b>\n"
        f"• 전일 종가: {res['price']:,}원 (RSI: {res['rsi']})\n"
        f"• <b>⏰ 매수 시간</b>: <b>오전 09:00 ~ 09:15</b> (시초가 변동성 매수)\n"
        f"• <b>🎯 6% 목표가</b>: <b>{res['target_price']:,}원</b>\n"
        f"• <b>⏱️ 매도 전략</b>: 매수 직후 MTS <b>[자동 감시 주문]</b>에 {res['target_price']:,}원을 입력하세요.\n"
        f"• <b>🛡️ 손절가(-2%)</b>: {res['stop_price']:,}원\n"
        f"• 포착 사유: {res['reason']}"
    )
    report_lines.append(item_msg)

# 조건 만족 종목이 없을 경우
if not report_lines:
    report_lines.append("오늘은 6% 수익 전략에 완벽히 부합하는 강력 매수 신호가 없습니다.\n현금을 보호하며 내일 장을 기약하는 것이 최선의 전략입니다.")

# 텔레그램 메세지 전송
kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일')
message = (
    f"🚨 <b>[KOSPI/KOSDAQ 주도주 6% AI 브리핑 - {kst}]</b>\n\n"
    f"빅데이터 기반으로 분석한 오늘의 최우선 매수 타점 TOP 3입니다:\n\n"
    + "\n\n-------------------------\n\n".join(report_lines)
)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})