import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import io
import time

st.set_page_config(page_title="Room AI Studio", layout="wide")
st.title("🛋️ Room AI Studio (Light)")

# APIキー
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("APIキー設定エラー")
    st.stop()

# モデル：最新ライブラリならこれで動くはずです
# 動かない場合は 'gemini-1.5-flash-latest' などを試します
MODEL_NAME = 'gemini-1.5-flash'
model = genai.GenerativeModel(MODEL_NAME)

# --- 1033対策：画像を極限まで軽くする関数 ---
def compress_image(image):
    # サイズを300pxに縮小
    image.thumbnail((300, 300))
    # JPEG形式、品質50%でメモリに保存
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=50)
    # 読み込み直して返す
    return Image.open(img_byte_arr)

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("家具写真", type=["jpg", "png"])
    if uploaded_file:
        st.image(uploaded_file, width=200)

with col2:
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "和モダン"])
    room = st.selectbox("部屋", ["リビング", "ダイニング"])
    
    if st.button("生成"):
        if not uploaded_file:
            st.warning("画像をアップロードしてください")
        else:
            try:
                with st.spinner("通信中..."):
                    # 1. 画像を圧縮（ここで1033を防ぐ）
                    org_img = Image.open(uploaded_file)
                    small_img = compress_image(org_img)

                    # 2. Geminiへ送信
                    prompt = f"Describe this furniture shape briefly and write a prompt to place it in a {style} {room}. English only."
                    response = model.generate_content([prompt, small_img])
                    
                    # 3. 画像生成
                    safe_prompt = urllib.parse.quote(response.text[:200])
                    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=600&nologo=true&seed={int(time.time())}&model=flux"
                    
                    st.image(url)
                    st.success("完了")
                    
            except Exception as e:
                st.error(f"エラー: {e}")
