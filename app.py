import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")
st.title("🛋️ Room AI Studio")
st.caption("通信エラー・モデル名エラー対策済み")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ SecretsにAPIキーを設定してください。")
    st.stop()

# --- 【重要】あなたの環境で「存在する」モデル名を使用 ---
# 診断リストにあった、最も確実な名前を指定します
MODEL_NAME = 'models/gemini-flash-latest'

@st.cache_resource
def get_model():
    return genai.GenerativeModel(MODEL_NAME)

try:
    model = get_model()
except Exception as e:
    st.error(f"モデル設定エラー: {e}")
    st.stop()

# --- 【最重要】通信エラー(1033)を回避する画像圧縮関数 ---
def compress_image(image):
    # 1. サイズを400pxまで縮小（スマホ写真は大きすぎるため）
    image.thumbnail((400, 400))
    
    # 2. メモリ上でJPEG形式に変換して容量を削減
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=60)
    img_byte_arr.seek(0)
    
    # 3. 軽量化した画像を返す
    return Image.open(img_byte_arr)

# --- メイン画面 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 家具の写真")
    f_file = st.file_uploader("家具をアップロード", type=["jpg", "png", "jpeg"])
    if f_file:
        # 画面表示用
        st.image(f_file, caption="解析対象", width=300)

with col2:
    st.subheader("2. 設定")
    room = st.selectbox("部屋", ["リビング", "ダイニング", "寝室"])
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "和モダン"])
    
    st.divider()
    generate_btn = st.button("✨ 生成スタート", type="primary")

if generate_btn:
    if not f_file:
        st.warning("写真をアップロードしてください")
    else:
        status = st.empty()
        status.info("🚀 AIが画像を解析中... (軽量化モード)")
        
        try:
            # 1. 画像を開いて圧縮（ここで1033を防ぐ）
            original_img = Image.open(f_file)
            small_img = compress_image(original_img)
            
            # 2. プロンプト作成指示
            prompt = f"Describe this furniture shape briefly and write a short English prompt to place it in a {style} {room}. No intro."
            
            # 3. 実行
            response = model.generate_content([prompt, small_img])
            
            # テキストの掃除
            eng_prompt = response.text.replace('\n', ' ').strip()[:300]
            
            status.success("解析完了！画像を描画します...")
            
            # 4. 画像生成 (Pollinations)
            safe_prompt = urllib.parse.quote(eng_prompt)
            img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
            
            # 5. 結果表示
            st.subheader("完成イメージ")
            st.image(img_url, use_container_width=True)
            
            # 予備リンク
            st.markdown(f"[画像が表示されない場合はこちら]({img_url})")
            
        except Exception as e:
            st.error("エラーが発生しました。")
            st.code(f"Error details: {e}")
