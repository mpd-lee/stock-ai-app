import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

# Streamlit 페이지 설정
st.set_page_config(page_title="주식 6% AI 자동탐색 시스템", layout="wide")

st.title("📈 주식 6% AI 자동탐색 & 실시간 알림 시스템")

# 1. 사이드바 - 시스템 및 알림 설정
st.sidebar.header("⚙️ 시스템 및 알림 설정")
bot_token = st.sidebar.text_input("봇 토큰 (Bot Token)", type="password")
chat_id = st.sidebar.text_input("채팅 ID (Chat ID)")

# 2. 분석 대상 주요 종목 리스트 (확장 가능)
STOCK_DICT = {
    'SK하이닉스': '000660.KS',
    '삼성전자': '005930.KS',
    'KB금융': '105560.KS',
    'LG에너지솔루션': '373220.KS',
    '삼성바이오로직스': '207940.KS',
    '셀트리온': '068270.KS',
    '현대차': '005380.KS',
    '기아': '000270.KS',
    'NAVER': '035420.KS',
    '카카오': '035720.KS',
    'POSCO홀딩스': '005490.KS',
    '한화에어로스페이스': '012450.KS',
    '알테오젠': '196170.KQ',
    '에코프로비엠': '247540.KQ',
    '신한지주': '055550.KS'
}

# 3. 실시간 기술적 분석 및 AI 승률 점수 계산 함수
@st.cache_data(ttl=300)  # 5분 단위 캐싱으로 최신 데이터 유지
def analyze_stocks():
    results = []
    for name, ticker in STOCK_DICT.items():
        try:
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            if len(df) < 20:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df = df.xs(ticker, axis=1, level=1)

            close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            change_rate = ((close - prev_close) / prev_close) * 100

            # 이동평균선 계산
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]

            # RSI 지표 계산
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]

            # AI 승률 점수 산출 로직 (기본 50점 + 조건별 가산점)
            score = 50
            if close > ma5: score += 15       # 단기 상향 추세
            if ma5 > ma20: score += 15        # 정배열 형성
            if 40 <= rsi <= 65: score += 15    # 적정 수급 구간
            if change_rate > 0: score += 5    # 당일 우상향

            target_price = int(close * 1.06)
            stop_loss = int(close * 0.98)

            signal = "🔥 강력 추천" if score >= 80 else ("👍 관망/관심" if score >= 65 else "⏳ 대기")

            results.append({
                '종목명': name,
                '종목코드': ticker.split('.')[0],
                '현재가': f"{int(close):,}원",
                '등락률': f"{change_rate:+.2f}%",
                'RSI': round(rsi, 1),
                '6% 목표가': f"{target_price:,}원",
                '손절가(-2%)': f"{stop_loss:,}원",
                'AI 점수': score,
                '매수 신호': signal
            })
        except Exception:
            continue

    res_df = pd.DataFrame(results)
    if not res_df.empty:
        # AI 점수 내림차순 정렬
        res_df = res_df.sort_values(by='AI 점수', ascending=False)
    return res_df

# 4. 실시간 분석 실행 및 승률 TOP 5 추출
with st.spinner("실시간 시장 데이터 및 AI 승률 분석 중..."):
    df_all = analyze_stocks()

df_top5 = df_all.head(5) if not df_all.empty else pd.DataFrame()

# 5. 대시보드 화면 구성
st.subheader("🔥 실시간 승률 TOP 5 AI 추천 종목")
st.write("시장 모멘텀과 기술적 지표를 실시간 분석하여 **승률 및 매수 신호가 가장 높은 상위 5개 종목**입니다.")
st.dataframe(df_top5, use_container_width=True)

# 6. 텔레그램 알림 전송 버튼
if st.sidebar.button("🔔 TOP 5 추천 종목 텔레그램 전송"):
    if bot_token and chat_id:
        msg = f"<b>[AI 주식 승률 TOP 5 추천 리포트]</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for idx, row in df_top5.reset_index(drop=True).iterrows():
            msg += f"<b>{idx+1}. {row['종목명']}</b> ({row['AI 점수']}점 / {row['매수 신호']})\n"
            msg += f"  • 현재가: {row['현재가']} ({row['등락률']})\n"
            msg += f"  • 🎯 6% 목표가: {row['6% 목표가']}\n"
            msg += f"  • 🛑 손절가(-2%): {row['손절가(-2%)']}\n\n"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'}
        res = requests.post(url, data=payload)

        if res.status_code == 200:
            st.sidebar.success("TOP 5 추천 종목 전송 완료!")
        else:
            st.sidebar.error("전송 실패. 토큰 및 Chat ID를 확인해주세요.")
    else:
        st.sidebar.warning("봇 토큰과 채팅 ID를 입력해주세요.")
        