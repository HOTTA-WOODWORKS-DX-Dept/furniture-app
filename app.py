import streamlit as st
import requests
import json
import base64
import io
import time
from PIL import Image

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")

# --- カスタムCSS（堀田木工所様向けデザイン） ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; background-color: #1E3A8A; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# --- API設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

# --- 共通関数 ---
def image_to_base64(uploaded_file):
    if uploaded_file is None: return None
    img = Image.open(uploaded_file)
    img.thumbnail((800, 800))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 管理者用：セッション状態の初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- メイン画面 ---
st.title("🛋️ Room AI Studio")
st.caption("AI Interior Coordination Prototype for Hotta Mokkosho")

tab1, tab2 = st.tabs(["🏠 サービス画面", "🔒 管理者コンソール"])

# ==========================================
# 🏠 サービス画面
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("Step 1: 家具と素材の登録")
        # ① 家具の撮影・アップロード
        f_file = st.file_uploader("① 家具を撮影またはアップロード", type=["jpg", "png", "jpeg"], key="fur")
        
        # ② 家具の種類（複数映り込み対策）
        f_type = st.selectbox("② ターゲットとなる家具の種類", ["3人掛けソファ", "1人掛けソファ", "ダイニングチェア", "ダイニングテーブル", "テレビボード", "デスク"])

        # ③ メイン色（生地）の登録
        fabric_file = st.file_uploader("③ 生地・素材の写真をアップロード (任意)", type=["jpg", "png", "jpeg"], key="fab")

        # ④ 木部（サブカラー）の登録
        wood_method = st.radio("④ 木部の指定方法", ["選択肢から選ぶ", "写真をアップロード"])
        wood_detail = ""
        if wood_method == "選択肢から選ぶ":
            wood_detail = st.selectbox("木部の色を選択", ["ナチュラルオーク", "ウォールナット", "ブラックチェリー", "ホワイトアッシュ"])
        else:
            wood_file = st.file_uploader("木部パーツの写真をアップロード", type=["jpg", "png", "jpeg"], key="wood")
            if wood_file: wood_detail = "uploaded photo"

    with col2:
        st.subheader("Step 2: 空間デザインの設定")
        # ⑤ 置きたい部屋
        room = st.selectbox("⑤ 配置する部屋", ["リビングルーム", "ダイニングルーム", "ベッドルーム", "書斎"])
        
        # ⑥ 部屋のテイスト・内装
        style = st.selectbox("⑥ 部屋のテイスト", ["北欧モダン", "ジャパンディ(和モダン)", "ヴィンテージ", "インダストリアル", "ナチュラル"])
        floor_color = st.selectbox("床の色", ["明るいオーク", "落ち着いたブラウン", "ホワイトタイル", "グレーコンクリート"])
        wall_color = st.selectbox("壁の色", ["ホワイト", "ライトグレー", "ベージュ", "ネイビー(アクセント)"])

        st.divider()
        # ⑦ 画像生成実行
        generate_btn = st.button("✨ コーディネート画像を生成", type="primary")

    if generate_btn:
        if not f_file:
            st.warning("家具の写真を登録してください。")
        else:
            status = st.empty()
            status.info("🚀 AIが家具と素材を分析してデザインを構築中...")
            
            try:
                # Gemini 2.0 Flash (Vision) で詳細なプロンプトを生成
                vision_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                
                f_base64 = image_to_base64(f_file)
                fab_base64 = image_to_base64(fabric_file) if fabric_file else None
                
                # Geminiへの詳細な指示
                analysis_prompt = f"""
                Analyze the provided furniture image (main target: {f_type}). 
                Task: Generate a high-quality interior photography prompt for Imagen 4.0.
                Setting: Place this {f_type} in a {style} {room}.
                Details: Floor is {floor_color}, Walls are {wall_color}. 
                Wood part: {wood_detail}.
                Important: Keep the exact shape and design of the {f_type} from the image. 
                If a fabric image is provided, use that texture/color for the upholstery.
                The scene should be cozy, realistic, and professionally lit.
                Output ONLY the English prompt.
                """
                
                contents = [{"parts": [{"text": analysis_prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": f_base64}}]}]
                if fab_base64:
                    contents[0]["parts"].append({"inline_data": {"mime_type": "image/jpeg", "data": fab_base64}})
                
                v_res = requests.post(vision_url, headers={'Content-Type': 'application/json'}, data=json.dumps({"contents": contents}))
                final_image_prompt = v_res.json()['candidates'][0]['content']['parts'][0]['text']

                # Imagen 4.0 で画像生成
                status.info("🎨 Imagen 4.0 が最終コーディネート画像を描画中...")
                imagen_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={api_key}"
                i_payload = {"instances": [{"prompt": final_image_prompt}], "parameters": {"sampleCount": 1, "aspectRatio": "4:3"}}
                i_res = requests.post(imagen_url, headers={'Content-Type': 'application/json'}, data=json.dumps(i_payload))
                
                if i_res.status_code == 200:
                    b64_img = i_res.json()['predictions'][0]['bytesBase64Encoded']
                    result_img = Image.open(io.BytesIO(base64.b64decode(b64_img)))
                    
                    status.success("コーディネートが完了しました！")
                    st.image(result_img, use_container_width=True, caption=f"{style}スタイルの提案")
                    
                    # ⑧ フィードバック機能
                    st.divider()
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        if st.button("❤️ 満足（いいね！）"):
                            st.toast("フィードバックありがとうございます！")
                    
                    # 管理者用履歴に追加
                    st.session_state.history.append({
                        "日付": time.strftime("%Y-%m-%d %H:%M"),
                        "家具": f_type,
                        "テイスト": style,
                        "部屋": room,
                        "生成プロンプト": final_image_prompt[:100] + "...",
                        "画像データ": b64_img # 簡易的に保存
                    })
                else:
                    st.error("画像生成でエラーが発生しました。")
            except Exception as e:
                st.error(f"システムエラー: {e}")

# ==========================================
# 🔒 管理者コンソール
# ==========================================
with tab2:
    st.subheader("管理者用：生成ログの確認")
    password = st.text_input("パスワードを入力してください", type="password")
    
    if password == "hotta-dx": # 仮のパスワード
        if not st.session_state.history:
            st.info("まだ生成履歴はありません。")
        else:
            st.write(f"現在の総生成数: {len(st.session_state.history)}件")
            for item in reversed(st.session_state.history):
                with st.expander(f"{item['日付']} - {item['家具']} ({item['テイスト']})"):
                    col_h1, col_h2 = st.columns([1, 2])
                    with col_h1:
                        st.image(base64.b64decode(item['画像データ']), use_container_width=True)
                    with col_h2:
                        st.write(f"**部屋:** {item['部屋']}")
                        st.write(f"**プロンプト:** {item['生成プロンプト']}")
    elif password:
        st.error("パスワードが正しくありません。")
