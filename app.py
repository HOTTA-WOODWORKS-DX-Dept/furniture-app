import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import time
import io

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio (Hybrid)", layout="wide")
st.title("🛋️ Room AI Studio")
st.caption("画像がだめなら文字で指示！ハイブリッド版")

# --- API設定 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 成功実績のあるモデル名
    model = genai.GenerativeModel('models/gemini-flash-latest')
except:
    st.error("APIキー設定エラー")
    st.stop()

# --- 画面構成 ---
st.subheader("1. 家具を指定する")

# タブで切り替え（ここがポイント！）
tab1, tab2 = st.tabs(["📷 写真をアップロード", "✍️ 文字で入力"])

furniture_desc = ""
uploaded_img = None

with tab1:
    f_file = st.file_uploader("家具の写真", type=["jpg", "png", "jpeg"])
    if f_file:
        st.image(f_file, width=200)
        uploaded_img = f_file

with tab2:
    text_input = st.text_input("家具の特徴を入力 (例: 茶色の革製3人掛けソファ)", "")
    if text_input:
        furniture_desc = text_input

st.subheader("2. 部屋のスタイル")
col1, col2 = st.columns(2)
with col1:
    room = st.selectbox("部屋", ["リビング", "ダイニング", "寝室", "オフィス"])
with col2:
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "インダストリアル", "和モダン"])

st.divider()

if st.button("✨ 生成スタート", type="primary"):
    status = st.empty()
    status.info("🚀 AIが思考中...")
    
    try:
        final_prompt = ""
        
        # A. 画像がある場合 (Geminiに画像を見せる)
        if uploaded_img:
            img = Image.open(uploaded_img)
            # 画像を極小化
            img.thumbnail((300, 300))
            
            prompt = f"Describe this furniture and write a short English prompt to place it in a {style} {room}. No intro."
            response = model.generate_content([prompt, img])
            final_prompt = response.text
            
        # B. 文字入力がある場合 (Geminiに想像させる)
        elif furniture_desc:
            prompt = f"Write a short English prompt for a photorealistic image of a '{furniture_desc}' placed in a {style} {room}. No intro."
            response = model.generate_content(prompt)
            final_prompt = response.text
            
        else:
            st.warning("写真か文字、どちらかを入力してください")
            st.stop()

        # 画像生成 (Pollinations)
        status.success("描画中...")
        clean_prompt = final_prompt.replace('\n', ' ').strip()[:400]
        encoded = urllib.parse.quote(clean_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
        
        st.image(url, use_container_width=True)
        st.markdown(f"[画像リンク]({url})")
        
    except Exception as e:
        st.error(f"エラー: {e}")
        st.info("ヒント: 画像でエラーが出る場合は、「文字で入力」タブを試してみてください。")
