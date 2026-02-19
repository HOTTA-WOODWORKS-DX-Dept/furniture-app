import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- ページ設定 ---
st.set_page_config(page_title="Furniture Coordinator Pro", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; padding: 0.5em; }
    .stButton>button:first-child { background-color: #0068C9; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🛋️ 家具コーディネートAI (Pro Edition)")
st.caption("Powered by Gemini 3 Pro Image Preview")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーが設定されていません。StreamlitのSecrets設定を行ってください。")
    st.stop()

# --- モデル設定（リストにあった最新のProモデルを使用） ---
# 画像生成に特化したGemini 3 Proのプレビュー版を指定
MODEL_NAME = 'models/gemini-3-pro-image-preview'

@st.cache_resource
def get_model():
    return genai.GenerativeModel(MODEL_NAME)

try:
    model = get_model()
except Exception as e:
    st.error(f"モデルの読み込みに失敗しました: {e}")
    st.stop()

# --- サイドバー：履歴・管理者（ダミー） ---
with st.sidebar:
    st.header("📜 生成履歴")
    st.info("ここに過去の生成履歴が表示されます")
    st.divider()
    st.caption(f"使用モデル: {MODEL_NAME}")

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
    wood_color = st.selectbox("木部の色を選択", ["指定なし", "ナチュラルオーク", "ウォールナット（濃茶）", "ブラック", "ホワイト", "真鍮・ゴールド"])

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
    generate_btn = st.button("✨ 画像を生成する (Gemini 3 Pro)", type="primary")

# --- 生成ロジック ---
if generate_btn:
    if not furniture_img:
        st.warning("⚠️ 家具の画像をアップロードしてください。")
    else:
        status_text = st.empty()
        status_bar = st.progress(0)
        
        try:
            # プロンプトの構築
            prompt = f"""
            You are an expert interior designer and AI image generator.
            Generate a photorealistic image based on the input image and instructions.

            # Input Image
            - The first image provided is the reference furniture ({furniture_type}).
            - Keep the shape and design of this furniture exactly as it is.

            # Instructions
            - Place this furniture in a {style} style {room_type}.
            - Floor & Wall context: {floor_wall}.
            - Lighting: Professional interior photography lighting, soft natural light.
            - Composition: Wide angle shot showing the room context.
            """
            
            inputs = [prompt, furniture_img]

            # 生地の指定がある場合
            if fabric_img:
                inputs[0] += "\n- Apply the texture and color of the second image (fabric) to the upholstery of the furniture."
                inputs.append(fabric_img)
            
            # 木部の指定がある場合
            if wood_color != "指定なし":
                inputs[0] += f"\n- Change the wood/leg parts color to {wood_color}."

            inputs[0] += "\n- Ensure high quality, realistic textures and shadows."

            status_text.info("🚀 Gemini 3 Pro が画像生成を開始しました... (30〜60秒かかります)")
            status_bar.progress(30)

            # API呼び出し
            response = model.generate_content(inputs)
            
            status_bar.progress(80)
            status_text.info("🎨 画像を処理中...")

            # 画像の取り出しと表示
            # Gemini 3 Pro Image Previewは、response.partsに画像データを含んで返すか、
            # まれにURLを返す場合があります。両方に対応できるように記述します。
            
            try:
                # パターンA: 画像データが直接返ってくる場合
                if hasattr(response, 'parts') and response.parts:
                    for part in response.parts:
                        if hasattr(part, 'image'):
                            # 画像データを表示
                            st.image(part.image, caption="Generated by Gemini 3 Pro", use_container_width=True)
                            st.balloons()
                            status_text.success("生成完了！")
                            break
                        elif hasattr(part, 'inline_data'):
                            # バイナリデータの場合
                            image_bytes = part.inline_data.data
                            img = Image.open(io.BytesIO(image_bytes))
                            st.image(img, caption="Generated by Gemini 3 Pro", use_container_width=True)
                            st.balloons()
                            status_text.success("生成完了！")
                            break
                # パターンB: 通常のテキストとしてURL等が返る場合（念のため）
                elif response.text:
                    st.write(response.text)
                    status_text.success("生成完了（テキスト応答）")
                else:
                    st.error("画像データが見つかりませんでした。")
                    
            except Exception as inner_e:
                # 念のためresponse全体を表示してデバッグできるようにする
                st.error(f"画像の表示中にエラー: {inner_e}")
                st.write(response)

            status_bar.progress(100)

            # ⑧ いいねボタン
            if st.button("❤️ 結果に満足"):
                st.toast("フィードバックを保存しました！")

        except Exception as e:
            st.error(f"生成エラー: {e}")
            st.warning("ヒント: 画像生成モデルは、安全フィルターにより生成が拒否されることがあります。別の角度の写真で試してみてください。")
            
