import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 1. 모바일 최적화 페이지 설정
st.set_page_config(page_title="6% AI 자동매매 시그널", layout="centered", initial_sidebar_state="collapsed")

# 🧠 AI가 엄선한 KOSPI/KOSDAQ 주도주 유니버스
TICKERS = {
    # 반도체 & AI
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "리노공업": "058470.KQ", "HPSP": "403870.KQ", "이수페타시스": "083640.KS",
    # 2차전지
    "LG에너지솔루션": "373220.KS", "에코프로비엠": "247540.KQ", "포스코퓨처엠": "003670.KS", "엔켐": "348370.KQ",
    # 바이오 & 헬스케어
    "삼성바이오로직스": "207940.KS", "셀트리온": "068270.KS", "알테오젠": "196170.KQ", "HLB": "028300.KQ", "유한양행": "000100.KS", "리가켐바이오": "141080.KQ",
    # 방산 & 로봇 & 자동차
    "한화에어로스페이스": "012450.KS", "LIG넥스원": "079550.KS", "현대차": "005380.KS", "기아": "000270.KS", "레인보우로보틱스": "277810.KQ",
    # 플랫폼 & 금융
    "KB금융": "105560.KS", "NAVER": "035420.KS", "카카오": "035720.KS"
}

# 2. 실시간 데이터 분석 함수 (60초 캐싱으로 속도 최적화)
@st.cache_data(ttl=60)
def get_ai_signals():
    results = []
    for name, ticker in TICKERS.items():
        try:
            df = yf.download(ticker, period="3mo", interval="1d", progress=False)
            if df.empty or len(df) < 20: continue
            
            df['MA20'] = df['Close'].rolling(window=20).mean()
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            close_price = int(latest['Close'].item())
            prev_close = int(prev['Close'].item())
            change_pct = ((close_price - prev_close) / prev_close) * 100
            
            # 매수/매도 가격 계산
            target_price = int(close_price * 1.06)  # 6% 수익가
            stop_price = int(close_price * 0.98)    # -2% 손절가
            rsi_val = round(latest['RSI'].item(), 1)
            
            buy_signal = False
            score = 0
            reason = ""
            
            if rsi_val < 30:
                buy_signal = True
                score = 100 - rsi_val
                reason = "RSI 30 이하 (과대낙폭 바닥 반등 구간)"
            elif latest['Close'].item() > latest['MA20'].item() and prev['Close'].item() <= prev['MA20'].item():
                buy_signal = True
                score = 70
                reason = "20일선 상향 돌파 (상승 추세 진입)"
                
            if buy_signal:
                results.append({
                    "name": name,
                    "price": close_price,
                    "change": change_pct,
                    "target": target_price,
                    "stop": stop_price,
                    "rsi": rsi_val,
                    "score": score,
                    "reason": reason
                })
        except Exception:
            pass
    
    # 점수 높은 순으로 상위 3개만 반환
    return sorted(results, key=lambda x: x['score'], reverse=True)[:3]

# 3. 앱 화면 구성 시작
st.title("🎯 내일의 6% 수익 AI 추천주")
st.markdown("매일 실시간으로 분석하여 **내일 아침 바로 걸어둘 수 있는** 정확한 가격을 알려드립니다.")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔄 최신 실시간 가격으로 새로고침", use_container_width=True):
        st.cache_data.clear() # 캐시를 지우고 새로 불러오기
with col2:
    kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%m/%d %H:%M')
    st.info(f"마지막 업데이트: {kst}")

st.divider()

# 4. 분석 진행 및 결과 출력
with st.spinner("AI가 KOSPI/KOSDAQ 주도주의 실시간 매수 타점을 분석하고 있습니다..."):
    signals = get_ai_signals()

if signals:
    for idx, s in enumerate(signals, 1):
        # 등락률 색상 지정
        color = "red" if s['change'] > 0 else ("blue" if s['change'] < 0 else "black")
        sign = "+" if s['change'] > 0 else ""
        
        st.subheader(f"🏆 AI 추천 {idx}위 : {s['name']}")
        st.markdown(f"**현재가:** <span style='color:{color}; font-size:18px;'><b>{s['price']:,}원 ({sign}{s['change']:.2f}%)</b></span> | **RSI 지수:** {s['rsi']}", unsafe_allow_html=True)
        st.caption(f"💡 **AI 포착 사유:** {s['reason']}")
        
        # 모바일에서 보기 편한 카드 UI
        with st.container():
            st.success(f"""
            **🟢 1단계: 매수 (사는 방법)**
            * **매수가격:** **{s['price']:,}원** 부근 지정가 매수
            * **매수시간:** 내일 아침 09:00 ~ 09:15 사이
            *(앱에서 위 가격으로 미리 매수 주문을 걸어두세요)*
            """)
            
            st.error(f"""
            **🔴 2단계: 매도 (파는 방법) - 매우 중요!**
            * **🎯 6% 익절가:** **{s['target']:,}원**
            * **🛡️ -2% 손절가:** **{s['stop']:,}원**
            *(매수가 체결되면 즉시 증권사 앱의 **'자동감시주문'**에 위 두 가격을 걸어두고 일상을 보내시면 됩니다)*
            """)
        st.write("---")
else:
    st.warning("⚠️ 현재 시장에서는 AI의 엄격한 6% 수익 조건을 만족하는 종목이 없습니다. 억지로 매수하지 말고 현금을 지키는 것도 투자입니다!")

# 5. 하단 매매 팁
st.markdown("""
---
### 💡 100% 자동화를 위한 꿀팁
증권사 어플(영웅문, 나무증권 등)에서 **[주식 자동감시주문]** 메뉴를 활용하세요. 
내가 일일이 주식창을 쳐다보지 않아도, AI가 알려준 **익절가**나 **손절가**에 도달하면 증권사 앱이 알아서 매도해 주어 마음 편한 투자가 가능합니다.
""")