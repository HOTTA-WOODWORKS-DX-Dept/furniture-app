import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# --- ページ設定 ---
st.set_page_config(page_title="Furniture AI Coordinator", layout="wide")

st.title("🛋️ 家具コーディネートAI (Stable Link)")
st.caption("最新の安定版モデルを自動認識して実行します")

# --- APIキー設定 ---
try:
    # SecretsからAPIキーを取得
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ APIキーが設定されていません。Streamlit CloudのSettings > Secretsを確認してください。")
    st.stop()

# --- モデル設定（診断リストにあった 'gemini-flash-latest' を直接指定） ---
# これにより 1.5 や 2.0 といった数字の指定ミスによる404エラーを回避します
MODEL_NAME = 'models/gemini-flash-latest'

@st.cache_resource
def get_model():
    try:
        return genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        st.error(f"モデルの起動に失敗しました: {e}")
        return None

model = get_model()

# --- メインエリア ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 家具・素材の登録")
    furniture_file = st.file_uploader("家具の写真", type=["jpg", "png", "jpeg"])
    fabric_file = st.file_uploader("生地の写真（任意）", type=["jpg", "png", "jpeg"])
    
    if furniture_file:
        st.image(Image.open(furniture_file), caption="対象家具", use_container_width=True)

with col2:
    st.subheader("2. 空間デザイン設定")
    room = st.selectbox("配置する部屋", ["リビング", "ダイニング", "寝室", "子供部屋", "書斎"])
    style = st.selectbox("デザインテイスト", ["北欧モダン", "ヴィンテージ", "インダストリアル", "和モダン", "シンプル"])
    
    st.divider()
    if st.button("✨ 画像を生成する", type="primary"):
        if not furniture_file:
            st.warning("家具の写真をアップロードしてください。")
        elif model is None:
            st.error("AIモデルが準備できていません。")
        else:
            with st.spinner("AIが空間をコーディネート中..."):
                try:
                    # 1. Geminiに家具を分析させ、プロンプトを生成させる
                    img = Image.open(furniture_file)
                    prompt_text = f"この家具のデザインを維持しつつ、{style}なスタイルの{room}に配置した高品質なインテリア写真の画像生成プロンプトを英語で1つ作成してください。出力はプロンプトのみ。説明不要。"
                    
                    content = [prompt_text, img]
                    if fabric_file:
                        content.append(Image.open(fabric_file))
                    
                    # 生成実行
                    response = model.generate_content(content)
                    eng_prompt = response.text
                    
                    # 2. 画像生成エンジン(Pollinations)で描画
                    # 文字数制限とエンコード処理
                    safe_prompt = urllib.parse.quote(eng_prompt[:500])
                    image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=768&nologo=true&seed=42&model=flux"
                    
                    # 結果表示
                    st.image(image_url, caption=f"{style}スタイルの提案", use_container_width=True)
                    st.success("コーディネートが完成しました！")
                    
                    with st.expander("AIの分析詳細"):
                        st.write(eng_prompt)
                    
                except Exception as e:
                    st.error(f"実行エラー: {e}")
                    st.info("ヒント: 一度アプリをRebootしてから再度お試しください。")
