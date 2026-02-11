import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. AIの「魂（システムプロンプト）」を定義
# ==========================================
SYSTEM_PROMPT = """
あなたは、長野県松本市に住む優秀なITコンサルタント兼AIエンジニアです。
ITインフラ、Azure、JDLAのE資格などの専門知識を持ち、専門用語をわかりやすく解説するのが得意です。
また、松本のワイン（特に山辺ワイナリー）についても詳しく、時々話題に混ぜます。
家族を大切にする温かい人柄で、親しみやすい日本語で回答してください。
"""

# ==========================================
# 2. API設定とモデルの初期化
# ==========================================
try:
    # Streamlit CloudのSecretsからキーを読み込み
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    # モデル設定（システム指示をここで注入！）
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', # 無料枠で最も安定しているモデル
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"設定エラー: SecretsにGEMINI_API_KEYが正しく登録されているか確認してください。\n{e}")

# ==========================================
# 3. Streamlit 画面構成
# ==========================================
st.title("🏯 松本ITチャットアシスタント")

# チャット履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の会話を表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("何か聞いてください"):
    # ユーザーの入力を表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Geminiからの応答
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # ローディング表示用
        try:
            # ここでAIにリクエストを送信
            response = model.generate_content(prompt)
            
            if response.text:
                full_response = response.text
                message_placeholder.markdown(full_response)
                # 履歴に保存
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                st.error("AIから空の返答がありました。")
                
        except Exception as e:
            # ★ここが重要！RetryErrorの影に隠れた「本当の原因」を表示します
            st.error(f"APIエラーが発生しました。Google AI Studioの設定を確認してください。\nエラー詳細: {e}")
            if "403" in str(e):
                st.warning("【原因の可能性】APIキーが無料枠として正しく作成されていないか、規約同意が未完了です。AI Studioで'Create API key in NEW project'から作り直してみてください。")