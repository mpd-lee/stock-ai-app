import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# 1. 페이지 기본 설정
st.set_page_config(page_title="주식 AI 대시보드", layout="wide")

# 2. 사이드바 설정 (토큰 및 채팅 ID 자동 입력)
st.sidebar.title("⚙️ 시스템 및 알림 설정")

bot_token = st.sidebar.text_input("봇 토큰 (Bot Token)", value="8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g")
chat_id = st.sidebar.text_input("채팅 ID (Chat ID)", value="8796285923")
min_score = st.sidebar.slider("최소 AI 점수 필터", min_value=0, max_value=100, value=50)

def send_telegram_msg(token, cid, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": cid, "text": message, "parse_mode": "HTML"}
    return requests.post(url, data=payload)

# 3. 실시간 주가 및 지표 계산 함수 (접속할 때마다 실행)
@st.cache_data(ttl=60) # 60초 동안은 데이터 캐싱(속도 최적화)
def fetch_realtime_data():
    tickers = {
        "삼성전자": "005930.KS",
        "SK하이닉스": "000660.KS",
        "KB금융": "105560.KS",
        "한화에어로스페이스": "012450.KS",
        "LG에너지솔루션": "373220.KS"
    }
    
    data_list = []
    for name, ticker in tickers.items():
        try:
            # 실시간 주가 및 과거 데이터 다운로드
            df = yf.download(ticker, period="3mo", interval="1d", progress=False)
            if df.empty:
                continue
            
            # 현재가 및 등락률 계산
            close_price = int(df['Close'].iloc[-1].item())
            prev_close = int(df['Close'].iloc[-2].item())
            change_rate = ((close_price - prev_close) / prev_close) * 100
            
            # RSI 계산
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = round(rsi.iloc[-1].item(), 1)
            
            # 6% 목표가 및 -2% 손절가 계산
            target_price = int(close_price * 1.06)
            stop_price = int(close_price * 0.98)
            
            # AI 점수 및 신호 로직 (RSI가 30 이하일 때 100점)
            ai_score = 100 if current_rsi < 30 else (80 if current_rsi < 50 else 50)
            signal = "🔥 강력추천" if ai_score >= 90 else "👀 관망/관심"

            data_list.append({
                "종목명": name,
                "현재가": f"{close_price:,}원",
                "등락률": f"{change_rate:+.2f}%",
                "RSI": current_rsi,
                "6% 목표가": f"{target_price:,}원",
                "손절가(-2%)": f"{stop_price:,}원",
                "AI 점수": ai_score,
                "매수 신호": signal
            })
        except Exception:
            pass
    return pd.DataFrame(data_list)

# 4. 메인 화면 출력
st.title("📊 주식 6% AI 자동탐색 & 실시간 알림 시스템")

tab1, tab2 = st.tabs(["🔥 실시간 스캔 & 트레이딩", "📈 AI 전략 승률 백테스팅"])

with tab1:
    st.subheader("🔥 실시간 승률 TOP 5 AI 추천 종목")
    st.caption("🔄 앱을 열거나 새로고침할 때마다 최신 실시간 주가와 RSI를 자동으로 분석해 가져옵니다.")
    
    # 실시간 데이터 불러오기
    with st.spinner('실시간 주식 데이터를 분석 중입니다... 잠시만 기다려주세요.'):
        df = fetch_realtime_data()
    
    if not df.empty:
        filtered_df = df[df["AI 점수"] >= min_score]
        st.dataframe(filtered_df, use_container_width=True)
        
        if st.sidebar.button("🔔 텔레그램으로 추천 종목 전송"):
            if bot_token and chat_id:
                top_items = filtered_df[filtered_df["AI 점수"] >= 90]["종목명"].tolist()
                if top_items:
                    msg_text = f"📢 <b>[AI 주식 실시간 추천 알림]</b>\n\n강력 추천 매수 종목: {', '.join(top_items)}\n\n앱에서 실시간 6% 목표가를 확인하세요!"
                else:
                    msg_text = "📢 현재 엄격한 AI 매수 조건(RSI 30 이하)을 만족하는 종목이 없습니다."
                
                res = send_telegram_msg(bot_token, chat_id, msg_text)
                if res.status_code == 200:
                    st.sidebar.success("텔레그램 전송 완료!")
                else:
                    st.sidebar.error("전송 실패. 오류가 발생했습니다.")
            else:
                st.sidebar.warning("봇 토큰과 채팅 ID를 입력해주세요.")
    else:
        st.error("주식 데이터를 불러오지 못했습니다. 장 마감 이후나 네트워크 상태를 확인해주세요.")

with tab2:
    st.write("📈 과거 데이터 기반 백테스팅 결과 화면입니다.")