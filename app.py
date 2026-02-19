import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import time
import re

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")

st.title("🛋️ Room AI Studio")
st.caption("画像表示エラー対策済みバージョン")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーを設定してください。")
    st.stop()

# --- モデル設定 ---
MODEL_NAME = 'gemini-flash-latest'
model = genai.GenerativeModel(MODEL_NAME)

# --- 画像処理関数 ---
def prepare_image(uploaded_file):
    if uploaded_file is None:
        return None
    img = Image.open(uploaded_file)
    img.thumbnail((700, 700)) # 通信負荷を下げる
    return img

# --- メインエリア ---
col1, col2 = st.columns([1, 1])

with col1:
    f_file = st.file_uploader("家具の写真をアップロード", type=["jpg", "jpeg", "png"])
    if f_file:
        st.image(prepare_image(f_file), caption="解析対象", use_container_width=True)

with col2:
    room = st.selectbox("配置する部屋", ["リビング", "ダイニング", "寝室"])
    style = st.selectbox("テイスト", ["北欧モダン", "ヴィンテージ", "和モダン"])
    
    st.divider()
    generate_btn = st.button("✨ 画像を生成する", type="primary")

# --- 生成ロジック ---
if generate_btn:
    if not f_file:
        st.warning("家具の写真をアップロードしてください。")
    else:
        with st.spinner("AIがコーディネートを構築中..."):
            try:
                # 1. Geminiに解析依頼
                img = prepare_image(f_file)
                prompt_msg = f"Look at the furniture and create a short English prompt (under 50 words) for a photorealistic {style} {room} interior. Output ONLY the prompt text. No quotes, no intro."
                
                response = model.generate_content([prompt_msg, img])
                raw_prompt = response.text
                
                # --- 【重要】プロンプトの「掃除」 ---
                # 改行を消し、余計な記号を削除し、短くカットする
                clean_prompt = raw_prompt.replace('\n', ' ').strip()
                clean_prompt = re.sub(r'[^a-zA-Z0-9\s,.-]', '', clean_prompt) # 記号を掃除
                clean_prompt = clean_prompt[:300] # 長すぎるとURLが壊れるのでカット
                
                # 2. 画像URLの構築
                # 毎回異なる結果が出るよう、seedに現在時刻を使用
                encoded_prompt = urllib.parse.quote(clean_prompt)
                img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
                
                # 3. 結果の表示
                st.subheader("🖼️ 生成された提案イメージ")
                
                # 画像の表示テスト
                image_placeholder = st.empty()
                image_placeholder.image(img_url, use_container_width=True)
                
                # バックアップ：もし画像が表示されない場合の直接リンク
                st.markdown(f"""
                ---
                ✅ **コーディネートが完了しました！** ※画像が表示されない場合は、以下のリンクを直接クリックして確認してください。  
                👉 [**ここをクリックして別タブで画像を開く**]({img_url})
                """)
                
                with st.expander("AIの指示内容を確認"):
                    st.write(f"生成に使用したプロンプト: {clean_prompt}")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
