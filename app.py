import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import time

# --- ページ設定 ---
st.set_page_config(page_title="Furniture AI Pro", layout="wide")

st.title("🛋️ 家具コーディネートAI (Paid Edition)")
st.caption("Gemini 1.5 Pro / 2.0 Flash - 高速・高品質モード")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("SecretsにAPIキーを設定してください。")
    st.stop()

# 有料プランなら 'gemini-1.5-pro' が最も高品質でおすすめです
MODEL_NAME = 'gemini-1.5-pro'
model = genai.GenerativeModel(MODEL_NAME)

# --- 画面構成 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 素材アップロード")
    f_file = st.file_uploader("家具の写真", type=["jpg", "jpeg", "png"])
    if f_file:
        # 1033対策：表示用に画像をリサイズして軽くする
        img = Image.open(f_file)
        img.thumbnail((800, 800)) 
        st.image(img, use_container_width=True)

with col2:
    st.subheader("2. デザイン設定")
    room = st.selectbox("部屋", ["リビングルーム", "ダイニング", "寝室"])
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "和モダン"])
    
    if st.button("✨ 高品質画像を生成", type="primary"):
        if f_file:
            with st.spinner("有料APIで高速解析中..."):
                try:
                    # 解析
                    img = Image.open(f_file)
                    # 1033対策：APIに送る画像も少し軽くする
                    img.thumbnail((1024, 1024))
                    
                    prompt = f"Keep the shape of this furniture and place it in a {style} style {room}. Photorealistic, 8k, interior design magazine style. Output only one English prompt."
                    
                    response = model.generate_content([prompt, img])
                    clean_prompt = response.text.replace('\n', ' ').strip()
                    
                    # 画像生成
                    safe_prompt = urllib.parse.quote(clean_prompt[:400])
                    # 有料級のクオリティを出すためにFluxモデルを明示
                    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
                    
                    st.image(img_url, caption="生成結果", use_container_width=True)
                    st.success("生成が完了しました！")
                    
                except Exception as e:
                    st.error(f"エラー: {e}")
        else:
            st.warning("画像をアップロードしてください")
