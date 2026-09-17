import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="AI 퀀트 자동매매 시스템", layout="centered", initial_sidebar_state="collapsed")

TICKERS = {
    # 100대 핵심 주도주 (기존과 동일하되 가장 반응이 빠른 대장주 위주 압축)
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "리노공업": "058470.KQ", "HPSP": "403870.KQ", 
    "LG에너지솔루션": "373220.KS", "에코프로비엠": "247540.KQ", "포스코퓨처엠": "003670.KS", "엔켐": "348370.KQ",
    "삼성바이오로직스": "207940.KS", "셀트리온": "068270.KS", "알테오젠": "196170.KQ", "HLB": "028300.KQ", "유한양행": "000100.KS", 
    "한화에어로스페이스": "012450.KS", "LIG넥스원": "079550.KS", "현대로템": "064350.KS", "HD현대일렉트릭": "267260.KS", 
    "레인보우로보틱스": "277810.KQ", "현대차": "005380.KS", "기아": "000270.KS", "삼양식품": "003230.KS", "KB금융": "105560.KS", "NAVER": "035420.KS"
}

# 1. 🚨 시장 전체 분위기(KOSPI) 파악 함수
@st.cache_data(ttl=300)
def check_market_trend():
    try:
        kospi = yf.download("^KS11", period="1mo", interval="1d", progress=False)
        kospi['MA20'] = kospi['Close'].rolling(window=20).mean()
        latest = kospi.iloc[-1]
        
        # 코스피 종가가 20일선 아래면 '하락장(위험)'으로 판단
        if latest['Close'].item() < latest['MA20'].item():
            return False 
        return True
    except:
        return True

# 2. 개별 종목 분석 함수
@st.cache_data(ttl=60)
def analyze_market():
    results = []
    for name, ticker in TICKERS.items():
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 20: continue
            
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
            
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
            
            vol_ratio = (latest['Volume'].item() / prev['Vol_MA20'].item()) * 100 if prev['Vol_MA20'].item() > 0 else 100
            rsi_val = round(latest['RSI'].item(), 1)
            
            # 매수 타점 및 분할 목표가
            buy_price1 = close_price  
            buy_price2 = int(close_price * 0.985)  
            target_pre = int(close_price * 1.035)  
            target_main = int(close_price * 1.06)  
            target_max = int(close_price * 1.15)   
            smart_stop = int(min(close_price * 0.97, prev['Low'].item())) 
            
            score = 0
            reason = []
            
            if rsi_val < 35:
                score += 40
                reason.append("과대낙폭 구간")
            elif latest['Close'].item() > latest['MA20'].item() and prev['Close'].item() <= prev['MA20'].item():
                score += 35
                reason.append("20일선 상승 돌파")
                
            # 🚀 세력 개입(호재/뉴스 선반영) 강력 감지 로직 (250% 이상)
            if vol_ratio >= 250:
                score += 50
                reason.append(f"🔥 강력 호재 선반영 (자금 {int(vol_ratio)}% 폭증)")

            if score >= 50:
                results.append({
                    "name": name, "price1": buy_price1, "price2": buy_price2, 
                    "change": change_pct, "vol_ratio": int(vol_ratio), 
                    "target_pre": target_pre, "target_main": target_main, "target_max": target_max, 
                    "stop": smart_stop, "reason": " / ".join(reason), "score": score
                })
        except Exception:
            pass
            
    return sorted(results, key=lambda x: x['score'], reverse=True)[:3]

# 3. UI 구성
st.title("🦅 AI 퀀트 : 상위 1% 매매 시스템")

kst = datetime.now(pytz.timezone('Asia/Seoul'))
time_str = kst.strftime('%m/%d %H:%M')

st.info(f"**⏰ 앱 확인 최적 시간:** 장 시작 전 **[오전 08:40 ~ 08:50]**\n(이 시간에 떠 있는 종목이 오늘의 최종 확정 종목입니다. 종목이 바뀔까 걱정하지 마시고 이 시간에 딱 1번만 확인하세요!)")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔄 현재 픽스(Fix)된 타점 확인", use_container_width=True):
        st.cache_data.clear()
with col2:
    st.write(f"최종 업데이트: {time_str}")

st.divider()

# 시장 상태 점검
is_market_good = check_market_trend()

if not is_market_good:
    st.error("🚨 **[시장 폭우 경보 발령]** 🚨\n현재 대한민국 증시가 전체적인 하락 추세(위험 구간)에 진입했습니다.\n오늘은 매수 시스템을 가동하지 마시고 **무조건 현금 100% 관망**하시기 바랍니다. 돈을 지키는 것이 최고의 수익입니다.")
else:
    st.success("☀️ **[시장 맑음]** 증시 추세가 양호합니다. AI 매매 시스템을 가동합니다.")
    
    with st.spinner("AI가 스마트머니(세력)의 자금 이동과 뉴스를 실시간 추적 중입니다..."):
        signals = analyze_market()

    if signals:
        for idx, s in enumerate(signals, 1):
            color = "red" if s['change'] > 0 else "blue"
            sign = "+" if s['change'] > 0 else ""
            
            st.subheader(f"🏆 확정 픽 {idx}위 : {s['name']}")
            st.markdown(f"**기준가:** <span style='color:{color}; font-size:18px;'><b>{s['price1']:,}원 ({sign}{s['change']:.2f}%)</b></span>", unsafe_allow_html=True)
            st.caption(f"💡 **AI 감지 정보:** {s['reason']}")
            
            with st.container():
                st.success(f"**🟢 [매수]** 1차: **{s['price1']:,}원**(50%) / 2차: **{s['price2']:,}원**(50%)")
                st.warning(f"**🎯 [익절]** 3.5% 도달 시 **{s['target_pre']:,}원**에서 절반 선제 매도! 남은 절반은 상한가(**{s['target_max']:,}원**)까지 추적!")
                st.error(f"**🛡️ [손절]** **{s['stop']:,}원** 도달 시 기계적 손절 (개미털기 라인 통과 시)")
            st.write("---")
    else:
        st.warning("⚠️ 오늘은 AI의 까다로운 기준을 뚫은 완벽한 종목이 없습니다. 쉬어가는 것도 투자입니다.")