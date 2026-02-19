import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# --- ページ設定 ---
st.set_page_config(page_title="Furniture AI Coordinator", layout="wide")

st.title("🛋️ 家具コーディネートAI (Stable Version)")
st.caption("最も安定した Gemini 1.5 Flash を使用しています")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーが設定されていません。StreamlitのSecretsを確認してください。")
    st.stop()

# --- モデル設定（無料枠が最も安定している 1.5 Flash を指定） ---
# 2.0がエラー(Limit 0)になるため、確実な 1.5 を使用します
MODEL_NAME = 'gemini-1.5-flash'

@st.cache_resource
def get_model():
    return genai.GenerativeModel(MODEL_NAME)

model = get_model()

# --- メインエリア ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 素材の登録")
    furniture_file = st.file_uploader("家具の画像", type=["jpg", "png", "jpeg"])
    fabric_file = st.file_uploader("生地の画像（任意）", type=["jpg", "png", "jpeg"])
    
    if furniture_file:
        img = Image.open(furniture_file)
        st.image(img, caption="対象家具", use_container_width=True)

with col2:
    st.subheader("2. 空間の設定")
    room = st.selectbox("部屋の種類", ["リビングルーム", "ダイニング", "寝室", "子供部屋", "書斎"])
    style = st.selectbox("テイスト", ["北欧モダン", "ヴィンテージ", "インダストリアル", "和モダン", "シンプル"])
    
    st.divider()
    if st.button("✨ コーディネート画像を生成", type="primary"):
        if not furniture_file:
            st.warning("家具画像をアップロードしてください")
        else:
            with st.spinner("AIがコーディネート案を作成中..."):
                try:
                    # 1. Gemini 1.5 Flashに指示書（プロンプト）を書かせる
                    furniture_img = Image.open(furniture_file)
                    prompt_msg = f"この家具を{style}な{room}に配置した、おしゃれなインテリア写真の画像生成プロンプトを英語で作成してください。家具の形は維持してください。説明は不要です。"
                    
                    content = [prompt_msg, furniture_img]
                    if fabric_file:
                        content.append(Image.open(fabric_file))
                    
                    # 実行
                    response = model.generate_content(content)
                    eng_prompt = response.text
                    
                    # 2. 画像生成エンジン(Pollinations)で描画
                    # Fluxという最新モデルを指定して高画質化します
                    encoded_prompt = urllib.parse.quote(eng_prompt[:500])
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed=42&model=flux"
                    
                    st.image(image_url, caption="生成されたコーディネート画像", use_container_width=True)
                    st.success("成功しました！")
                    
                    with st.expander("AIの指示内容を確認"):
                        st.write(eng_prompt)
                    
                except Exception as e:
                    st.error(f"生成エラーが発生しました。申し訳ありません。")
                    st.info(f"エラー詳細: {e}")
