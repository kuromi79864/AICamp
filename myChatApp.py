import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# ==========================================
# 1. 魂の注入：地域ガイド（知的な案内人）
# ==========================================
SYSTEM_PROMPT = """
あなたは、長野県松本市の歴史や文化に精通した「地域ガイド」です。
...（中略：先ほどのシビックプライド重視の設定）...
"""

# ==========================================
# 2. API設定
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=SYSTEM_PROMPT,
        tools=[{"google_search_retrieval": {}}]
    )
except Exception as e:
    st.error(f"システム設定エラー: {e}")

# ==========================================
# 3. UI配置：タイマー部分を独立（Fragment化）
# ==========================================
st.set_page_config(page_title="待ち時間ガイド", page_icon="⌛")

st.title("⌛ 待ち時間ガイド")
st.caption("松本の街の深みを再発見する、知的なひとときを。")

# --- (A) 一番上の設定エリア ---
selected_minutes = st.number_input("待ち時間はあと何分ですか？", min_value=1, max_value=60, value=5)
if st.button("タイマーを開始する"):
    st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)

# --- (B) カウントダウン専用の「独立した」エリア ---
@st.fragment(run_every="1s") # 1秒ごとに「ここだけ」を更新
def show_countdown():
    if "end_time" in st.session_state:
        remaining = st.session_state.end_time - datetime.now()
        seconds_left = int(remaining.total_seconds())
        
        if seconds_left > 0:
            mins, secs = divmod(seconds_left, 60)
            if seconds_left <= 60:
                st.error(f"⚠️ **出発まで あと {mins:02d}:{secs:02d}** （準備を始めましょう）")
            else:
                st.info(f"⌛ **出発まで あと {mins:02d}:{secs:02d}** です。")
        else:
            st.warning("🚌 お時間です。お気をつけていってらっしゃいませ。")

# タイマーの表示場所
st.divider()
show_countdown() 
st.divider()

# ==========================================
# 4. チャット表示・実行（ここは更新に巻き込まれない）
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 履歴の表示
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

# チャット入力
if prompt := st.chat_input("今、どこにいらっしゃいますか？"):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("情報を確認しています..."):
            try:
                chat = model.start_chat(history=st.session_state.chat_history)
                
                # 1分未満のフラグ準備
                time_info = ""
                if "end_time" in st.session_state:
                    if (st.session_state.end_time - datetime.now()).total_seconds() <= 60:
                        time_info = "【重要：残り1分未満。出発を促してください】"
                
                response = chat.send_message(f"{time_info}（現在の設定：{selected_minutes}分）\n{prompt}")
                
                st.markdown(response.text)
                
                # 履歴保存
                st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
                st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")