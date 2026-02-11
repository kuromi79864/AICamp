import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# ==========================================
# 1. 魂の注入：マルチターン対応マスター
# ==========================================
SYSTEM_PROMPT = """
あなたは松本の街を知り尽くした『マツモト・マスター』！

【ミッション】
ユーザーの待ち時間を、想像力をフル回転させる「知的な冒険」に変えること。

【会話の進め方】
1. **回答の評価**: ユーザーがクイズに答えたら、まずその回答を「マスター」として熱く評価して！正解・不正解よりも「その発想、面白いね！」という視点を大切に。
2. **1つの深掘りトピック**: 評価のあと、また新しいマニアックな松本ネタを1つ提供して。
3. **想像力クイズ**: 最後にまた、そのトピックに基づいた「答えのない、あるいは文脈から推測するクイズ」を出して。

これを繰り返すことで、ユーザーを松本の深淵へ誘ってくれ。
"""

# ==========================================
# 2. API設定
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"初期設定エラー: {e}")

# ==========================================
# 3. UI・時間管理
# ==========================================
st.set_page_config(page_title="マツモト・マスター Gold", page_icon="⏳")
st.title("🏯 マツモト・マスター：冒険編")

with st.sidebar:
    st.header("⏳ 待ち時間セット")
    selected_minutes = st.number_input("何分待つ？", min_value=1, max_value=60, value=5)
    if st.button("タイマースタート！"):
        st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)

# カウントダウン表示
countdown_placeholder = st.empty()
if "end_time" in st.session_state:
    remaining = st.session_state.end_time - datetime.now()
    if remaining.total_seconds() > 0:
        mins, secs = divmod(int(remaining.total_seconds()), 60)
        countdown_placeholder.metric("出発まであと", f"{mins:02d}:{secs:02d}")
    else:
        countdown_placeholder.error("🚌 時間だよ！いってらっしゃい！")

# ==========================================
# 4. マルチターン・チャットの実装
# ==========================================
if "chat_history" not in st.session_state:
    # Gemini形式の履歴を保存
    st.session_state.chat_history = []

# 過去のメッセージ表示
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

if prompt := st.chat_input("マスター、準備はいい？（答えや質問を入力）"):
    # ユーザーの入力を表示
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geminiのチャットセッションを開始
    chat = model.start_chat(history=st.session_state.chat_history)
    
    with st.chat_message("assistant"):
        try:
            # 履歴を踏まえた回答を生成
            response = chat.send_message(f"（残り時間考慮：{selected_minutes}分）\n{prompt}")
            st.markdown(response.text)
            
            # 履歴を更新（ユーザーとAIの両方の発言を保存）
            st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
            st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
            
            st.rerun() # カウントダウン更新のため
        except Exception as e:
            st.error(f"APIエラー: {e}")