import streamlit as st
import google.generativeai as genai
import os

# ページ設定
st.set_page_config(page_title="Furniture AI", layout="wide")

# タイトル
st.title("🛋️ 家具AI")

# APIキーの読み込み（エラーハンドリング付き）
try:
    # 1. Secretsから読み込みトライ
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("設定エラー: Secretsに GEMINI_API_KEY がありません。")
        st.stop()
        
    # 2. 初期化
    genai.configure(api_key=api_key)
    
    # 3. モデル選択（安全なフラッシュモデル）
    model = genai.GenerativeModel("gemini-1.5-flash")
    
except Exception as e:
    st.error(f"起動エラー: {e}")
    st.stop()

# 入力フォーム
user_input = st.text_input("どんな家具の画像を生成したいですか？", "北欧風のソファ")

if st.button("生成"):
    try:
        with st.spinner("AIに問い合わせ中..."):
            # 画像生成プロンプトを作成させる
            response = model.generate_content(f"Create a short English prompt for an image of: {user_input}")
            
            # 結果表示
            st.success("成功しました")
            st.write(response.text)
            
    except Exception as e:
        st.error(f"実行エラー: {e}")
