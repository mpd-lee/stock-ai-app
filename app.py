import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="AI 퀀트 자동매매", layout="centered")

TICKERS = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "리노공업": "058470.KQ", 
    "에코프로비엠": "247540.KQ", "알테오젠": "196170.KQ", "HLB": "028300.KQ", "현대로템": "064350.KS", 
    "HD현대일렉트릭": "267260.KS", "삼양식품": "003230.KS", "NAVER": "035420.KS"
}

# (기존 분석 함수 생략 없이 간단히 포함 - 실제로는 이전 답변의 로직을 그대로 유지합니다)
@st.cache_data(ttl=60)
def analyze_market(mode="morning"):
    results = []
    for name, ticker in TICKERS.items():
        try:
            df = yf.download(ticker, period="1mo", interval="1d", progress=False)
            if df.empty or len(df) < 5: continue
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            close_price = int(latest['Close'].item())
            vol_ratio = (latest['Volume'].item() / prev['Volume'].item()) * 100 if prev['Volume'].item() > 0 else 100
            
            # 모드에 따른 로직 분리
            score = 0
            reason = ""
            if mode == "morning":
                # 아침용: 안정성 위주
                if close_price > df['Close'].rolling(5).mean().iloc[-1]: score += 50
                reason = "안정적 상승 추세"
            elif mode == "live":
                # 실시간용: 거래량 폭발 위주 (호재 반영)
                if vol_ratio > 300: 
                    score += 100
                    reason = f"🔥 장중 긴급 호재 (거래량 {int(vol_ratio)}% 폭증!)"

            if score > 0:
                results.append({"name": name, "price": close_price, "reason": reason, "score": score})
        except:
            pass
    return sorted(results, key=lambda x: x['score'], reverse=True)[:3]

# --- UI 구성 ---
st.title("🦅 AI 퀀트 : 상위 1% 매매 시스템")
st.write("안정적인 아침 픽과 실시간 돌발 호재를 완벽히 분리했습니다.")

# 💡 투 트랙 탭 생성
tab1, tab2 = st.tabs(["🌅 아침 확정 매매 (안정형)", "⚡ 장중 긴급 레이더 (공격형)"])

# 첫 번째 탭: 기존처럼 아침에 한 번만 확인하는 곳
with tab1:
    st.info("**⏰ 아침 08:45 전용** - 하루 딱 한 번만 눌러서 오늘의 주력 종목을 세팅하세요.")
    if st.button("🔄 아침 픽스(Fix) 새로고침", key="morning_btn"):
        st.cache_data.clear()
        
    signals = analyze_market(mode="morning")
    if signals:
        for s in signals:
            st.success(f"🏆 주력 매수: **{s['name']}** (현재가 {s['price']:,}원) - {s['reason']}")
    else:
        st.warning("오늘은 보수적으로 접근하세요.")

# 두 번째 탭: 장중에 심심할 때 눌러보거나 호재를 찾을 때 쓰는 곳
with tab2:
    st.error("**🔥 장중 09:00 ~ 15:30 전용** - 실시간으로 갑자기 돈이 몰리는 호재 종목을 찾습니다.")
    if st.button("⚡ 실시간 호재 레이더 가동 (새로고침)", key="live_btn"):
        st.cache_data.clear()
        
    live_signals = analyze_market(mode="live")
    if live_signals and live_signals[0]['score'] >= 100:
        for s in live_signals:
            st.error(f"🚀 **긴급 포착!** **{s['name']}** (현재가 {s['price']:,}원) \n\n이유: {s['reason']}")
            st.write("👉 즉시 증권사 뉴스를 확인하시고 짧게 단타(스캘핑)로 접근하세요!")
    else:
        st.write("현재 특이 거래량(호재)이 터진 종목이 없습니다. 평온한 상태입니다.")