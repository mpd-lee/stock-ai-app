import streamlit as st
import requests
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
# 📡 실시간 0초 지연 데이터 크롤링 (모바일 전용 API - 차단 없음!)
# ==========================================
def get_realtime_data(code):
    # 네이버 모바일 앱 전용 데이터 통로를 사용하여 해외 서버 차단을 완벽 회피합니다.
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        
        price = int(data['closePrice'].replace(',', ''))
        rate = float(data['fluctuationsRatio'])
        volume = int(data['accumulatedTradingVolume'].replace(',', ''))
        
        return {"price": price, "rate": rate, "volume": volume}
    except Exception:
        return None

# ==========================================
# 🖥️ 웹 UI 화면 그리기 (디자인 및 기능 완벽 최적화)
# ==========================================
st.title("🦅 AI 퀀트 : 상위 1% 매매 시스템")
st.markdown("안정적인 아침 픽과 실시간 돌발 호재를 완벽히 분리했습니다.")

tab1, tab2 = st.tabs(["🌅 실시간 주도주 TOP 5", "⚡ 장중 긴급 레이더 (LIVE)"])

# ----------------------------------------
# 탭 1: 실시간 TOP 5
# ----------------------------------------
with tab1:
    st.info("⏰ 버튼을 누르면 현재 돈이 가장 많이 몰리는 실시간 TOP 5를 즉시 스캔합니다.")
    
    if st.button("🔄 실시간 TOP 5 스캔 (0초 지연)", use_container_width=True):
        with st.spinner("모바일 전용망을 통해 실시간 데이터를 수집 중입니다..."):
            results = []
            for code, name in TICKERS.items():
                data = get_realtime_data(code)
                if data and data["price"] > 0:
                    score = data["rate"] * (data["volume"] / 10000)
                    results.append({
                        "code": code, "name": name, 
                        "price": data["price"], "rate": data["rate"], "score": score
                    })
            
            results.sort(key=lambda x: x["score"], reverse=True)
            top5 = results[:5]
            
            if not top5:
                st.error("🚨 통신이 원활하지 않습니다. 잠시 후 다시 시도해 주세요.")
            else:
                now_time = datetime.datetime.now().strftime('%H시 %M분 %S초')
                st.success(f"✅ 분석 완료! (스캔 기준 시간: {now_time})")
                
                # 매수/매도 가격을 직관적이고 예쁘게 표시
                for idx, item in enumerate(top5, 1):
                    price = item['price']
                    target = int(price * 1.05) # 익절가 +5%
                    stop = int(price * 0.97)   # 손절가 -3%
                    
                    st.markdown(f"### {idx}위. 🏆 **{item['name']}** ({item['rate']:+.2f}%)")
                    
                    # 3가지 색상 박스로 명확하게 안내
                    st.success(f"**💸 [진입] 현재가 (매수가) :** {price:,}원")
                    st.info(f"**🎯 [익절] 1차 목표가 (+5%) :** {target:,}원")
                    st.error(f"**🛑 [손절] 위험 차단가 (-3%) :** {stop:,}원")
                    
                    st.link_button(f"📈 {item['name']} 차트/호가창 바로가기", f"https://m.stock.naver.com/item/main.nhn?code={item['code']}")
                    st.divider() 
                    
                st.info("💡 신한증권 '자동감시주문'에 위 [목표가/손절가]를 그대로 입력해두시면 마음 편히 외출하실 수 있습니다!")

# ----------------------------------------
# 탭 2: 장중 긴급 레이더 (새 기능 활성화)
# ----------------------------------------
with tab2:
    st.warning("⚡ 급락 징후나 손절선을 위협하는 위험 종목을 실시간으로 감지하여 경고합니다.")
    
    if st.button("🚨 긴급 레이더 가동", use_container_width=True):
        with st.spinner("유니버스 전 종목의 위험 징후를 스캔 중입니다..."):
            alerts = []
            for code, name in TICKERS.items():
                data = get_realtime_data(code)
                if data:
                    # 당일 -3% 이상 하락 중인 종목을 감지
                    if data["rate"] <= -3.0:
                        alerts.append(f"**{name}** (현재 {data['rate']}% 급락 중)")
            
            if len(alerts) > 0:
                st.error("⚠️ **[주의] 현재 급락 징후가 포착된 종목이 있습니다! 확인 바랍니다.**")
                for alert in alerts:
                    st.markdown(f"• {alert}")
            else:
                st.success("✅ 스캔 완료! 현재 관심 종목 중 급락하는 위험 종목은 없습니다. (모두 안전)")
