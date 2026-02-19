import streamlit as st
import vertexai
from vertexai.vision_models import ImageGenerationModel, Image as VertexImage
from google.oauth2 import service_account
import json
from PIL import Image as PILImage
import io

# ページ設定
st.set_page_config(page_title="AIソファ・リデコレーター v3", layout="centered")

st.title("🛋️ AIソファ・リデコレーター (Imagen 3対応)")
st.write("最新の Imagen 3 モデルを使用して、ソファの張り替えを行います。")

# --- 1. 認証と初期化 ---
try:
    if "gcp_key_json" in st.secrets:
        key_info = json.loads(st.secrets["gcp_key_json"])
        creds = service_account.Credentials.from_service_account_info(key_info)
        project_id = key_info["project_id"]
        # locationはモデルが対応している us-central1 を指定
        vertexai.init(project=project_id, location="us-central1", credentials=creds)
        st.success("✅ Google Cloud 認証成功")
    else:
        st.error("エラー: Secretsに 'gcp_key_json' が設定されていません。")
        st.stop()
except Exception as e:
    st.error(f"認証設定エラー: {e}")
    st.stop()

# --- 2. ユーザー入力フォーム ---
with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. 元画像 (ソファ)")
        uploaded_sofa = st.file_uploader("ソファの写真をアップロード", type=["jpg", "png", "jpeg"])
    with col2:
        st.subheader("2. マスク画像")
        uploaded_mask = st.file_uploader("変更エリア(白)を指定", type=["jpg", "png", "jpeg"])

    st.subheader("3. デザインの指示")
    prompt_text = st.text_area(
        "英語で指示してください", 
        value="A high-quality photo of a sofa upholstered in green striped fabric, placed in a modern minimal living room with dark wooden floor and white walls, 8k, interior design style",
        height=100
    )
    
    submitted = st.form_submit_button("🎨 最新AIで画像を生成する", use_container_width=True)

# --- 3. 画像生成処理 ---
if submitted:
    if uploaded_sofa and uploaded_mask and prompt_text:
        status = st.empty()
        try:
            status.info("🚀 最新モデル Imagen 3 を起動中...")
            
            # 画像データの変換
            vertex_sofa_img = VertexImage(image_bytes=uploaded_sofa.getvalue())
            vertex_mask_img = VertexImage(image_bytes=uploaded_mask.getvalue())

            # === 修正ポイント: 最新の Imagen 3 モデルを指定 ===
            model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

            status.info("🎨 画像を描画中... (しばらくお待ちください)")

            # Imagen 3 用の編集（Inpainting）実行
            # ※旧モデルにあった guidance_scale は削除し、シンプルに設定します
            generated_images = model.edit_image(
                base_image=vertex_sofa_img,
                mask=vertex_mask_img,
                prompt=prompt_text,
                number_of_images=1,
            )

            # 結果表示
            status.success("✨ 完成しました！")
            result_bytes = generated_images[0]._image_bytes
            st.image(result_bytes, caption="Imagen 3 による生成結果", use_column_width=True)

            # ダウンロードボタン
            st.download_button(
                label="📥 画像をダウンロード",
                data=result_bytes,
                file_name="imagen3_sofa.png",
                mime="image/png"
            )

        except Exception as e:
            status.error(f"生成エラーが発生しました: {e}")
            st.write("詳細デバッグ情報:", e) # エラー内容を詳しく表示
            
    else:
        st.warning("⚠️ 画像2枚とプロンプトを入力してください。")
