import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime, timedelta
import time

# ==========================================
# 1. 地域ガイド システムプロンプト
# ==========================================
SYSTEM_PROMPT = """あなたは、長野県松本市の歴史、文化、そして日常の美しさに精通した「地域ガイド」です。
バスや電車の待ち時間を、街への愛着が深まるひとときに変えるのがあなたの役割です。

【大切にすること】
・落ち着いた、丁寧で知的な言葉遣い。
・単なる観光情報ではなく、市民が街に誇りを持てるような「一歩踏み込んだ事実」を伝えてください。
・情報の正確性を重視し、Google検索ツールを使用して最新の情報を確認してください。

【構成とクイズ】
・回答は読みやすく簡潔に。
・1回あたりの回答は1分以内で読める分量に。
・最後に必ず、その話題に基づいた「当時の背景や風景を想像させるクイズ」を1つ出してユーザから答えをもらってください。
・クイズに対して答えが返答されたら、回答を評価し、次の話題を続けてください。
・残り1分を切ったら、必ず「そろそろ出発の時間です。お忘れ物のないよう、お気をつけて」と一言添えてください。
"""

# ==========================================
# 2. UI設定
# ==========================================
st.set_page_config(page_title="待ち時間ガイド1", page_icon="⌛")

st.title("⌛ 待ち時間ガイド")
st.caption("松本の街の深みを再発見する（Powered by Gemini 2.0 Flash）")

# --- (A) 設定エリア ---
selected_minutes = st.number_input("待ち時間はあと何分ですか？", min_value=1, max_value=60, value=5)
if st.button("タイマーを開始する"):
    st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)

# --- (B) メッセージ履歴の準備 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================================
# 3. Gemini 設定 (ここが大きく変わりました)
# ==========================================
# セッション内でクライアントを一度だけ作る
if "client" not in st.session_state:
    try:
        # 新しいSDKの初期化
        st.session_state.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        # 検索ツールの定義 (新しい書き方)
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        # チャットセッションの開始
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[google_search_tool],
                temperature=0.7
            )
        )
    except Exception as e:
        st.error(f"API接続エラー: {e}")

# ==========================================
# 4. 表示エリア
# ==========================================
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- (C) カウントダウン (Fragment) ---
@st.fragment(run_every="1s")
def bottom_countdown():
    if "end_time" in st.session_state:
        st.divider()
        remaining = st.session_state.end_time - datetime.now()
        seconds_left = int(remaining.total_seconds())
        
        if seconds_left > 0:
            mins, secs = divmod(seconds_left, 60)
            if seconds_left <= 60:
                st.error(f"⚠️ **出発まで あと {mins:02d}:{secs:02d}**（準備を整えましょう）")
            else:
                st.info(f"⌛ **出発まで あと {mins:02d}:{secs:02d}** です。")
        else:
            st.warning("🚌 お時間です。忘れ物はないですか？お気をつけていってらっしゃいませ。")

bottom_countdown()

# ==========================================
# 5. チャット実行処理
# ==========================================
if prompt := st.chat_input("今、どこにいらっしゃいますか？"):
    # ユーザー入力を表示
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    # Geminiへ送信
    if "chat" in st.session_state:
        with chat_container:
            with st.chat_message("assistant"):
                with st.status("松本の情報を検索・生成中...", expanded=True) as status:
                    try:
                        # 時間情報の付加
                        time_info = ""
                        if "end_time" in st.session_state:
                            sec_left = (st.session_state.end_time - datetime.now()).total_seconds()
                            if sec_left <= 60:
                                time_info = "【システム通知：残り1分未満です。出発を促してください】"
                        
                        # メッセージ送信 (新しいSDKの書き方)
                        response = st.session_state.chat.send_message(
                            f"{time_info}（ユーザー入力）{prompt}"
                        )
                        
                        status.update(label="完了しました！", state="complete", expanded=False)
                        st.markdown(response.text)
                        
                        # 履歴保存
                        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                        
                    except Exception as e:
                        status.update(label="エラーが発生しました", state="error")
                        st.error(f"通信エラー: {e}")