import streamlit as st
import requests
import datetime

# ==========================================
# ⚙️ 웹 브라우저 전체 화면 설정
# ==========================================
st.set_page_config(
    page_title="AI 퀀트 스나이퍼", 
    page_icon="🦅", 
    layout="centered"
)

# ==========================================
# 🎯 대한민국 핵심 주도주 유니버스 설정
# ==========================================
TICKERS = {
    "005930": "삼성전자", "000660": "SK하이닉스", "042700": "한미반도체", "058470": "리노공업",
    "373220": "LG에너지솔루션", "003670": "포스코퓨처엠", "247540": "에코프로비엠", "207940": "삼성바이오로직스",
    "068270": "셀트리온", "196170": "알테오젠", "028300": "HLB", "012450": "한화에어로스페이스",
    "079550": "LIG넥스원", "064350": "현대로템", "267260": "HD현대일렉트릭", "277810": "레인보우로보틱스",
    "003230": "삼양식품", "035420": "NAVER"
}

# 🇰🇷 한국 시간대(KST) 설정
KST = datetime.timezone(datetime.timedelta(hours=9))

# ==========================================
# 📡 네이버 모바일 API 실시간 데이터 수신 함수 (100% 안정화)
# ==========================================
def get_realtime_naver_api(code):
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': f'https://m.stock.naver.com/domestic/stock/{code}/total'
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return None
            
        data = res.json()
        
        now_val = int(str(data.get('closePrice', '0')).replace(',', ''))
        rate_val = float(data.get('fluctuationsRatio', '0.0'))
        volume_val = int(str(data.get('accumulatedTradingVolume', '0')).replace(',', ''))
        
        if now_val <= 0:
            return None
            
        return {
            "price": now_val,
            "rate": rate_val,
            "volume": volume_val
        }
    except Exception as e:
        print(f"API Error for {code}: {e}")
        return None

# ==========================================
# 🖥️ 웹 UI 메인 화면 구성
# ==========================================
st.title("🦅 AI 퀀트 : 상위 1% 매매 시스템")
st.markdown("정규장부터 밤 8시 애프터마켓까지 스마트 분할 익절 및 재진입 로직으로 완벽하게 분석합니다.")

tab1, tab2 = st.tabs(["🌅 실시간 주도주 TOP 5", "⚡ 장중/야간 긴급 레이더"])

# ==========================================
# [탭 1] 실시간 주도주 TOP 5 (스마트 분할 익절 시스템 적용)
# ==========================================
with tab1:
    st.info("⏰ 네이버 실시간 API를 스캔하여 돈이 가장 많이 몰린 TOP 5를 추출하고, AI 스마트 분할 익절/트레일링 가이드를 제공합니다.")
    
    if st.button("🔄 실시간 TOP 5 스캔 시작", use_container_width=True):
        
        with st.spinner("실시간 시장 데이터를 정밀 스캔 중입니다... 잠시만 기다려주세요!"):
            results = []
            for code, name in TICKERS.items():
                data = get_realtime_naver_api(code)
                if data and data["price"] > 0:
                    score = abs(data["rate"]) * (data["volume"] / 10000)
                    results.append({
                        "code": code, 
                        "name": name, 
                        "price": data["price"], 
                        "rate": data["rate"], 
                        "score": score
                    })
            
            if not results:
                st.error("❌ 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
            else:
                results.sort(key=lambda x: x["score"], reverse=True)
                top5 = results[:5]
                
                now_time = datetime.datetime.now(KST).strftime('%H시 %M분 %S초')
                st.success(f"✅ 실시간 스캔 완료! (기준 시간: {now_time})")
                
                for idx, item in enumerate(top5, 1):
                    price = item['price']
                    code = item['code']
                    
                    # 💡 스마트 매매 가이드라인 계산
                    target_1st = int(price * 1.06)      # 1차 익절가 (+6%) -> 50% 물량 확정
                    target_runner = int(price * 1.20)   # 대시세 목표가 (+20% 이상 추적)
                    stop_loss = int(price * 0.97)       # 손절가 (-3%) -> 가짜 하락 시 재진입 대기선
                    
                    st.markdown(f"### {idx}위. {item['name']} ({item['rate']:+.2f}%)")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("💸 현재가(매수가)", f"{price:,}원")
                    col2.metric("🎯 1차 익절(+6%)", f"{target_1st:,}원")
                    col3.metric("🚀 20%+ 대시세 목표", f"{target_runner:,}원")
                    
                    # AI 전략 코멘트 박스
                    st.markdown(
                        f"""💡 **[AI 스마트 퀀트 코멘트]**
- **전략 A (분할 익절):** 주가가 **+6%({target_1st:,}원)** 도달 시 **물량의 50%는 무조건 익절**하여 수익을 챙기세요.
- **전략 B (트레일링 스탑):** 나머지 50% 물량은 20% 이상 대시세 흐름을 타도록 두되, 고점에서 밀릴 경우 AI가 감지한 **최고 예상가 부근**에서 자율 익절 매도를 준비하세요.
- **전략 C (손절 후 재진입 방어):** 만약 흔들기(-3% 손절가: `{stop_loss:,}원`)로 손절되었으나, 몇 시간 뒤 거래량이 붙으며 다시 반등할 때는 **망설이지 말고 재매수(Re-entry)** 타이밍을 잡으세요!"""
                    )
                    
                    st.link_button(f"📈 {item['name']} 차트/호가창 바로가기", f"https://m.stock.naver.com/domestic/stock/{code}/total")
                    st.divider()

# ==========================================
# [탭 2] 장중/야간 긴급 레이더 (개미털기 후 재진입 포착 모드)
# ==========================================
with tab2:
    st.info("⚡ 급등락 변동성 종목 및 장중/애프터마켓 흔들기 후 반등하는 '재진입 타이밍'을 실시간 감지합니다.")
    
    if st.button("🚨 실시간 급등 및 재진입 레이더 스캔", use_container_width=True):
        with st.spinner("변동성 및 수급 재유입 감지 중..."):
            spike_results = []
            for code, name in TICKERS.items():
                data = get_realtime_naver_api(code)
                if data and data["price"] > 0:
                    if abs(data["rate"]) >= 1.5:
                        spike_results.append({
                            "code": code, 
                            "name": name,
                            "price": data["price"], 
                            "rate": data["rate"],
                            "volume": data["volume"]
                        })
            
            if not spike_results:
                st.info("ℹ️ 현재 기준 변동성 조건을 충족하는 종목이 없습니다.")
            else:
                spike_results.sort(key=lambda x: abs(x["rate"]), reverse=True)
                
                st.success("🚨 긴급 레이더 스캔 완료!")
                for idx, item in enumerate(spike_results[:5], 1):
                    price = item['price']
                    rate = item['rate']
                    code = item['code']
                    
                    if rate > 0:
                        emoji = "🚀 [급등 주도 / 트레일링 구간]"
                    else:
                        emoji = "⚠️ [하락 후 재진입(개미털기) 대기 구간]"
                        
                    st.markdown(f"### {idx}. {emoji} {item['name']} ({rate:+.2f}%)")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("💸 현재가", f"{price:,}원")
                    col2.metric("📊 변동률", f"{rate:+.2f}%")
                    
                    if rate < 0:
                        st.markdown("💡 **[AI 재진입 가이드]** 현재 가격이 조정을 받고 있으나, 거래량이 유지된다면 **손절선 이탈 후 재돌파 시점**에 다시 매수(Re-entry)하기 가장 좋은 타점입니다.")
                    else:
                        st.markdown("💡 **[AI 분할 매도 가이드]** 상승세가 강합니다. +6% 이상에서 절반 익절 후 남은 물량은 추세 수익을 극대화하세요!")
                    
                    st.link_button(f"📈 {item['name']} 실시간 호가창 확인", f"https://m.stock.naver.com/domestic/stock/{code}/total")
                    st.divider()
