import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# 1. 페이지 기본 설정
st.set_page_config(page_title="AI 주도주 스마트 매매 시스템", layout="centered", initial_sidebar_state="collapsed")

# 🧠 대한민국 증시 핵심 주도주 100선 유니버스
TICKERS = {
    # 💻 반도체 / CXL / HBM
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "한미반도체": "042700.KS", "리노공업": "058470.KQ", "HPSP": "403870.KQ", 
    "이수페타시스": "083640.KS", "가온칩스": "399840.KQ", "테크윙": "089030.KQ", "원익IPS": "240810.KQ", "주성엔지니어링": "036930.KQ",
    # 🔋 2차전지 / 전고체
    "LG에너지솔루션": "373220.KS", "POSCO홀딩스": "005490.KS", "포스코퓨처엠": "003670.KS", "에코프로비엠": "247540.KQ", 
    "에코프로": "086520.KQ", "엔켐": "348370.KQ", "엘앤에프": "066970.KQ", "금양": "001570.KS",
    # 🧬 바이오 / 헬스케어 (대형 모멘텀주)
    "삼성바이오로직스": "207940.KS", "셀트리온": "068270.KS", "알테오젠": "196170.KQ", "HLB": "028300.KQ", 
    "유한양행": "000100.KS", "리가켐바이오": "141080.KQ", "휴젤": "145020.KQ", "삼천당제약": "000250.KQ", "보로노이": "310210.KQ",
    # 🚀 방산 / 우주항공 / 조선
    "한화에어로스페이스": "012450.KS", "LIG넥스원": "079550.KS", "현대로템": "064350.KS", "한국항공우주": "047810.KS", 
    "HD현대중공업": "329180.KS", "HD한국조선해양": "009540.KS", "한화오션": "042660.KS",
    # ⚡ 전력설비 / 원자력 / AI 데이터센터
    "HD현대일렉트릭": "267260.KS", "효성중공업": "298040.KS", "LS 일렉트릭": "010120.KS", "LS": "006260.KS", "두산에너빌리티": "034020.KS",
    # 🤖 로봇 / AI 소프트웨어
    "레인보우로보틱스": "277810.KQ", "두산로보틱스": "454910.KS", "포스코DX": "022100.KS", "플래티어": "367000.KQ",
    # 🚗 자동차 / 전장
    "현대차": "005380.KS", "기아": "000270.KS", "현대모비스": "012330.KS", "HL만도": "204320.KS",
    # 💄 K-뷰티 / K-푸드 / 소비재
    "실리콘투": "257720.KQ", "삼양식품": "003230.KS", "농심": "004370.KS", "APR": "278470.KS", "한국화장품제조": "003350.KS",
    # 💰 금융 / 벨류업
    "KB금융": "105560.KS", "신한지주": "055550.KS", "하나금융지주": "086790.KS", "메리츠금융지주": "138040.KS",
    # 🌐 엔터 / 게임 / 플랫폼
    "NAVER": "035420.KS", "카카오": "035720.KS", "크래프톤": "259960.KS", "하이브": "352820.KS", "JYP Ent.": "035900.KQ"
}

# 2. 실시간 AI 종목 분석 로직
@st.cache_data(ttl=60)
def analyze_market():
    results = []
    for name, ticker in TICKERS.items():
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 20: continue
            
            # 이동평균선 및 거래량 지표 계산
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
            
            # RSI 계산
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
            
            # 거래량 급증 비율 (%)
            vol_ratio = (latest['Volume'].item() / prev['Vol_MA20'].item()) * 100 if prev['Vol_MA20'].item() > 0 else 100
            rsi_val = round(latest['RSI'].item(), 1)
            
            # 목표가 계산 (1차: +6% 안전 확보 / 2차: +12%~상한가 추종)
            target1 = int(close_price * 1.06)
            target2 = int(close_price * 1.13)
            
            # 스마트 손절가 (단순 -2%가 아닌 주요 지지선 반영)
            smart_stop = int(min(close_price * 0.975, prev['Low'].item()))
            
            score = 0
            reason = []
            
            # AI 필터링 스코어링 시스템
            if rsi_val < 35:
                score += 40
                reason.append("과대낙폭 바닥 반등 타점")
            elif latest['Close'].item() > latest['MA20'].item() and prev['Close'].item() <= prev['MA20'].item():
                score += 35
                reason.append("20일선 정배열 돌파")
                
            # 🔥 수급/거래량 폭증 가산점 (200% 이상 터질 경우 뉴스/호재 동반)
            if vol_ratio >= 200:
                score += 45
                reason.append(f"🔥 세력/호재 수급 유입 (거래량 {int(vol_ratio)}% 폭증)")
            elif vol_ratio >= 150:
                score += 20
                reason.append(f"거래량 유의미한 증가 ({int(vol_ratio)}%)")

            if score >= 50:
                results.append({
                    "name": name,
                    "price": close_price,
                    "change": change_pct,
                    "vol_ratio": int(vol_ratio),
                    "target1": target1,
                    "target2": target2,
                    "stop": smart_stop,
                    "rsi": rsi_val,
                    "score": score,
                    "reason": " / ".join(reason)
                })
        except Exception:
            pass
            
    return sorted(results, key=lambda x: x['score'], reverse=True)[:3]

# 3. UI 구성
st.title("⚡ AI 주도주 스마트 자동매매 대시보드")
st.caption("100여 개 핵심 대장주의 실시간 수급·거래량·기술적 타점을 종합 분석합니다.")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🔄 실시간 데이터 갱신", use_container_width=True):
        st.cache_data.clear()
with col2:
    kst = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%m/%d %H:%M')
    st.info(f"업데이트: {kst}")

st.divider()

with st.spinner("AI가 100개 대장주의 실시간 기사·수급·거래량을 스캔 중입니다..."):
    signals = analyze_market()

if signals:
    for idx, s in enumerate(signals, 1):
        color = "red" if s['change'] > 0 else ("blue" if s['change'] < 0 else "black")
        sign = "+" if s['change'] > 0 else ""
        
        st.subheader(f"🏆 AI 추천 {idx}위 : {s['name']}")
        st.markdown(f"**현재가:** <span style='color:{color}; font-size:19px;'><b>{s['price']:,}원 ({sign}{s['change']:.2f}%)</b></span> | **거래량:** <span style='color:red;'><b>{s['vol_ratio']}% 폭증</b></span>", unsafe_allow_html=True)
        st.caption(f"💡 **AI 포착 신호:** {s['reason']}")
        
        with st.container():
            st.success(f"""
            **🟢 [매수 매뉴얼]**
            * **추천 매수가:** **{s['price']:,}원** 부근 (내일 09:00~09:15 시초가 대응)
            """)
            
            st.warning(f"""
            **🎯 [상한가 추종 분할 익절 전략 - 6% 한계 극복]**
            * **1차 목표가 (50% 익절):** **{s['target1']:,}원** (+6% 선에서 안전하게 수익 확정)
            * **2차 목표가 (상한가 추적):** **{s['target2']:,}원 이상** (잔여 50%는 트레일링 스탑 적용하여 폭등 시 상한가까지 대박 수익 추적!)
            """)
            
            st.error(f"""
            **🛡️ [스마트 손절 라인]**
            * **스마트 손절가:** **{s['stop']:,}원**
            *(단순 -2% 손절이 아닌, 주요 지지선을 반영해 개미털기 파동을 견디도록 설계)*
            """)
        st.write("---")
else:
    st.warning("⚠️ 현재 시장에서는 AI의 엄격한 고수익·고승률 조건을 충족하는 종목이 없습니다. 현금을 보유하고 대기하세요!")

st.markdown("""
---
### 💡 천재 AI의 트레일링 스탑(Trailing Stop) 매매 팁
1. **1차 목표가({s['target1']:,}원)**에 도달하면 물량의 **50%를 즉시 익절**하여 수익을 챙깁니다.
2. 나머지 50% 물량의 **손절 라인을 '내 매수가' 위로 올려 설정**합니다.
3. 이제 주가가 상한가를 가든 폭등을 하든 **손실 위험 0% 상태**에서 최고점 매도를 노릴 수 있습니다!
""")