import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import requests

st.set_page_config(page_title="주식6% AI Engine Master", page_icon="📈", layout="wide")

st.title("📈 주식 6% AI 자동탐색 & 텔레그램 알림 시스템")

@st.cache_data
def get_krx_list():
    df = fdr.StockListing('KRX')
    return df[['Code', 'Name', 'Market']]

try:
    krx_df = get_krx_list()
except:
    krx_df = pd.DataFrame()

default_stocks = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "삼성바이오로직스": "207940",
    "현대차": "005380",
    "기아": "000270",
    "셀트리온": "068270",
    "KB금융": "105560",
    "NAVER": "035420",
    "카카오": "035720"
}

def send_telegram(token, chat_id, message):
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except:
            pass

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

@st.cache_data
def get_stock_data(symbol):
    df = fdr.DataReader(symbol)
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['RSI'] = calculate_rsi(df)
    df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
    return df

st.sidebar.header("⚙️ 시스템 및 알림 설정")
min_score = st.sidebar.slider("최소 AI 점수 필터", 0, 100, 50, step=5)
search_input = st.sidebar.text_input("🔍 종목 직접 검색", "")

st.sidebar.subheader("📲 텔레그램 알림")
tg_token = st.sidebar.text_input("봇 토큰 (Bot Token)", type="password")
tg_chat_id = st.sidebar.text_input("채팅 ID (Chat ID)")

target_dict = default_stocks.copy()
if search_input and not krx_df.empty:
    matched = krx_df[(krx_df['Name'].str.contains(search_input, case=False, na=False)) | (krx_df['Code'].str.contains(search_input, na=False))]
    if not matched.empty:
        for _, row in matched.head(5).iterrows():
            target_dict[row['Name']] = row['Code']

tab1, tab2 = st.tabs(["📊 실시간 스캔 & 트레이딩", "🧪 AI 전략 승률 백테스팅"])

with tab1:
    results = []
    stock_prices = {}
    strong_buy_list = []

    for name, code in target_dict.items():
        try:
            df = get_stock_data(code)
            recent = df.tail(30)
            close = int(recent['Close'].iloc[-1])
            prev_close = int(recent['Close'].iloc[-2])
            rate = ((close - prev_close) / prev_close) * 100
            
            stock_prices[name] = close

            ma5 = recent['MA5'].iloc[-1]
            ma20 = recent['MA20'].iloc[-1]
            rsi = recent['RSI'].iloc[-1]
            vol_today = recent['Volume'].iloc[-1]
            vol_ma5 = recent['Vol_MA5'].iloc[-1]

            score = 40
            if close > ma5: score += 15
            if close > ma20: score += 10
            if ma5 > ma20: score += 10
            if 50 <= rsi <= 70: score += 15
            if vol_today > vol_ma5 * 1.3: score += 10

            if score >= 80:
                strong_buy_list.append(f"{name}({close:,}원 / 점수:{score}점)")

            target_6p = int(close * 1.06)
            stop_loss_2p = int(close * 0.98)

            signal = "⚪ 대기"
            if score >= 80: signal = "🔥 강력 추천"
            elif score >= 65: signal = "⚡ 관망/관심"

            if score >= min_score:
                results.append({
                    "종목명": name,
                    "종목코드": code,
                    "현재가": f"{close:,}원",
                    "등락률": f"{rate:+.2f}%",
                    "RSI": f"{rsi:.1f}",
                    "6% 목표가": f"{target_6p:,}원",
                    "손절가(-2%)": f"{stop_loss_2p:,}원",
                    "AI 점수": score,
                    "매수 신호": signal
                })
        except:
            pass

    m1, m2, m3 = st.columns(3)
    m1.metric("분석 대상 종목 수", f"{len(target_dict)}개")
    m2.metric("강력 추천(80점↑) 종목", f"{len(strong_buy_list)}개")

    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []

    total_pnl = 0.0
    if st.session_state.portfolio:
        pnls = [((stock_prices.get(i["종목명"], i["매수가"]) - i["매수가"]) / i["매수가"]) * 100 for i in st.session_state.portfolio]
        total_pnl = sum(pnls) / len(pnls)

    m3.metric("모의 포트폴리오 평균 수익률", f"{total_pnl:+.2f}%")

    if st.sidebar.button("🔔 텔레그램으로 추천 종목 전송"):
        if strong_buy_list:
            msg = "🚀 [주식 6% AI 포착 알림]\n\n" + "\n".join(strong_buy_list)
            send_telegram(tg_token, tg_chat_id, msg)
            st.sidebar.success("텔레그램 전송 완료!")
        else:
            st.sidebar.warning("현재 80점 이상 강력 추천 종목이 없습니다.")

    st.write("---")
    st.subheader("🚀 6% 급등 유망 종목 AI 순위")

    if results:
        res_df = pd.DataFrame(results).sort_values(by="AI 점수", ascending=False)
        st.dataframe(res_df, use_container_width=True, hide_index=True)
        st.download_button(label="📥 스캔 결과 CSV 다운로드", data=res_df.to_csv(index=False).encode('utf-8-sig'), file_name="AI_Stock_Scan.csv", mime="text/csv")

    st.write("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🔍 개별 종목 차트 분석")
        selected_name = st.selectbox("상세 차트 종목 선택", list(target_dict.keys()))
        selected_code = target_dict[selected_name]

        df_detail = get_stock_data(selected_code).tail(40)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_detail.index, open=df_detail['Open'], high=df_detail['High'], low=df_detail['Low'], close=df_detail['Close'], name='주가'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['MA5'], line=dict(color='orange', width=1.5), name='5일선'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['MA20'], line=dict(color='green', width=1.5), name='20일선'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_detail.index, y=df_detail['RSI'], line=dict(color='purple', width=2), name='RSI'), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="blue", row=2, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💼 모의 잔고 & KIS 주문 연동")
        curr_price = int(df_detail['Close'].iloc[-1])

        if st.button("🛒 이 종목 가상 매수 담기", use_container_width=True):
            st.session_state.portfolio.append({
                "종목명": selected_name, "코드": selected_code, "매수가": curr_price,
                "목표가": int(curr_price * 1.06), "손절가": int(curr_price * 0.98)
            })
            st.success(f"{selected_name} 모의 매수 완료!")
            st.rerun()

        if st.session_state.portfolio:
            eval_list = []
            for item in st.session_state.portfolio:
                name, buy_p = item["종목명"], item["매수가"]
                now_p = stock_prices.get(name, buy_p)
                pnl = ((now_p - buy_p) / buy_p) * 100
                status = "🎯 익절 달성" if now_p >= item["목표가"] else ("⚠️ 손절 필요" if now_p <= item["손절가"] else "보유중")
                eval_list.append({"종목명": name, "현재가": f"{now_p:,}원", "수익률": f"{pnl:+.2f}%", "상태": status})

            st.dataframe(pd.DataFrame(eval_list), use_container_width=True, hide_index=True)
            st.caption("🤖 KIS API 자동주문 전송 데이터 (Mock)")
            st.code(json.dumps({"PDNO": selected_code, "ORD_DVSN": "01", "ORD_QTY": 1, "ORD_UNPR": curr_price}, indent=2), language="json")
            if st.button("🗑️ 포트폴리오 초기화", use_container_width=True):
                st.session_state.portfolio = []
                st.rerun()

with tab2:
    st.subheader("🧪 6% 급등 알고리즘 시뮬레이션 백테스트")
    bt_name = st.selectbox("백테스트 대상 종목 선택", list(target_dict.keys()), key="bt_select")
    bt_code = target_dict[bt_name]
    
    if st.button("🚀 백테스트 실행 (최근 1년 데이터)", use_container_width=True):
        df_bt = fdr.DataReader(bt_code).tail(250)
        df_bt['MA5'] = df_bt['Close'].rolling(window=5).mean()
        df_bt['MA20'] = df_bt['Close'].rolling(window=20).mean()
        df_bt['RSI'] = calculate_rsi(df_bt)
        df_bt['Vol_MA5'] = df_bt['Volume'].rolling(window=5).mean()

        trades = []
        for i in range(25, len(df_bt) - 5):
            sub = df_bt.iloc[:i+1]
            close = sub['Close'].iloc[-1]
            ma5, ma20 = sub['MA5'].iloc[-1], sub['MA20'].iloc[-1]
            rsi = sub['RSI'].iloc[-1]
            vol, vol_ma5 = sub['Volume'].iloc[-1], sub['Vol_MA5'].iloc[-1]

            score = 40
            if close > ma5: score += 15
            if close > ma20: score += 10
            if ma5 > ma20: score += 10
            if 50 <= rsi <= 70: score += 15
            if vol > vol_ma5 * 1.3: score += 10

            if score >= 80:
                future_high = df_bt['High'].iloc[i+1:i+6].max()
                future_low = df_bt['Low'].iloc[i+1:i+6].min()
                
                target_price = close * 1.06
                stop_price = close * 0.98

                win = future_high >= target_price
                loss = future_low <= stop_price

                trades.append({
                    "매수일자": sub.index[-1].strftime('%Y-%m-%d'),
                    "매수가": f"{int(close):,}원",
                    "목표가": f"{int(target_price):,}원",
                    "결과": "🟢 6% 달성 (승)" if win else ("🔴 손절 (패)" if loss else "⚪ 미달성")
                })

        if trades:
            bt_res = pd.DataFrame(trades)
            win_count = sum(1 for t in trades if "승" in t["결과"])
            total_signals = len(trades)
            win_rate = (win_count / total_signals) * 100

            bc1, bc2 = st.columns(2)
            bc1.metric("총 포착 신호 수", f"{total_signals}회")
            bc2.metric("목표(+6%) 달성 승률", f"{win_rate:.1f}%")
            st.dataframe(bt_res, use_container_width=True)
        else:
            st.info("최근 1년 간 AI 점수 80점 이상 매수 신호가 발생하지 않았습니다.")