import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")

# デザイン：堀田木工所様のDXツールらしい、清潔感のあるスタイル
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #1E3A8A; color: white; }
    .main-img { border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    .stSelectbox label { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🛋️ Room AI Studio")
st.caption("AIが提案する、理想のインテリアコーディネート")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーを設定してください。")
    st.stop()

# --- 通信エラー対策：画像リサイズ関数 ---
def prepare_image(uploaded_file):
    if uploaded_file is None:
        return None
    img = Image.open(uploaded_file)
    img.thumbnail((800, 800)) # 1033エラーを防ぐための軽量化
    return img

# --- モデル設定（成功した 'gemini-flash-latest' を使用） ---
MODEL_NAME = 'gemini-flash-latest'
model = genai.GenerativeModel(MODEL_NAME)

# --- 画面レイアウト ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. 家具と素材を読み込む")
    # 家具画像
    f_file = st.file_uploader("家具の写真をアップロード", type=["jpg", "jpeg", "png"])
    if f_file:
        st.image(prepare_image(f_file), caption="解析対象", use_container_width=True)
    
    # 生地・素材画像
    fabric_file = st.file_uploader("生地・素材の写真（任意）", type=["jpg", "jpeg", "png"])
    if fabric_file:
        st.image(prepare_image(fabric_file), width=150, caption="適用する素材")

with col2:
    st.subheader("2. お部屋をコーディネート")
    room = st.selectbox("配置する部屋", ["リビングルーム", "ダイニングルーム", "ベッドルーム", "書斎/オフィス", "子供部屋"])
    style = st.selectbox("インテリアテイスト", ["北欧モダン", "ジャパンディ(和モダン)", "ヴィンテージ", "インダストリアル", "ラグジュアリー"])
    
    st.write("▼ 追加設定")
    c1, c2 = st.columns(2)
    with c1:
        floor = st.selectbox("床材", ["ナチュラルオーク", "ウォールナット", "ホワイトタイル", "グレーコンクリート"])
    with c2:
        wall = st.selectbox("壁紙", ["プレーンホワイト", "ライトグレー", "ベージュ", "アクセントブルー"])

    st.divider()
    generate_btn = st.button("✨ この設定でイメージを生成する")

# --- 生成処理 ---
if generate_btn:
    if not f_file:
        st.warning("家具の写真をアップロードしてください。")
    else:
        with st.spinner("AIが空間をデザイン中..."):
            try:
                # 1. Geminiに解析とプロンプト作成を依頼
                img = prepare_image(f_file)
                prompt_msg = f"""
                You are a professional interior designer. 
                Analyze the furniture in the image and create an English image generation prompt.
                Action: Place this furniture into a {style} {room}.
                Context: {floor} floor, {wall} walls.
                Instructions: Keep the furniture shape and color. Photorealistic, 8k, natural soft lighting.
                Output ONLY the English prompt.
                """
                
                content = [prompt_msg, img]
                if fabric_file:
                    content.append(prepare_image(fabric_file))
                
                response = model.generate_content(content)
                eng_prompt = response.text.replace('\n', ' ').strip()
                
                # 2. 画像生成（Pollinations AI）
                safe_prompt = urllib.parse.quote(eng_prompt[:400])
                # 毎回違う結果にするためにseedに時間を使用
                img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
                
                # 3. 結果表示
                st.subheader("🖼️ 生成された提案イメージ")
                st.image(img_url, use_container_width=True)
                
                st.success("コーディネートが完了しました！")
                
                with st.expander("AIによるデザイン解説（英文プロンプト）"):
                    st.write(eng_prompt)

            except Exception as e:
                st.error(f"エラーが発生しました。時間を置いて再度お試しください。")
                st.caption(f"Detail: {e}")
