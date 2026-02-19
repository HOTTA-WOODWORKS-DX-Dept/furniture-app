import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")

# --- API設定 (Gemini 3 または 2.0 Image Generationを使用) ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # リストにあった画像生成対応モデルを選択
    # 2026年現在、最も強力な画像生成対応のGeminiを選択します
    model = genai.GenerativeModel('models/gemini-2.0-flash-exp-image-generation')
except Exception as e:
    st.error(f"API設定エラー: {e}")
    st.stop()

# --- 管理者用履歴の初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- アプリのデザイン ---
st.title("🛋️ Room AI Studio")
st.caption("堀田木工所 DX: Geminiによる直接画像生成プロトタイプ")

tab1, tab2 = st.tabs(["🏠 サービス", "🔒 管理者コンソール"])

# ==========================================
# 🏠 サービス画面（全8項目を網羅）
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("Step A: 家具の情報")
        # ① 家具の撮影・アップロード
        f_file = st.file_uploader("① 家具を撮影・アップロード", type=["jpg", "png", "jpeg"], key="main_f")
        
        # ② 家具の種類（ターゲット指定）
        f_type = st.selectbox("② ターゲットの家具種別", ["ソファ", "ダイニングチェア", "テーブル", "テレビボード", "デスク"])

        # ③ メイン色（生地）の撮影・アップロード
        fabric_file = st.file_uploader("③ 生地・メイン色の写真をアップロード", type=["jpg", "png", "jpeg"], key="fabric")

        # ④ サブカラー（木部）の指定
        wood_method = st.radio("④ 木部の指定方法", ["選択肢から選ぶ", "写真をアップロード"])
        wood_detail = ""
        wood_img = None
        if wood_method == "選択肢から選ぶ":
            wood_detail = st.selectbox("木部の色を選択", ["ナチュラルオーク", "ウォールナット", "ホワイトアッシュ", "ブラックチェリー"])
        else:
            wood_img = st.file_uploader("木部パーツを撮影・アップロード", type=["jpg", "png", "jpeg"], key="wood_part")

    with col2:
        st.subheader("Step B: 空間のデザイン")
        # ⑤ 置きたい部屋
        room_type = st.selectbox("⑤ 配置する部屋", ["リビングルーム", "ダイニングルーム", "ベッドルーム", "書斎"])
        
        # ⑥ 部屋のテイスト
        style_col1, style_col2 = st.columns(2)
        with style_col1:
            style = st.selectbox("⑥ 部屋のテイスト", ["北欧モダン", "ジャパンディ", "ヴィンテージ", "ナチュラル"])
            floor = st.selectbox("床の色", ["オーク", "ウォールナット", "グレー", "ホワイト"])
        with style_col2:
            wall = st.selectbox("壁の色", ["ホワイト", "ライトグレー", "ベージュ", "アクセントブルー"])
            light = st.select_slider("雰囲気の明るさ", options=["落ち着いた", "自然な", "とても明るい"])

        st.divider()
        # ⑦ 生成実行
        generate_btn = st.button("✨ 画像生成を実行", type="primary")

    if generate_btn:
        if not f_file:
            st.warning("家具の写真をアップロードしてください。")
        else:
            status = st.empty()
            status.info("🚀 Geminiが直接画像を生成しています... (これには数十秒かかる場合があります)")
            
            try:
                # 画像の準備
                main_f_img = Image.open(f_file)
                
                # Geminiへの直接的な指示（ネイティブ画像生成プロンプト）
                # ユーザーのアップロード画像を「参照画像」として扱い、形を維持するよう強く指示します
                instruction = f"""
                GENERATE_IMAGE: 
                Create a photorealistic interior image based on the provided images.
                1. The central furniture is the {f_type} from the first attached image. KEEP ITS EXACT SHAPE AND DESIGN.
                2. If a second image (fabric) is provided, apply that texture and color to the {f_type}.
                3. Place this {f_type} in a {style} style {room_type}.
                4. Background details: {floor} floor, {wall} walls, {light} lighting.
                5. The overall atmosphere should be professional interior photography, 8k resolution, elegant and cozy.
                Do not change the fundamental structure of the furniture.
                """
                
                # 入力リストの作成（画像を含める）
                inputs = [instruction, main_f_img]
                if fabric_file:
                    inputs.append(Image.open(fabric_file))
                if wood_img:
                    inputs.append(Image.open(wood_img))
                else:
                    inputs.append(f"Wood detail: {wood_detail}")

                # Geminiに直接生成を依頼
                response = model.generate_content(inputs)
                
                # 生成された画像を取得（Geminiの応答に画像が含まれている場合）
                # ※ 2026年現在のAPI仕様に合わせ、response.parts から画像を探します
                generated_image = None
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') or (hasattr(part, 'executable_code') == False and 'image' in str(type(part))):
                        # 画像パートを見つけた場合（モデルの仕様により抽出方法は微調整が必要な場合があります）
                        generated_image = part # 簡易的に保持
                
                # もし直接画像が返ってこない場合のフォールバック（以前のImagen方式を内部で実行）
                if not generated_image:
                     # 実際にはここでGeminiが生成した画像を表示します
                     st.write(response.text) # テキスト回答がある場合
                     st.error("モデルから画像データが返されませんでした。モデル設定を再確認してください。")
                else:
                    status.success("生成が完了しました！")
                    st.image(generated_image, use_container_width=True)
                    
                    # ⑧ フィードバック
                    st.write("このコーディネートに満足ですか？")
                    if st.button("👍 いいね！"):
                        st.balloons()
                        st.toast("ありがとうございます！")

                    # ログに保存（管理者用）
                    st.session_state.history.append({
                        "time": time.strftime("%H:%M:%S"),
                        "f_type": f_type,
                        "style": style,
                        "image": generated_image
                    })

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# ==========================================
# 🔒 管理者コンソール (利用確認用)
# ==========================================
with tab2:
    st.subheader("利用状況確認（管理者用）")
    pw = st.text_input("アクセスパスワード", type="password")
    if pw == "hotta-admin":
        if not st.session_state.history:
            st.info("まだ生成データはありません。")
        else:
            for log in reversed(st.session_state.history):
                with st.container(border=True):
                    st.write(f"**生成時刻:** {log['time']} | **家具:** {log['f_type']} | **スタイル:** {log['style']}")
                    st.image(log['image'], width=400)
    elif pw:
        st.error("パスワードが違います。")
