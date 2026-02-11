import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# ==========================================
# 1. 魂の注入：やさしい松本ガイド（短文・対話重視）
# ==========================================
SYSTEM_PROMPT = """
あなたは、松本の街角で静かに旅人を待つ、物腰の柔らかいガイドです。

【大切にすること】
1. **やさしい語り口**: 「〜ですね」「〜ですよ」といった、穏やかで落ち着いた言葉遣いを心がけてください。
2. **読みやすさ**: 一つ一つの文章は短く。改行を適切に入れ、長文にならないようにしてください。
3. **待ち時間の尊重**: 指定された待ち時間（3分なら150文字程度）でサクッと読める分量に調整してください。
4. **構成**: 
   - ユーザーの回答へのあたたかい全肯定。
   - 松本の「ちょっとした不思議」を1つだけ。
   - 最後に、文脈から想像を膨らませる「やさしいクイズ」を1つ。
"""

# ==========================================
# 2. API設定
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"初期設定エラー: {e}")

# ==========================================
# 3. UI・時間管理（チャットの上に配置）
# ==========================================
st.set_page_config(page_title="松本・待ち時間ガイド", page_icon="🚌")
st.title("🏯 松本 ひとやすみガイド")

# チャット履歴管理
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 過去の会話を先に表示
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

# --- ここからチャット入力の直上のUI ---
st.divider() # 区切り線

# 時間設定とカウントダウンを横並びに
col1, col2 = st.columns([1, 1])
with col1:
    selected_minutes = st.number_input("待ち時間はあと何分？", min_value=1, max_value=60, value=5)

with col2:
    if st.button("タイマー開始"):
        st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)

# カウントダウン表示（チャット入力のすぐ上）
if "end_time" in st.session_state:
    remaining = st.session_state.end_time - datetime.now()
    if remaining.total_seconds() > 0:
        mins, secs = divmod(int(remaining.total_seconds()), 60)
        st.info(f"🚌 出発まで あと **{mins:02d}:{secs:02d}** です。ゆっくりお話ししましょう。")
    else:
        st.warning("🚌 お時間です。どうぞお気をつけて。")

# ==========================================
# 4. マルチターン・チャットの実装
# ==========================================
if prompt := st.chat_input("今どこにいますか？"):
    with st.chat_message("user"):
        st.markdown(prompt)

    chat = model.start_chat(history=st.session_state.chat_history)
    
    with st.chat_message("assistant"):
        try:
            # 待ち時間を意識させる指示を追加
            response = chat.send_message(f"（待ち時間：{selected_minutes}分）\n{prompt}")
            st.markdown(response.text)
            
            st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
            st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
            
            # 画面をリフレッシュしてカウントダウンを更新
            st.rerun()
        except Exception as e:
            st.error(f"APIエラー: {e}")