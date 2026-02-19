import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")
st.title("🛋️ Room AI Studio")
st.caption("通信軽量化・モデル名修正済みバージョン")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ SecretsにAPIキーを設定してください。")
    st.stop()

# --- 【修正点1】あなたのリストに確実に存在するモデル名を使用 ---
MODEL_NAME = 'models/gemini-flash-latest'

@st.cache_resource
def get_model():
    return genai.GenerativeModel(MODEL_NAME)

try:
    model = get_model()
except Exception as e:
    st.error(f"モデル設定エラー: {e}")
    st.stop()

# --- 【修正点2】通信エラー(1033)を防ぐ強力なリサイズ関数 ---
def compress_image(uploaded_file):
    if uploaded_file is None:
        return None
    img = Image.open(uploaded_file)
    # 1033エラー対策：サイズを512pxまで小さくする（AIの認識には十分です）
    img.thumbnail((512, 512)) 
    return img

# --- メイン画面 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 家具の写真")
    f_file = st.file_uploader("家具をアップロード", type=["jpg", "png", "jpeg"])
    if f_file:
        # 画面表示用には少し綺麗に見せる
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
        status.info("🚀 AIが画像を解析中... (通信負荷を下げて実行中)")
        
        try:
            # 1. 画像を圧縮してGeminiに送信
            small_img = compress_image(f_file)
            
            # プロンプト作成指示
            prompt = f"Describe this furniture and place it in a {style} {room}. Output a short English prompt for image generation. No intro."
            
            # 実行
            response = model.generate_content([prompt, small_img])
            eng_prompt = response.text.replace('\n', ' ').strip()[:300]
            
            status.success("解析完了！画像を描画します...")
            
            # 2. 画像生成 (Pollinations)
            safe_prompt = urllib.parse.quote(eng_prompt)
            img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
            
            # 3. 結果表示
            st.subheader("完成イメージ")
            st.image(img_url, use_container_width=True)
            
            # もし画像が出ない場合の予備リンク
            st.markdown(f"[画像が表示されない場合はこちらをクリック]({img_url})")
            
        except Exception as e:
            st.error("エラーが発生しました。")
            st.code(f"Error details: {e}")
            if "404" in str(e):
                st.info("モデル名が見つかりません。'models/gemini-flash-latest' が無効の可能性があります。")
            elif "429" in str(e):
                st.info("APIの無料枠制限(Quota)です。時間を空けるか、APIキーを変更してください。")
