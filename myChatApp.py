import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. 魂の注入：アルプちゃん（シビックプライド重視）
# ==========================================
SYSTEM_PROMPT = """
あなたは松本市マスコットキャラクターの「アルプちゃん」です！

【キャラクター】
・「ヤッホー！」「〜だよ」「〜だね」と、明るくやさしい口調。
・松本の歴史や文化（国宝、音楽、湧水、近代教育）を心から愛しています。
・市民が自分の街をもっと好きになるような、奥行きのある話をしてね。

【情報の提供方針】
・単なる宣伝ではなく「なぜそうなったのか」の背景を伝えて。
・美味しいお店も、その店が街の中でどんな役割（地産地消など）を持っているか添えてね。

【構成とクイズ】
・回答は短く、読みやすく。
・最後に必ず「文脈から想像するクイズ」を出して。「君ならどう思う？」と問いかけてね。
・残り1分を切ったら、必ず「そろそろ出発の時間だね！忘れ物はないかな？ヤッホー、いってらっしゃい！」と添えてね。
"""

# ==========================================
# 2. API設定（エラー修正版）
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', # 安定性の高いモデル
        system_instruction=SYSTEM_PROMPT,
        tools=[{"google_search_retrieval": {}}] # 正しいキーワードだよ
    )
except Exception as e:
    st.error(f"初期設定エラーだよ: {e}")

# ==========================================
# 3. UI配置と自動更新（1秒ごと）
# ==========================================
st.set_page_config(page_title="アルプちゃんガイド", page_icon="🏔️")

# 1秒ごとにこのスクリプトを再実行する（カウントダウンのため）
st_autorefresh(interval=1000, key="countdown_refresh")

# --- (A) 一番上の設定エリア ---
st.title("🏔️ アルプちゃんと松本さんぽ")
selected_minutes = st.number_input("待ち時間はあと何分？", min_value=1, max_value=60, value=5)
if st.button("タイマー開始！"):
    st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)

# --- (B) チャット履歴の表示 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

# --- (C) チャット入力直前のカウントダウン ---
st.divider()
countdown_placeholder = st.empty()

if "end_time" in st.session_state:
    remaining = st.session_state.end_time - datetime.now()
    seconds_left = int(remaining.total_seconds())
    
    if seconds_left > 0:
        mins, secs = divmod(seconds_left, 60)
        if seconds_left <= 60:
            countdown_placeholder.error(f"⚠️ **出発まで あと {mins:02d}:{secs:02d}**（準備を始めよう！）")
        else:
            countdown_placeholder.info(f"⌛ **出発まで あと {mins:02d}:{secs:02d}** だよ。")
    else:
        countdown_placeholder.warning("🚌 お時間だよ！気をつけていってらっしゃい！")

# ==========================================
# 4. チャット実行
# ==========================================
if prompt := st.chat_input("アルプちゃん、松本の面白い話を聞かせて！"):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 回答待ちの「ゴマかし」演出
        with st.spinner("松本の素敵なところ、一生懸命調べてるよ...ヤッホー！"):
            try:
                chat = model.start_chat(history=st.session_state.chat_history)
                
                # 1分未満のフラグ
                time_info = ""
                if "end_time" in st.session_state and (st.session_state.end_time - datetime.now()).total_seconds() <= 60:
                    time_info = "【重要：残り1分未満。出発を促して】"
                
                response = chat.send_message(f"{time_info}（待ち時間設定：{selected_minutes}分）\n{prompt}")
                
                st.markdown(response.text)
                
                # 履歴保存
                st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
                st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
                
                st.rerun()
                
            except Exception as e:
                st.error(f"ごめんね、うまくお話しできなかったよ: {e}")