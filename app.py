import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import time

# --- ページ設定 ---
st.set_page_config(page_title="Furniture AI Coordinator", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; padding: 0.8em; background-color: #0068C9; color: white; }
    .main-img { border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

st.title("🛋️ 家具コーディネートAI")
st.caption("Gemini 2026 Edition - 堀田木工所 DX事業部プロトタイプ")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ SecretsにAPIキーを設定してください。")
    st.stop()

# --- モデル設定（安定版を使用） ---
MODEL_NAME = 'models/gemini-flash-latest'
model = genai.GenerativeModel(MODEL_NAME)

# --- メインエリア ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. 家具・素材の登録")
    furniture_file = st.file_uploader("家具の写真（スマホで撮影）", type=["jpg", "png", "jpeg"])
    fabric_file = st.file_uploader("生地の写真（任意）", type=["jpg", "png", "jpeg"])
    
    if furniture_file:
        st.image(Image.open(furniture_file), caption="解析対象の家具", use_container_width=True)

with col2:
    st.subheader("2. 空間デザイン設定")
    room = st.selectbox("配置する部屋", ["リビングルーム", "ダイニング", "ベッドルーム", "子供部屋", "書斎"])
    style = st.selectbox("デザインテイスト", ["北欧モダン", "ヴィンテージ", "インダストリアル", "和モダン", "シンプル"])
    
    st.divider()
    if st.button("✨ この設定で画像を生成する"):
        if not furniture_file:
            st.warning("家具の写真をアップロードしてください。")
        else:
            with st.spinner("AIが空間をデザインしています..."):
                try:
                    # 1. Geminiにプロンプトを作成させる
                    img = Image.open(furniture_file)
                    prompt_text = f"この家具のデザインを忠実に再現し、{style}な{room}に配置した高品質なインテリア写真のプロンプトを英語で作成してください。出力はプロンプトのみ。説明不要。"
                    
                    content = [prompt_text, img]
                    if fabric_file:
                        content.append(Image.open(fabric_file))
                    
                    response = model.generate_content(content)
                    # プロンプトを整理（改行などを消してURLを壊さないようにする）
                    eng_prompt = response.text.replace('\n', ' ').strip()
                    
                    # 2. 画像生成エンジンへ送信
                    # 安全のために長さを制限し、URLエンコードする
                    safe_prompt = urllib.parse.quote(eng_prompt[:400])
                    # 画像URLを生成（seedをランダムにして毎回違う画像にする）
                    random_seed = int(time.time())
                    image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=768&nologo=true&seed={random_seed}&model=flux"
                    
                    # 3. 結果の表示
                    st.subheader("🖼️ 生成されたコーディネート案")
                    # 画像本体を表示
                    st.image(image_url, caption=f"{style}スタイルの提案", use_container_width=True)
                    
                    # 万が一、ブラウザの制限で画像が表示されない時用のバックアップリンク
                    st.markdown(f"🔗 [画像をフルサイズで開く]({image_url})")
                    
                    st.success("コーディネートが完成しました！")
                    
                    with st.expander("AIによるコーディネートの解説（英文プロンプト）"):
                        st.write(eng_prompt)
                        
                    # ⑧ いいねボタン
                    if st.button("❤️ このコーディネートを保存"):
                        st.toast("お気に入り登録しました！")
                    
                except Exception as e:
                    st.error(f"生成中にエラーが発生しました。時間を置いて再度お試しください。")
                    st.caption(f"Error detail: {e}")
                    
