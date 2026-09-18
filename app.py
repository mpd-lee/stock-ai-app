import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime

# ==========================================
# ⚙️ 웹 브라우저 전체 화면 설정
# ==========================================
st.set_page_config(page_title="AI 퀀트 스나이퍼", page_icon="🦅", layout="centered")

# ==========================================
# 🎯 주도주 유니버스 설정
# ==========================================
TICKERS = {
    "005930": "삼성전자", "000660": "SK하이닉스", "042700": "한미반도체", "058470": "리노공업",
    "373220": "LG에너지솔루션", "003670": "포스코퓨처엠", "247540": "에코프로비엠", "207940": "삼성바이오로직스",
    "068270": "셀트리온", "196170": "알테오젠", "028300": "HLB", "012450": "한화에어로스페이스",
    "079550": "LIG넥스원", "064350": "현대로템", "267260": "HD현대일렉트릭", "277810": "레인보우로보틱스",
    "003230": "삼양식품", "035420": "NAVER"
}

# 🇰🇷 한국 시간대 설정
KST = datetime.timezone(datetime.timedelta(hours=9))

# ==========================================
# 📡 실시간 데이터 크롤링 함수 (장외 방어 로직 추가)
# ==========================================
def get_realtime_naver_finance(code):
    url = f"https://finance.naver.com/item/sise.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        now_tag = soup.select_one('#_nowVal')
        rate_tag = soup.select_one('#_rate')
        quant_tag = soup.select_one('#_quant')
        
        # 장이 닫혀있어 태그가 없거나 값이 비어있는 경우 방어
        if not now_tag or not rate_tag or not quant_tag:
            return None
            
        now_val = now_tag.text.replace(',', '').strip()
        rate_val = rate_tag.text.replace('%', '').strip()
        quant_val = quant_tag.text.replace(',', '').strip()
        
        if not now_val or not rate_val or not quant_val:
            return None
            
        return {"price": int(now_val), "rate": float(rate_val), "volume": int(quant_val)}
    except Exception:
        return None

# ==========================================
# 🖥️ 웹 UI 화면 그리기
# ==========================================
st.title("🦅 AI 퀀트 : 상위 1% 매매 시스템")
st.markdown("안정적인 아침 픽과 실시간 돌발 호재를 완벽히 분리했습니다.")

tab1, tab2 = st.tabs(["🌅 실시간 주도주 TOP 5", "⚡ 장중 긴급 레이더 (준비중)"])

with tab1:
    st.info("⏰ 8시 45분 단일 종목의 위험성을 없앴습니다. 버튼을 누르면 현재 돈이 가장 많이 몰리는 실시간 TOP 5를 즉시 스캔합니다.")
    
    if st.button("🔄 실시간 TOP 5 스캔 (0초 지연)", use_container_width=True):
        
        with st.spinner("네이버 금융 실시간 호가창 데이터를 분석 중입니다..."):
            results = []
            for code, name in TICKERS.items():
                data = get_realtime_naver_finance(code)
                if data and data["price"] > 0:
                    score = data["rate"] * (data["volume"] / 10000)
                    results.append({
                        "code": code, "name": name, 
                        "price": data["price"], "rate": data["rate"], "score": score
                    })
            
            # 🛑 장외 시간이라 데이터를 못 가져온 경우를 위한 안전 장치 (더미 시뮬레이션 데이터 제공)
            if not results:
                st.warning("⚠️ 현재 주식 시장이 닫혀 있어 실시간 호가 데이터를 가져올 수 없습니다. 아래는 시스템 테스트용 예시 화면입니다.")
                # 테스트용 가상 데이터 생성
                results = [
                    {"code": "005930", "name": "삼성전자", "price": 72000, "rate": 1.5, "score": 150},
                    {"code": "000660", "name": "SK하이닉스", "price": 175000, "rate": 3.2, "score": 320},
                    {"code": "042700", "name": "한미반도체", "price": 110000, "rate": 4.1, "score": 410},
                    {"code": "247540", "name": "에코프로비엠", "price": 180000, "rate": -0.5, "score": 50},
                    {"code": "267260", "name": "HD현대일렉트릭", "price": 310000, "rate": 5.0, "score": 500}
                ]
            
            results.sort(key=lambda x: x["score"], reverse=True)
            top5 = results[:5]
            
            now_time = datetime.datetime.now(KST).strftime('%H시 %M분 %S초')
            st.success(f"✅ 분석 완료! (기준 시간: {now_time})")
            
            for idx, item in enumerate(top5, 1):
                price = item['price']
                target = int(price * 1.05) 
                stop = int(price * 0.97)   
                
                st.markdown(f"### {idx}위. {item['name']} ({item['rate']:+.2f}%)")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("💸 현재가(매수가)", f"{price:,}원")
                col2.metric("🎯 익절가(+5%)", f"{target:,}원")
                col3.metric("🛑 손절가(-3%)", f"{stop:,}원")
                
                st.link_button(f"📈 {item['name']} 차트/호가창 바로가기", f"https://m.stock.naver.com/item/main.nhn?code={item['code']}")
                st.divider()
                
            st.info("💡 위 가격을 신한증권 '자동감시주문'에 그대로 입력해두시면 마음 편히 일상을 즐기실 수 있습니다!")
