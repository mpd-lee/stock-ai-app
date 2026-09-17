import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# 1. 페이지 기본 설정
st.set_page_config(page_title="주식 AI 대시보드", layout="wide")

# 2. 사이드바 설정 (토큰 및 채팅 ID 자동 입력 설정)
st.sidebar.title("⚙️ 시스템 및 알림 설정")

bot_token = st.sidebar.text_input(
    "봇 토큰 (Bot Token)", 
    value="8824795320:AAGnTxvxuE9HtByGoyam09DarUdyvIBuY2g"
)
chat_id = st.sidebar.text_input(
    "채팅 ID (Chat ID)", 
    value="8796285923"
)

min_score = st.sidebar.slider("최소 AI 점수 필터", min_value=0, max_value=100, value=50)

# 텔레그램 알림 전송 함수
def send_telegram_msg(token, cid, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": cid, "text": message, "parse_mode": "HTML"}
    return requests.post(url, data=payload)

# 3. 메인 화면
st.title("📊 주식 6% AI 자동탐색 & 실시간 알림 시스템")

tab1, tab2 = st.tabs(["🔥 실시간 스캔 & 트레이딩", "📈 AI 전략 승률 백테스팅"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("분석대상종목수", "10개")
    col2.metric("강력 추천(90점+) 종목", "4개")
    col3.metric("모의 포트폴리오 평균 수익률", "+0.00%")

    st.write("---")
    st.subheader("🔥 실시간 승률 TOP 5 AI 추천 종목")

    # 종목 데이터
    stocks = [
        {"종목명": "KB금융", "종목코드": "105560", "현재가": "180,200원", "등락률": "+1.81%", "RSI": 58.3, "6% 목표가": "191,012원", "손절가(-2%)": "176,596원", "AI 점수": 100, "매수 신호": "🔥 강력추천"},
        {"종목명": "한화에어로스페이스", "종목코드": "012450", "현재가": "1,094,000원", "등락률": "+3.70%", "RSI": 42.5, "6% 목표가": "1,159,640원", "손절가(-2%)": "1,072,120원", "AI 점수": 100, "매수 신호": "🔥 강력추천"},
        {"종목명": "신한지주", "종목코드": "055550", "현재가": "113,500원", "등락률": "+1.29%", "RSI": 57.0, "6% 목표가": "120,310원", "손절가(-2%)": "111,230원", "AI 점수": 100, "매수 신호": "🔥 강력추천"},
        {"종목명": "SK하이닉스", "종목코드": "000660", "현재가": "1,747,000원", "등락률": "-0.57%", "RSI": 57.2, "6% 목표가": "1,851,820원", "손절가(-2%)": "1,712,000원", "AI 점수": 95, "매수 신호": "🔥 강력추천"},
        {"종목명": "LG에너지솔루션", "종목코드": "373220", "현재가": "362,500원", "등락률": "-1.00%", "RSI": 47.6, "6% 목표가": "384,250원", "손절가(-2%)": "355,250원", "AI 점수": 75, "매수 신호": "👀 관망/관심"},
        {"종목명": "삼성전자", "종목코드": "005930", "현재가": "254,000원", "등락률": "+0.20%", "RSI": 47.6, "6% 목표가": "269,240원", "손절가(-2%)": "248,920원", "AI 점수": 55, "매수 신호": "⏳ 대기"}
    ]

    df = pd.DataFrame(stocks)
    filtered_df = df[df["AI 점수"] >= min_score]
    st.dataframe(filtered_df, use_container_width=True)

    # 알림 전송 버튼 동작
    if st.sidebar.button("🔔 텔레그램으로 추천 종목 전송"):
        if bot_token and chat_id:
            top_items = filtered_df[filtered_df["AI 점수"] >= 90]["종목명"].tolist()
            msg_text = f"📢 <b>[AI 주식 실시간 추천 알림]</b>\n\n강력 추천 종목: {', '.join(top_items)}\n\n대시보드에서 상세 목표가를 확인하세요!"
            
            res = send_telegram_msg(bot_token, chat_id, msg_text)
            if res.status_code == 200:
                st.sidebar.success("텔레그램전송 완료!")
            else:
                st.sidebar.error("전송 실패. Chat ID 및 토큰을 확인하세요.")
        else:
            st.sidebar.warning("봇 토큰과 채팅 ID를 입력해주세요.")

with tab2:
    st.write("📈 과거 데이터 기반 백테스팅 결과 화면입니다.")