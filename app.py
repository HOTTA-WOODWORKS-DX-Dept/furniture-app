import streamlit as st
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel, Image
import io
from PIL import Image as PILImage

# ページ設定
st.title("🛋️ AIソファ・リデコレーター")
st.write("ソファの画像とマスク（変更したい部分）をアップして、新しい生地を指示してください。")

# Google Cloud設定 (Streamlit CloudのSecretsから読み込む設定)
# プロジェクトIDとロケーションはご自身のものに合わせてください
PROJECT_ID = st.secrets["GCP_PROJECT_ID"]
LOCATION = "us-central1"

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"GCP接続エラー: {e}")

# 画像アップロード
uploaded_sofa = st.file_uploader("1. ソファの画像をアップロード", type=["jpg", "png"])
uploaded_mask = st.file_uploader("2. マスク画像をアップロード（変更箇所が白、他が黒）", type=["jpg", "png"])
text_prompt = st.text_input("3. どんな生地・部屋にしますか？（英語推奨）", "A sofa with green striped fabric in a modern minimal room")

if st.button("画像生成スタート"):
    if uploaded_sofa and uploaded_mask and text_prompt:
        with st.spinner('AIがデザイン中...（20〜30秒かかります）'):
            try:
                # 画像の読み込みと変換
                sofa_img = Image(image_bytes=uploaded_sofa.getvalue())
                mask_img = Image(image_bytes=uploaded_mask.getvalue())

                # モデルのロード (Imagen 2 または 3)
                model = ImageGenerationModel.from_pretrained("imagegeneration@006")

                # 生成実行
                generated_images = model.edit_image(
                    base_image=sofa_img,
                    mask=mask_img,
                    prompt=text_prompt,
                    edit_mode="inpainting-insert",
                )

                # 結果表示
                st.success("完成しました！")
                st.image(generated_images[0]._image_bytes, caption="生成された画像")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    else:
        st.warning("画像とプロンプトを全て入力してください。")
