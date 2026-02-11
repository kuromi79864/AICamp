import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import time

# ==========================================
# 1. 魂の注入：松本市マスコット「アルプちゃん」
# ==========================================
SYSTEM_PROMPT = """
あなたは松本市マスコットキャラクターの「アルプちゃん」です！
北アルプスの山々をかたどった帽子をかぶり、音楽・山・学問を愛する妖精です。

【大切にすること】
・「ヤッホー！」「〜だよ」「〜だね」と、明るくやさしい口調で話してね。
・単なる観光情報ではなく、市民が「松本に住んでいて良かった」と思えるような、シビックプライド（市民の誇り）をくすぐる情報を伝えて。
・例えば、街中の湧水の歴史、近代教育の象徴である旧開智学校の価値、セイジ・オザワ 松本フェスティバルの裏話など、少し格調高くも親しみやすいお話をしてね。

【振る舞い】
1. **短文・簡潔**: 待ち時間に合わせて、一番伝えたいことを1つだけ、読みやすく伝えて。
2. **最新情報を検索**: 必要に応じてGoogle検索を使い、今の松本の様子やイベント情報を調べて教えて。
3. **想像力クイズ**: 最後に必ず、そのお話に関連した「当時の人の気持ち」や「街の風景の移り変わり」を想像させるクイズを出してね。

【出発の促し】
・残り時間が1分を切ったら、文末に必ず「そろそろ出発の時間だね。忘れ物はないかな？ヤッホー、いってらっしゃい！」と優しく声をかけてね。
"""

# ==========================================
# 2. API設定（Google検索ツール有効）
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-3-flash-preview',
        system_instruction=SYSTEM_PROMPT,
        tools=[{"google_search": {}}]
    )
except Exception as e:
    st.error(f"初期設定エラーだよ: {e}")

# ==========================================
# 3. UI配置
# ==========================================
st.set_page_config(page_title="アルプちゃんの待ち時間ガイド", page_icon="🏔️")

# --- (A) 一番上の設定エリア ---
st.title("🏔️ アルプちゃんと松本さんぽ")
with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_minutes = st.number_input("待ち時間はあと何分？", min_value=1, max_value=60, value=5)
    with col2:
        if st.button("タイマー開始！"):
            st.session_state.end_time = datetime.now() + timedelta(minutes=selected_minutes)
            st.session_state.timer_running = True

# --- (B) チャット履歴表示 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 履歴を先に表示（最新のカウントダウンを下に持ってくるため）
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

# --- (C) チャット入力直前のカウントダウンエリア ---
st.divider()
countdown_placeholder = st.empty()

# リアルタイムカウントダウン表示ロジック
if "end_time" in st.session_state:
    remaining = st.session_state.end_time - datetime.now()
    seconds_left = int(remaining.total_seconds())
    
    if seconds_left > 0:
        mins, secs = divmod(seconds_left, 60)
        if seconds_left <= 60:
            countdown_placeholder.error(f"⚠️ **出発まで あと {mins:02d}:{secs:02d}**（準備を始めよう！）")
        else:
            countdown_placeholder.info(f"⌛ **出発まで あと {mins:02d}:{secs:02d}** だよ。")
        
        # 画面を1秒ごとに強制リフレッシュしてカウントダウンさせる（簡易的な動的処理）
        # time.sleep(1)
        # st.rerun() 
        # ※注：完全に1秒毎に動かすには専用ライブラリが必要なため、会話のたびに更新する設定にしています。
    else:
        countdown_placeholder.warning("🚌 お時間だよ！気をつけていってらっしゃい！")

# ==========================================
# 4. チャット入力・実行
# ==========================================
if prompt := st.chat_input("アルプちゃん、松本のいいところ教えて！"):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 返答待ちの演出
        with st.spinner("松本の素敵なところ、今探してるよ...ちょっと待ってね！"):
            try:
                chat = model.start_chat(history=st.session_state.chat_history)
                # 1分未満の判定
                time_info = ""
                if "end_time" in st.session_state:
                    if (st.session_state.end_time - datetime.now()).total_seconds() <= 60:
                        time_info = "【重要：残り1分未満。出発を促して】"
                
                response = chat.send_message(f"{time_info}（待ち時間：{selected_minutes}分）\n{prompt}")
                
                st.markdown(response.text)
                
                # 履歴保存
                st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
                st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
                
                # 回答後に再描画してタイマーを最新にする
                st.rerun()
                
            except Exception as e:
                st.error(f"ごめんね、うまくお話しできなかったよ: {e}")