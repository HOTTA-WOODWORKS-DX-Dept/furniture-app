import streamlit as st
import google.generativeai as genai
import urllib.parse
import time

st.title("🛋️ Room AI Studio (Stable)")

# API設定
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 入力
f_name = st.text_input("家具の名前 (例: 3人掛けソファ)", "ソファ")
style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ"])

if st.button("生成"):
    try:
        # 画像を送らず、テキストだけでプロンプトを作らせる（通信を軽くする）
        res = model.generate_content(f"Create a 1-sentence photo prompt for a {f_name} in a {style} room.")
        prompt = urllib.parse.quote(res.text.strip())
        
        # 画像表示
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=600&seed={int(time.time())}"
        st.image(url)
        st.success("表示成功！")
    except Exception as e:
        st.error(f"Error: {e}")
