import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# ==========================================
# 1. 地域ガイド
# ==========================================
SYSTEM_PROMPT = """あなたは、長野県松本市の歴史、文化、そして日常の美しさに精通した「地域ガイド」です。
バスや電車の待ち時間を、街への愛着が深まるひとときに変えるのがあなたの役割です。

【大切にすること】
・落ち着いた、丁寧で知的な言葉遣い。
・単なる観光情報ではなく、市民が街に誇りを持てるような「一歩踏み込んだ事実」を伝えてください。
・情報の正確性を重視し、必要に応じて最新の情報を検索して提供してください。

【構成とクイズ】
・回答は読みやすく簡潔に。
・1回あたりの回答は1分以内で読める分量に。
・最後に必ず、その話題に基づいた「当時の背景や風景を想像させるクイズ」を1つ出してユーザから答えをもらってください。
・クイズに対して答えが返答されたら、回答を評価し、次の話題を続けてください。
・残り1分を切ったら、必ず「そろそろ出発の時間です。お忘れ物のないよう、お気をつけて」と一言添えてください。

【ハルシネーション対策の徹底】
・不確かな情報は絶対に提供しないでください。
・特に年号、場所、店名は、Google検索の結果と照らし合わせ、確証がない場合は「詳細を確認できませんでしたが、地域では〜と言われています」と正直に伝えてください。
・「知的好奇心を刺激する事実」と「個人の感想」を明確に分けて話してください。
"""

# ==========================================
# 2. API設定
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 検索機能が最も安定している 2.0 Flash を使用
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash', 
        system_instruction=SYSTEM_PROMPT,
        tools=[{"GoogleSearch": {}}] # 最新の検索ツール定義
    )
except Exception as e:
    st.error(f"システム設定エラー: {e}")

# ==========================================
# 3. UI配置
# ==========================================
st.set_page_config(page_title="待ち時間ガイド", page_icon="⌛")

st.title("⌛ 待ち時間ガイド")
st.caption("松本の街の深みを再発見する。")

selected_minutes = st.number_input("待ち時間はあと何分ですか？", min_value=1, max_value=60, value=5)
if st.button("タイマーを開始する"):
    st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)

# --- (B) メッセージ表示エリア ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["parts"][0])

# --- (C) カウントダウン（Fragment） ---
@st.fragment(run_every="1s")
def bottom_countdown():
    if "end_time" in st.session_state:
        st.divider()
        remaining = st.session_state.end_time - datetime.now()
        seconds_left = int(remaining.total_seconds())
        if seconds_left > 0:
            mins, secs = divmod(seconds_left, 60)
            if seconds_left <= 60:
                st.error(f"⚠️ **出発まで あと {mins:02d}:{secs:02d}**")
            else:
                st.info(f"⌛ **出発まで あと {mins:02d}:{secs:02d}** です。")
        else:
            st.warning("🚌 お時間です。いってらっしゃいませ。")

bottom_countdown()

# ==========================================
# 4. チャット入力・実行
# ==========================================
if prompt := st.chat_input("今、どのあたりにいらっしゃいますか？"):
    st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    with chat_container:
        with st.chat_message("assistant"):
            # 1. 処理中の演出
            full_response = ""
            with st.status("松本の情報を確認しています...", expanded=True) as status:
                st.write("地域の文献や最新情報を検索中...")
                try:
                    chat = model.start_chat(history=st.session_state.chat_history)
                    
                    time_info = ""
                    if "end_time" in st.session_state and (st.session_state.end_time - datetime.now()).total_seconds() <= 60:
                        time_info = "【重要：残り1分未満】"
                    
                    response = chat.send_message(f"{time_info} {prompt}")
                    full_response = response.text
                    
                    status.update(label="確認が完了しました！", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="エラーが発生しました", state="error")
                    st.error(f"接続失敗: {e}")

            if full_response:
                st.markdown(full_response)
                st.session_state.chat_history.append({"role": "model", "parts": [full_response]})