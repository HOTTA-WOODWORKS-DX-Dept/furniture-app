import streamlit as st
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel, Image as VertexImage
from google.oauth2 import service_account
import json
from PIL import Image as PILImage
import io

# ページ設定
st.set_page_config(page_title="AIソファ・リデコレーター", layout="centered")

st.title("🛋️ AIソファ・リデコレーター")
st.write("Google Cloud Vertex AI (Imagen 2) を使用して、ソファの生地と部屋を張り替えます。")

# --- 1. 認証と初期化 (ここが最重要) ---
# Streamlit CloudのSecretsからJSONキーを読み込み、認証を通します。
try:
    if "gcp_key_json" in st.secrets:
        # SecretsからJSON文字列を取得して辞書に変換
        key_info = json.loads(st.secrets["gcp_key_json"])
        
        # 認証情報(Credentials)オブジェクトを作成
        creds = service_account.Credentials.from_service_account_info(key_info)
        
        # プロジェクトIDをJSONから自動取得
        project_id = key_info["project_id"]
        
        # Vertex AIを初期化 (credentialsを明示的に渡すことでTimeoutエラーを防ぐ)
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
        uploaded_mask = st.file_uploader("変更エリア(白)を指定した画像", type=["jpg", "png", "jpeg"])
        st.caption("※白の部分が書き換わります。")

    st.subheader("3. デザインの指示 (プロンプト)")
    prompt_text = st.text_area(
        "英語で詳しく指示してください", 
        value="A modern sofa upholstered in green striped fabric, placed in a modern minimal living room with dark wooden floor and white walls, photorealistic, 8k, interior design photography",
        height=100
    )
    
    negative_prompt = st.text_input(
        "除外したい要素 (Negative Prompt)", 
        value="low quality, blurry, distorted, watermark, text, cartoon, illustration"
    )

    submitted = st.form_submit_button("🎨 画像を生成する", use_container_width=True)

# --- 3. 画像生成処理 ---

if submitted:
    if uploaded_sofa and uploaded_mask and prompt_text:
        status_container = st.empty() # 進捗表示用
        
        try:
            status_container.info("🚀 AIモデルを起動中...")
            
            # 画像をVertex AI用に読み込み
            sofa_bytes = uploaded_sofa.getvalue()
            mask_bytes = uploaded_mask.getvalue()
            
            vertex_sofa_img = VertexImage(image_bytes=sofa_bytes)
            vertex_mask_img = VertexImage(image_bytes=mask_bytes)

            # モデルのロード (Imagen 2)
            model = ImageGenerationModel.from_pretrained("imagegeneration@005")

            status_container.info("🎨 画像を描画中... (20〜40秒ほどかかります)")

            # 生成実行 (edit_image)
            generated_images = model.edit_image(
                base_image=vertex_sofa_img,
                mask=vertex_mask_img,
                prompt=prompt_text,
                negative_prompt=negative_prompt,
                guidance_scale=60, # プロンプトへの忠実度 (大きいほど指示に従う)
                number_of_images=1
            )

            # 結果の表示
            status_container.success("✨ 完成しました！")
            
            # 生成された画像を表示
            result_image = generated_images[0]
            
            # UIに表示
            st.image(result_image._image_bytes, caption="AIによる生成結果", use_column_width=True)

            # ダウンロードボタンの作成
            # VertexImageをPIL経由でバイト列に戻してダウンロード可能にする
            pil_img = PILImage.open(io.BytesIO(result_image._image_bytes))
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            byte_im = buf.getvalue()

            st.download_button(
                label="📥 画像をダウンロード",
                data=byte_im,
                file_name="ai_generated_sofa.png",
                mime="image/png"
            )

        except Exception as e:
            status_container.error(f"生成中にエラーが発生しました: {e}")
            st.error("ヒント: プロンプトがポリシー違反（有名人の名前など）の場合や、サーバー混雑時にもエラーが出ることがあります。")
            
    else:
        st.warning("⚠️ 画像2枚とプロンプトをすべて入力してください。")
