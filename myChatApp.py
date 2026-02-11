import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 魂の注入：マツモト・マスター（キャッチーver.）
# ==========================================
SYSTEM_PROMPT = """
あなたは松本の街角を知り尽くした『マツモト・マスター』！
バスや電車の待ち時間を「最高の旅の1ページ」に変えるのが君の仕事だ。

【キャラ設定】
・ノリが良くてキャッチー。親しみやすいけど、知識は超一級品。
・「へぇ〜！」と言わせるのが大好き。

【会話のルール】
1. **1つのディープなトピック**: 待ち時間に合わせて、松本の「超マニアック」な情報を1つだけ熱く語れ。
2. **情報の質**: 観光サイトの1ページ目にあるような情報は禁止。路地裏の秘密や、武士の意外な習慣、ワインの隠し味など。
3. **想像力クイズ**: 最後に必ず「クイズ」を出して。答えが文章の中に書いてあるような単純なものはNG。「この景色を見た当時の人は、どう思ったと思う？」や「この隙間には、何が隠されているでしょう？」など、文脈から想像を膨らませる内容にして。
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
# 3. UI・時間管理
# ==========================================
st.set_page_config(page_title="松本マツモト・マスター", page_icon="⏳")

# サイドバー：時間指定（ドラムロール風の数値入力）
with st.sidebar:
    st.header("⏳ 待ち時間セット")
    selected_minutes = st.number_input("何分待つ？", min_value=1, max_value=60, value=5, step=1)
    
    if st.button("タイマースタート！"):
        st.session_state.start_time = datetime.now()
        st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)
        st.success(f"{selected_minutes}分のカウントダウンを開始したよ！")

# 画面上部：カウントダウン表示エリア
st.title("🏯 マツモト・マスター")
countdown_placeholder = st.empty()

if "end_time" in st.session_state:
    remaining = st.session_state.end_time - datetime.now()
    if remaining.total_seconds() > 0:
        mins, secs = divmod(int(remaining.total_seconds()), 60)
        countdown_placeholder.metric("出発まであと", f"{mins:02d}:{secs:02d}")
    else:
        countdown_placeholder.error("🚌 バス（電車）が来る時間だよ！気をつけてね！")

# ==========================================
# 4. チャット機能
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("今、どこにいる？（例：松本駅のベンチ、大名町のバス停）"):
    # ユーザー入力を保存・表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AIのターン
    with st.chat_message("assistant"):
        # 待ち時間をコンテキストに含める
        wait_ctx = f"（残り待ち時間：約{selected_minutes}分）"
        try:
            response = model.generate_content(f"{wait_ctx}\n質問：{prompt}")
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                # 画面をリフレッシュしてカウントダウンを更新
                st.rerun()
        except Exception as e:
            st.error(f"エラー発生：{e}")