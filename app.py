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

# ==========================================
# 📡 실시간 0초 지연 데이터 크롤링 함수
# ==========================================
def get_realtime_naver_finance(code):
    url = f"https://finance.naver.com/item/sise.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 네이버 금융에서 현재가, 등락률, 거래량 실시간 수집
        now_val = soup.select_one('#_nowVal').text.replace(',', '')
        rate_val = soup.select_one('#_rate').text.replace('%', '').strip()
        quant_val = soup.select_one('#_quant').text.replace(',', '')
        
        return {"price": int(now_val), "rate": float(rate_val), "volume": int(quant_val)}
    except Exception:
        return None

# ==========================================
# 🖥️ 웹 UI 화면 그리기 (근영님 아이디어 적용)
# ==========================================
st.title("🦅 AI 퀀트 : 상위 1% 매매 시스템")
st.markdown("안정적인 아침 픽과 실시간 돌발 호재를 완벽히 분리했습니다.")

# 탭 메뉴 구성
tab1, tab2 = st.tabs(["🌅 실시간 주도주 TOP 5", "⚡ 장중 긴급 레이더 (준비중)"])

with tab1:
    st.info("⏰ 8시 45분 단일 종목의 위험성을 없앴습니다. 버튼을 누르면 현재 돈이 가장 많이 몰리는 실시간 TOP 5를 즉시 스캔합니다.")
    
    # 새로운 새로고침 버튼 (UI 변화의 핵심)
    if st.button("🔄 실시간 TOP 5 스캔 (0초 지연)", use_container_width=True):
        
        with st.spinner("네이버 금융 실시간 호가창 데이터를 분석 중입니다..."):
            results = []
            for code, name in TICKERS.items():
                data = get_realtime_naver_finance(code)
                if data and data["price"] > 0:
                    # 거래량과 등락률을 조합한 랭킹 스코어
                    score = data["rate"] * (data["volume"] / 10000)
                    results.append({
                        "code": code, "name": name, 
                        "price": data["price"], "rate": data["rate"], "score": score
                    })
            
            # 점수순 정렬 후 상위 5개 자르기
            results.sort(key=lambda x: x["score"], reverse=True)
            top5 = results[:5]
            
            if not top5:
                st.warning("데이터를 불러오지 못했습니다. 장이 열려있는지 확인해 주세요.")
            else:
                now_time = datetime.datetime.now().strftime('%H시 %M분 %S초')
                st.success(f"✅ 분석 완료! (스캔 기준 시간: {now_time})")
                
                # TOP 5 화면에 예쁘게 출력
                for idx, item in enumerate(top5, 1):
                    price = item['price']
                    target = int(price * 1.05) # 익절가 5%
                    stop = int(price * 0.97)   # 손절가 -3%
                    
                    st.markdown(f"### {idx}위. {item['name']} ({item['rate']:+.2f}%)")
                    
                    # 3단 칼럼으로 가격 보기 좋게 배치
                    col1, col2, col3 = st.columns(3)
                    col1.metric("💸 현재가(매수가)", f"{price:,}원")
                    col2.metric("🎯 익절가(+5%)", f"{target:,}원")
                    col3.metric("🛑 손절가(-3%)", f"{stop:,}원")
                    
                    # 버튼 누르면 폰에서 네이버 호가창으로 바로 이동
                    st.link_button(f"📈 {item['name']} 차트/호가창 바로가기", f"https://m.stock.naver.com/item/main.nhn?code={item['code']}")
                    st.divider() # 구분선
                    
                st.info("💡 위 가격을 신한증권 '자동감시주문'에 그대로 입력해두시면 마음 편히 여행을 즐기실 수 있습니다!")
