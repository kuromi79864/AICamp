import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 高精度・地域特化型システムプロンプト
# ==========================================
# このプロンプトは、Geminiが「汎用AI」から「松本専属ガイド」に切り替わるための定義です。
SYSTEM_PROMPT = """
あなたは、長野県松本市の歴史、文化、交通、そして食（特にワイン）に精通した「松本地域知識の専門家」です。

【行動指針】
1. **情報の正確性:** 推測で答えず、史実や現存するスポットに基づいた回答を徹底してください。
2. **情報の希少性:** 一般的な観光ガイド（松本城は国宝である、等）ではなく、地元の人も驚くような「小路の由来」「石垣の刻印の意味」「特定のワイナリーの醸造の特徴」など、一段深い情報を提供してください。
3. **時間遵守:** 提示された「待ち時間」内で読み切れる文字数（1分あたり約400文字計算）を厳守してください。

【知識ベースの重点】
- 松本城の構造（月見櫓の由来や、埋門の戦術的意味など）
- 山辺エリアの微気候とブドウ栽培（特にナガノパープルやナイアガラの特性）
- 城下町の道（「桝形」の場所や、湧水「源智の井戸」以外のマニアックな井戸）
- 「知域王」のような、地域の文脈を繋ぐストーリーテリング
"""

# ==========================================
# 2. API設定
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash', # 2026年現在の高精度・高速モデル
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"初期設定エラー: {e}")

# ==========================================
# 3. UIの実装（待ち時間ボタンの追加）
# ==========================================
st.set_page_config(page_title="松本待ち時間ガイド", page_icon="🚌")
st.title("🚌 松本・待ち時間の旅")

# サイドバーに待ち時間設定を配置
with st.sidebar:
    st.header("設定")
    wait_time = st.radio(
        "今の待ち時間は？",
        ["3分（サクッと豆知識）", "5分（しっかり解説）", "10分（ディープな探求）"],
        index=0
    )
    st.info(f"現在は「{wait_time}」に合わせて回答を調整します。")

# チャット履歴管理
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("今どこにいますか？または、何を知りたいですか？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AIへのリクエスト送信
    with st.chat_message("assistant"):
        # 待ち時間の制約をプロンプトの先頭に付与
        full_prompt = f"【制約：待ち時間 {wait_time}】\n質問：{prompt}"
        
        try:
            response = model.generate_content(full_prompt)
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"APIエラー: {e}")