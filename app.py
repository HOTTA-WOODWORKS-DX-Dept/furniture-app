import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# --- ページ設定 ---
st.set_page_config(page_title="Furniture Coordinator 2.0", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; padding: 0.5em; }
    .stButton>button:first-child { background-color: #0068C9; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🛋️ 家具コーディネートAI (Gemini 2.0)")
st.caption("Powered by Gemini 2.0 Flash (Vision) + AI Image Generator")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーが設定されていません。StreamlitのSecrets設定を行ってください。")
    st.stop()

# --- モデル設定（確実に動くGemini 2.0 Flashを使用） ---
# このモデルは画像を「見る」能力が非常に高いです
MODEL_NAME = 'gemini-2.0-flash'

@st.cache_resource
def get_model():
    return genai.GenerativeModel(MODEL_NAME)

try:
    model = get_model()
except Exception as e:
    st.error(f"モデルの読み込みに失敗しました: {e}")
    st.stop()

# --- メインエリア ---
col1, col2 = st.columns([1, 1.2])

# 【左カラム】入力エリア
with col1:
    st.subheader("1. 家具と素材")
    
    # ① 家具画像（必須）
    st.write("▼ ベースとなる家具")
    furniture_file = st.file_uploader("家具をアップロード", type=["jpg", "png", "jpeg"], key="fur")
    furniture_img = None
    if furniture_file:
        furniture_img = Image.open(furniture_file)
        st.image(furniture_img, use_container_width=True)

    # ③ メイン生地（任意）
    st.write("▼ 生地の素材感（張り地など）")
    fabric_file = st.file_uploader("生地画像をアップロード（任意）", type=["jpg", "png", "jpeg"], key="fab")
    fabric_img = None
    if fabric_file:
        fabric_img = Image.open(fabric_file)
        st.image(fabric_img, width=150)
        
    # ④ 木部・サブカラー（任意）
    st.write("▼ 木部・脚の色（任意）")
    wood_color = st.selectbox("木部の色を選択", ["元のまま", "ナチュラルオーク", "ウォールナット（濃茶）", "ブラック", "ホワイト", "真鍮・ゴールド"])

# 【右カラム】設定と生成エリア
with col2:
    st.subheader("2. コーディネート設定")
    
    # ② 家具の種類
    furniture_type = st.text_input("家具の種類（例：3人掛けソファ、ダイニングチェア）", value="家具")

    # ⑤ 部屋の選択
    room_type = st.selectbox("置きたい部屋", ["リビングルーム", "ダイニングルーム", "ベッドルーム", "書斎", "子供部屋", "カフェのラウンジ"])

    # ⑥ テイストと内装
    c1, c2 = st.columns(2)
    with c1:
        style = st.selectbox("インテリアテイスト", ["北欧モダン", "シンプルモダン", "ヴィンテージ", "インダストリアル", "ジャパンディ（和モダン）", "ラグジュアリー"])
    with c2:
        floor_wall = st.selectbox("床と壁の雰囲気", ["明るいフローリングと白壁", "ダークな床とグレーの壁", "コンクリート打ちっぱなし", "畳と塗り壁"])

    # ⑦ 生成実行
    st.divider()
    generate_btn = st.button("✨ 画像を生成する", type="primary")

# --- 生成ロジック ---
if generate_btn:
    if not furniture_img:
        st.warning("⚠️ 家具の画像をアップロードしてください。")
    else:
        status_text = st.empty()
        status_bar = st.progress(0)
        
        try:
            # 1. Gemini 2.0 Flash に「画像を見てプロンプトを書かせる」
            status_text.info("👀 Gemini 2.0 が家具と生地を観察中...")
            
            prompt_instruction = f"""
            You are an expert interior designer.
            Look at the input images and create a detailed English image generation prompt to visualize the final scene.

            # Input Images
            1. The first image is the main furniture ({furniture_type}).
            2. (Optional) The second image is the fabric/texture to be applied to the furniture.

            # Task
            Describe the scene where this furniture is placed in a {style} style {room_type}.
            
            # Details to include in the prompt:
            - **Furniture:** Describe the furniture shape based on the first image.
            - **Material:** If the second image exists, describe its color and texture (e.g., velvet, linen, leather) and apply it to the furniture.
            - **Wood Color:** The legs/frame should be {wood_color}.
            - **Room Context:** {floor_wall}.
            - **Lighting & Vibe:** Photorealistic, 8k, interior design magazine quality, cinematic lighting.
            
            Output ONLY the English prompt. No explanations.
            """
            
            inputs = [prompt_instruction, furniture_img]
            if fabric_img:
                inputs.append(fabric_img)
            
            # Gemini実行
            response = model.generate_content(inputs)
            generated_prompt = response.text
            
            status_bar.progress(50)
            status_text.info("🎨 画像を描画中...")
            print(f"Prompt: {generated_prompt}") # デバッグ用

            # 2. 生成されたプロンプトを使って画像を表示 (Pollinations API)
            # URLエンコード（文字をURLで使える形式に変換）
            encoded_prompt = urllib.parse.quote(generated_prompt[:400]) # 長すぎるとエラーになるので調整
            
            # 画像URLを作成（ここが画像生成エンジンになります）
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed=123&model=flux"
            
            # 表示
            st.image(image_url, caption=f"Generated: {style} style {room_type}", use_container_width=True)
            
            status_bar.progress(100)
            status_text.success("生成完了！")
            
            with st.expander("AIが作成した指示書（プロンプト）を見る"):
                st.write(generated_prompt)
                
            # ⑧ いいねボタン
            if st.button("❤️ 結果に満足"):
                st.toast("フィードバックを保存しました！")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.warning("ヒント: 一時的な通信エラーの可能性があります。もう一度ボタンを押してみてください。")
