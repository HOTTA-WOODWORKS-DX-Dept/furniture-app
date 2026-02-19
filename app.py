import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# --- ページ設定 ---
st.set_page_config(page_title="Furniture Coordinator 2026", layout="wide")

st.title("🛋️ 家具コーディネートAI")
st.caption("最新の無料モデルを自動選択して生成します")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーが設定されていません。")
    st.stop()

# --- 【重要】エラー回避用：利用可能な無料モデルを自動選択 ---
@st.cache_resource
def get_safe_model():
    # 優先順位：2.0 Flash > 1.5 Flash > 1.5 Pro
    # ※ 3-pro-image はエラーになるのでリストから除外しています
    candidate_models = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    for model_name in candidate_models:
        try:
            m = genai.GenerativeModel(model_name)
            # テスト的に名前を取得
            return m, model_name
        except:
            continue
    return None, None

model, active_model_name = get_safe_model()

if not model:
    st.error("利用可能なモデルが見つかりません。")
    st.stop()

# --- メイン画面 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 素材の登録")
    furniture_file = st.file_uploader("家具の画像", type=["jpg", "png", "jpeg"])
    fabric_file = st.file_uploader("生地の画像（任意）", type=["jpg", "png", "jpeg"])
    
    if furniture_file:
        st.image(Image.open(furniture_file), caption="対象家具", use_container_width=True)

with col2:
    st.subheader("2. 空間の設定")
    room = st.selectbox("部屋の種類", ["リビング", "ダイニング", "寝室", "子供部屋"])
    style = st.selectbox("テイスト", ["北欧モダン", "ヴィンテージ", "インダストリアル", "ジャパンディ"])
    
    st.divider()
    if st.button("✨ コーディネート画像を生成", type="primary"):
        if not furniture_file:
            st.warning("家具画像をアップロードしてください")
        else:
            with st.spinner(f"AI({active_model_name})が分析中..."):
                try:
                    # 1. Geminiに指示書（プロンプト）を書かせる
                    furniture_img = Image.open(furniture_file)
                    prompt_msg = f"この家具を{style}な{room}に配置するための、詳細な英語の画像生成プロンプトを作成してください。説明は不要です。"
                    
                    content = [prompt_msg, furniture_img]
                    if fabric_file:
                        content.append(Image.open(fabric_file))
                    
                    response = model.generate_content(content)
                    eng_prompt = response.text
                    
                    # 2. 画像生成エンジン(Pollinations)で描画
                    encoded_prompt = urllib.parse.quote(eng_prompt[:500])
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&model=flux"
                    
                    st.image(image_url, caption="生成されたコーディネート", use_container_width=True)
                    st.success("成功しました！")
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
