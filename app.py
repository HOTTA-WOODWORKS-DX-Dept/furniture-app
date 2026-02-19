import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("🛋️ 家具コーディネートAI")

# APIキーの読み込み（設定されていない場合の案内を表示）
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.success("API接続OK")
except:
    st.warning("APIキーが設定されていません。Streamlitの設定画面でSecretsを入力してください。")

# 画面レイアウト
uploaded_file = st.file_uploader("家具の画像をアップロード", type=["jpg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="アップロード画像", use_column_width=True)
    if st.button("コーディネート開始"):
        st.info("ここにAIの生成結果が表示されます（現在はテスト動作中）")
