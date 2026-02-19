import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Furniture Coordinator", layout="wide")
st.title("🛋️ 家具コーディネートAI (DX事業部)")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーが設定されていません。")
    st.stop()

# --- 【修正版】使えるモデルを自動で探す ---
def get_available_model():
    """今使えるモデルを探して返す"""
    try:
        # 1. まずは最新のFlashを試す
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        try:
            # 2. ダメならProを試す
            return genai.GenerativeModel('gemini-1.5-pro')
        except:
            # 3. それでもダメなら旧モデル(Vision)を試す
            return genai.GenerativeModel('gemini-pro-vision')

model = get_available_model()

# --- デバッグ表示（何を使っているか確認） ---
# st.caption(f"使用中のAIモデル: {model._model_name}") # エラー回避のためコメントアウト

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 画像入力")
    uploaded_file = st.file_uploader("家具の画像をアップロード", type=["jpg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

with col2:
    st.subheader("2. 生成")
    room = st.selectbox("部屋", ["リビング", "寝室", "オフィス"])
    if st.button("生成スタート"):
        if uploaded_file:
            with st.spinner("生成中..."):
                try:
                    # シンプルなプロンプトで実行
                    prompt = f"この家具を{room}に置いたイメージ画像を生成してください。"
                    response = model.generate_content([prompt, image])
                    st.write(response.text)
                    st.success("指示の生成に成功しました")
                except Exception as e:
                    st.error(f"エラー詳細: {e}")
                    st.write("対策: requirements.txtのバージョンを確認してください")
