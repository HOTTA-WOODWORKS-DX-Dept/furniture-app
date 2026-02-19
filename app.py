import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")
st.title("🛋️ Room AI Studio")
st.caption("接続テストOK・モデル名修正済みバージョン")

# --- APIキー設定 ---
try:
    # SecretsからAPIキーを読み込む
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("SecretsにAPIキーが設定されていません。")
        st.stop()
except Exception as e:
    st.error(f"API設定エラー: {e}")
    st.stop()

# --- 【修正点】あなたの環境で確実に動くモデル名 ---
MODEL_NAME = 'models/gemini-flash-latest'
model = genai.GenerativeModel(MODEL_NAME)

# --- 画像圧縮関数（念のための通信対策） ---
def compress_image(image):
    image.thumbnail((500, 500)) # サイズを小さくする
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=70) # 軽量化
    img_byte_arr.seek(0)
    return Image.open(img_byte_arr)

# --- 画面構成 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 家具を決める")
    # タブで「写真」か「文字」か選べるようにする
    tab_photo, tab_text = st.tabs(["📷 写真をアップロード", "✍️ 文字で入力"])
    
    uploaded_file = None
    text_input = ""

    with tab_photo:
        uploaded_file = st.file_uploader("家具の写真", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, width=200)
    
    with tab_text:
        text_input = st.text_input("家具の特徴 (例: 茶色の革製ソファ)", "")

with col2:
    st.subheader("2. 部屋のイメージ")
    room = st.selectbox("部屋", ["リビング", "ダイニング", "寝室", "オフィス"])
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "インダストリアル", "和モダン"])
    
    st.divider()
    generate_btn = st.button("✨ 画像を生成する", type="primary")

# --- 生成実行 ---
if generate_btn:
    status = st.empty()
    status.info("🚀 AIがデザインを考えています...")
    
    try:
        # プロンプト（指示書）の作成
        final_prompt = ""
        
        # A. 写真がある場合
        if uploaded_file:
            img = Image.open(uploaded_file)
            img = compress_image(img) # 軽量化
            prompt = f"Describe this furniture and write a short English prompt to place it in a {style} {room}. No intro."
            response = model.generate_content([prompt, img])
            final_prompt = response.text
            
        # B. 文字がある場合
        elif text_input:
            prompt = f"Write a short English prompt for a photorealistic image of a '{text_input}' placed in a {style} {room}. No intro."
            response = model.generate_content(prompt)
            final_prompt = response.text
            
        else:
            st.warning("写真か文字、どちらかを入力してください")
            st.stop()

        # プロンプトの掃除（改行などを消す）
        clean_prompt = final_prompt.replace('\n', ' ').strip()[:400]
        
        # 画像生成 (Pollinations)
        status.success("描画中...")
        encoded = urllib.parse.quote(clean_prompt)
        # 毎回違う画像が出るようにseedに時間を使う
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
        
        # 結果表示
        st.subheader("完成イメージ")
        st.image(img_url, use_container_width=True)
        st.markdown(f"🔗 [画像が表示されない場合はここをクリック]({img_url})")
        
    except Exception as e:
        st.error("エラーが発生しました")
        st.code(f"詳細: {e}")
