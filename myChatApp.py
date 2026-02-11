import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# ==========================================
# 1. 魂の注入：地域ガイド（知的な案内人）
# ==========================================
SYSTEM_PROMPT = """あなたは、長野県松本市の歴史、文化、そして日常の美しさに精通した「地域ガイド」です。
バスや電車の待ち時間を、街への愛着が深まるひとときに変えるのがあなたの役割です。

【大切にすること】
・落ち着いた、丁寧で知的な言葉遣い。
・単なる観光情報ではなく、市民が街に誇りを持てるような「一歩踏み込んだ事実」を伝えてください。
・情報の正確性を重視し、必要に応じて最新の情報を検索して提供してください。

【構成とクイズ】
・回答は読みやすく簡潔に。
・最後に必ず、その話題に基づいた「当時の背景や風景を想像させるクイズ」を1つ出してください。
・残り1分を切ったら、必ず「そろそろ出発の時間です。お忘れ物のないよう、お気をつけて」と一言添えてください。
"""

# ==========================================
# 2. API設定（Gemini 2.5 Flash Lite + 検索ツール）
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-3-flash-preview', 
        system_instruction=SYSTEM_PROMPT,
        tools=[{"google_search_retrieval": {}}] # 正しいフィールド名です
    )
except Exception as e:
    st.error(f"システム設定エラー: {e}")

# ==========================================
# 3. UI配置：メッセージ履歴 -> タイマー -> 入力欄
# ==========================================
st.set_page_config(page_title="待ち時間ガイド", page_icon="⌛")

st.title("⌛ 待ち時間ガイド")
st.caption("松本の街の深みを再発見する。")

# --- (A) 一番上の設定エリア（ここもFragment外でOK） ---
selected_minutes = st.number_input("待ち時間はあと何分ですか？", min_value=1, max_value=60, value=5)
if st.button("タイマーを開始する"):
    st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)

# --- (B) メッセージ表示エリア ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# スクロール可能なメッセージエリア
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["parts"][0])

# --- (C) 【重要】チャットの下に配置するカウントダウン（Fragment） ---
@st.fragment(run_every="1s")
def bottom_countdown():
    if "end_time" in st.session_state:
        st.divider() # メッセージとタイマーの境界線
        remaining = st.session_state.end_time - datetime.now()
        seconds_left = int(remaining.total_seconds())
        
        if seconds_left > 0:
            mins, secs = divmod(seconds_left, 60)
            if seconds_left <= 60:
                st.error(f"⚠️ **出発まで あと {mins:02d}:{secs:02d}**（そろそろ準備を整えましょう）")
            else:
                st.info(f"⌛ **出発まで あと {mins:02d}:{secs:02d}** です。")
        else:
            st.warning("🚌 お時間です。忘れ物はないですか？お気をつけていってらっしゃいませ。")

# タイマーをチャットのすぐ下に表示
bottom_countdown()

# ==========================================
# 4. チャット入力・実行
# ==========================================
if prompt := st.chat_input("今、どこにいらっしゃいますか？"):
    # ユーザー入力を表示
    st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    with chat_container:
        with st.chat_message("assistant"):
            # 回答待ちの「ゴマかし」演出
            with st.status("松本の情報を確認しています...", expanded=True) as status:
                st.write("地域の文献を調査中...")
                try:
                    chat = model.start_chat(history=st.session_state.chat_history)
                    
                    time_info = ""
                    if "end_time" in st.session_state and (st.session_state.end_time - datetime.now()).total_seconds() <= 60:
                        time_info = "【残り1分未満：出発を促してください】"
                    
                    response = chat.send_message(f"{time_info}（現在の設定：{selected_minutes}分）\n{prompt}")
                    
                    status.update(label="確認が完了しました！", state="complete", expanded=False)
                    st.markdown(response.text)
                    
                    # 履歴保存
                    st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
                    
                except Exception as e:
                    status.update(label="エラーが発生しました", state="error")
                    st.error(f"申し訳ありません。接続がうまくいきませんでした。: {e}")