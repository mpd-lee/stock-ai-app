import streamlit as st
import yfinance as yf
import requests
import datetime

# ==========================================
# ⚙️ 텔레그램 봇 세팅
# ==========================================
TELEGRAM_TOKEN = "8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
TELEGRAM_CHAT_ID = "8796285923"

def send_telegram_msg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except:
        pass

# ==========================================
# ⚙️ 웹 브라우저 설정
# ==========================================
st.set_page_config(page_title="AI 퀀트 스나이퍼", page_icon="🦅", layout="centered")

# ==========================================
# 🎯 주도주 유니버스
# ==========================================
TICKERS = {
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "042700.KS": "한미반도체", "058470.KQ": "리노공업",
    "373220.KS": "LG에너지솔루션", "003670.KS": "포스코퓨처엠", "247540.KQ": "에코프로비엠", "207940.KS": "삼성바이오로직스",
    "068270.KS": "셀트리온", "196170.KQ": "알테오젠", "028300.KQ": "HLB", "012450.KS": "한화에어로스페이스",
    "079550.KS": "LIG넥스원", "064350.KS": "현대로템", "267260.KS": "HD현대일렉트릭", "277810.KQ": "레인보우로보틱스",
    "003230.KS": "삼양식품", "035420.KS": "NAVER"
}

# ==========================================
# 📡 글로벌 금융망 데이터 크롤링 (차단 방지)
# ==========================================
def get_realtime_data(ticker_code):
    try:
        tk = yf.Ticker(ticker_code)
        info = tk.fast_info
        price = info['last_price']
        prev_close = info['previous_close']
        volume = info['last_volume']
        
        if prev_close and prev_close > 0:
            rate = ((price - prev_close) / prev_close) * 100
        else:
            rate = 0.0
            
        return {"price": int(price), "rate": rate, "volume": int(volume)}
    except Exception:
        return None

# ==========================================
# 🖥️ 텔레그램 + 웹 UI 완벽 통합 화면
# ==========================================
st.title("🦅 AI 퀀트 : 상위 1% 매매 시스템")
st.markdown("텔레그램 알림 시스템과 실시간 웹 어플리케이션을 하나로 통합했습니다.")

tab1, tab2 = st.tabs(["🌅 실시간 주도주 TOP 5", "🚨 장중 긴급 레이더 (LIVE)"])

# ----------------------------------------
# 탭 1: 실시간 TOP 5
# ----------------------------------------
with tab1:
    st.info("⏰ 버튼을 누르면 실시간 데이터를 분석하고, **동시에 텔레그램으로도 추천 브리핑을 전송**합니다.")
    
    if st.button("🔄 TOP 5 스캔 및 텔레그램 전송", use_container_width=True):
        with st.spinner("데이터를 분석 중입니다..."):
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
                st.error("🚨 데이터를 불러오지 못했습니다. 장이 열려있는지 확인해 주세요.")
            else:
                now_time = datetime.datetime.now().strftime('%H시 %M분')
                st.success(f"✅ 분석 완료! (기준 시간: {now_time}) - 텔레그램 봇으로도 전송되었습니다.")
                
                tg_msg = f"🦅 <b>AI 퀀트 주도주 TOP 5 스캔</b> ({now_time})\n"
                tg_msg += "──────────────────\n\n"
                
                for idx, item in enumerate(top5, 1):
                    price = item['price']
                    target = int(price * 1.05) 
                    stop = int(price * 0.97)   
                    code_num = item['code'].split('.')[0]
                    
                    st.markdown(f"### {idx}위. 🏆 **{item['name']}** ({item['rate']:+.2f}%)")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("💸 현재가(매수가)", f"{price:,}원")
                    col2.metric("🎯 익절가(+5%)", f"{target:,}원")
                    col3.metric("🛑 손절가(-3%)", f"{stop:,}원")
                    
                    st.link_button(f"📈 {item['name']} 차트/호가창 열기", f"https://m.stock.naver.com/item/main.nhn?code={code_num}")
                    st.divider() 
                    
                    tg_msg += f"{idx}위. <b>{item['name']}</b> ({item['rate']:+.2f}%)\n"
                    tg_msg += f" 💸 매수가: {price:,}원\n"
                    tg_msg += f" 🎯 익절가: {target:,}원 (+5%)\n"
                    tg_msg += f" 🛑 손절가: {stop:,}원 (-3%)\n\n"
                
                st.info("💡 신한증권 '자동감시주문'에 위 [목표가/손절가]를 그대로 입력해두시면 마음 편히 외출하실 수 있습니다!")
                tg_msg += "💡 위 가격을 신한증권 '자동감시주문'에 세팅해 두세요!"
                send_telegram_msg(tg_msg)

# ----------------------------------------
# 탭 2: 장중 긴급 레이더 (근영님 아이디어 적용!)
# ----------------------------------------
with tab2:
    st.warning("⚡ 급락 징후(-3% 이상)를 실시간 감지하여 웹과 텔레그램으로 즉시 경고합니다.")
    
    if st.button("🚨 긴급 레이더 가동 및 알림", use_container_width=True):
        with st.spinner("유니버스 전 종목의 위험 징후를 스캔 중입니다..."):
            alerts_data = []
            for code, name in TICKERS.items():
                data = get_realtime_data(code)
                if data and data["rate"] <= -3.0: 
                    alerts_data.append({
                        "code": code, "name": name, 
                        "price": data["price"], "rate": data["rate"]
                    })
            
            if len(alerts_data) > 0:
                st.error(f"⚠️ **[주의] 현재 급락 징후가 포착된 {len(alerts_data)}개 종목이 있습니다!**")
                
                tg_alert_msg = "🚨 <b>[긴급 탈출 경보]</b> 🚨\n\n"
                
                for item in alerts_data:
                    name = item['name']
                    rate = item['rate']
                    price = item['price']
                    code_num = item['code'].split('.')[0]
                    
                    # 1. 웹 화면 출력 (글씨 깨짐 수정 & 버튼 추가)
                    st.markdown(f"### ⚠️ **{name}** ({rate:+.2f}% 급락 중)")
                    st.write(f"💸 **현재가:** {price:,}원")
                    # 호가창 즉시 이동 버튼 추가
                    st.link_button(f"📉 {name} 차트/호가창 즉시 확인 (대응하기)", f"https://m.stock.naver.com/item/main.nhn?code={code_num}")
                    st.divider()
                    
                    # 2. 텔레그램 메시지 조립
                    tg_alert_msg += f"• <b>{name}</b> (현재 {rate:+.2f}% 급락)\n"
                
                tg_alert_msg += "\n손절선을 위협하고 있습니다. 즉시 HTS/MTS를 확인 바랍니다."
                send_telegram_msg(tg_alert_msg)
                
                st.success("📲 텔레그램으로도 긴급 경보를 발송했습니다. 스마트폰 알림을 확인하세요.")
            else:
                st.success("✅ 스캔 완료! 현재 급락하는 위험 종목은 없습니다. (모두 안전)")
