import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# --- 設定 ---
st.set_page_config(page_title="Furniture Coordinator", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🛋️ 家具コーディネートAI (DX事業部)")

# --- APIキーの確認 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ APIキーが設定されていません。StreamlitのSecrets設定を行ってください。")
    st.stop()

# --- サイドバー：管理者メニュー ---
with st.sidebar:
    st.header("管理者メニュー")
    admin_password = st.text_input("パスワード", type="password")
    if admin_password == "dx2026":  # 仮のパスワード
        st.success("ログイン成功")
        st.write("ここに生成ログを表示します（今後実装）")

# --- メイン画面 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 素材の登録")
    
    # 家具画像
    st.write("▼ 家具本体（形を使います）")
    input_furniture = st.file_uploader("家具をアップロード", type=["jpg", "png"], key="fur")
    furniture_img = None
    if input_furniture:
        furniture_img = Image.open(input_furniture)
        st.image(furniture_img, use_container_width=True)

    # 生地画像
    st.write("▼ 生地/マテリアル（色・質感を反映）")
    input_fabric = st.file_uploader("生地をアップロード（任意）", type=["jpg", "png"], key="fab")
    fabric_img = None
    if input_fabric:
        fabric_img = Image.open(input_fabric)
        st.image(fabric_img, width=150)

with col2:
    st.subheader("2. 空間設定")
    
    room_type = st.selectbox("部屋の種類", ["リビング", "ダイニング", "寝室", "子供部屋", "書斎/オフィス"])
    style = st.selectbox("インテリアテイスト", ["北欧モダン", "ヴィンテージ", "ジャパニーズモダン", "インダストリアル", "ラグジュアリー"])
    
    st.write("▼ 詳細設定")
    c1, c2 = st.columns(2)
    with c1:
        floor = st.selectbox("床の色", ["オーク（ナチュラル）", "ウォールナット（濃茶）", "ホワイト", "コンクリート"])
    with c2:
        wall = st.selectbox("壁の色", ["ホワイト", "グレー", "ベージュ", "アクセントクロス（ブルー）"])

    st.write("---")
    
    # 生成ボタン
    generate_btn = st.button("✨ コーディネート画像を生成する")

# --- 生成ロジック ---
if generate_btn:
    if not furniture_img:
        st.warning("まずは「家具の画像」をアップロードしてください。")
    else:
        status_text = st.empty()
        status_text.info("🤖 AIが画像を分析中...")
        
        try:
            # 1. Geminiを使って画像を分析し、プロンプトを作成させる
            # Gemini 1.5 Flashを使用（高速・軽量）
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # AIへの命令
            prompt = f"""
            あなたはプロのインテリアコーディネーターです。
            与えられた家具画像（および生地画像）を分析し、指定された部屋に配置したシーンを描画するための「英語の画像生成プロンプト」を作成してください。
            
            # 条件
            - 家具: 画像の家具の形状を維持する。
            - マテリアル: 生地の画像がある場合は、その質感と色を家具に適用する。
            - 部屋: {style}な{room_type}。
            - 床: {floor}
            - 壁: {wall}
            - アングル: 部屋全体が見え、家具が魅力的に見えるアングル。
            - 照明: 自然光が入る明るく魅力的な雰囲気。
            
            出力は「画像生成用の英語プロンプト」のみを記述してください。説明は不要です。
            """
            
            inputs = [prompt, furniture_img]
            if fabric_img:
                inputs.append(fabric_img)
            
            # 分析実行
            response = model.generate_content(inputs)
            image_prompt = response.text
            
            status_text.info("🎨 画像を描画中...")
            
            # 2. 生成されたプロンプトを使って画像を表示
            # （プロトタイプのため、URLベースの高速生成API "Pollinations" を使用して表示します）
            # ※本番開発ではGoogle ImagenやStable Diffusion APIに置き換えます
            
            encoded_prompt = urllib.parse.quote(image_prompt[:300]) # 長すぎるとエラーになるので調整
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed=42"
            
            st.image(image_url, caption=f"{style}な{room_type}のコーディネート", use_container_width=True)
            
            # 結果表示エリア
            st.success("生成完了！")
            with st.expander("AIが作成したプロンプトを見る"):
                st.write(image_prompt)
            
            if st.button("❤️ いいね！"):
                st.toast("フィードバックを保存しました")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
