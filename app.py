import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")

# --- 1. API設定（Gemini Native画像生成） ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # リストにあった画像生成対応の最新Geminiを選択
    model = genai.GenerativeModel('models/gemini-3-pro-image-preview')
except Exception as e:
    st.error(f"API設定エラー: {e}")
    st.stop()

# --- 管理者用：生成履歴の初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = []

st.title("🛋️ Room AI Studio")
st.caption("堀田木工所 DX：Geminiネイティブ・コーディネート・システム")

tab1, tab2 = st.tabs(["🏠 サービス画面", "🔒 管理者コンソール"])

# ==========================================
# 🏠 サービス画面（ご要望の①〜⑦を実装）
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("Step 1: 家具と素材の入力")
        
        # ① スマホで撮影 or アップロード
        f_file = st.file_uploader("① 家具を撮影・アップロード", type=["jpg", "png", "jpeg"], key="main_f")
        
        # ② 家具の種類を選ぶ（複数映り込み対策）
        f_type = st.selectbox("② ターゲットの家具を選択", ["ソファ", "チェア", "テーブル", "テレビボード", "デスク"])

        # ③ 生地のメイン色画像を撮影・アップロード
        fabric_file = st.file_uploader("③ 生地の素材・色を撮影・アップロード", type=["jpg", "png", "jpeg"], key="fabric")

        # ④ サブカラー（木部）の設定
        wood_method = st.radio("④ 木部の指定", ["選択肢から選ぶ", "画像を撮影・アップロード"])
        wood_val = ""
        wood_img = None
        if wood_method == "選択肢から選ぶ":
            wood_val = st.selectbox("木部色を選択", ["ナチュラルオーク", "ウォールナット", "アッシュ", "チェリー"])
        else:
            wood_img = st.file_uploader("木部パーツを撮影・アップロード", type=["jpg", "png", "jpeg"], key="wood")

    with col2:
        st.subheader("Step 2: お部屋のコーディネート設定")
        
        # ⑤ 置きたい部屋を選ぶ
        room = st.selectbox("⑤ 配置する部屋", ["リビングルーム", "ダイニングルーム", "ベッドルーム", "書斎"])
        
        # ⑥ 部屋のテイスト・床・壁
        style = st.selectbox("⑥ 部屋のテイスト", ["北欧モダン", "ジャパンディ", "ヴィンテージ", "ナチュラル"])
        c1, c2 = st.columns(2)
        with c1:
            floor = st.selectbox("床の色", ["明るいオーク", "落ち着いたブラウン", "ホワイト", "グレー"])
        with c2:
            wall = st.selectbox("壁の色", ["ホワイト", "ライトグレー", "ベージュ", "アクセントブルー"])

        st.divider()
        
        # ⑦ 画像生成を実行
        generate_btn = st.button("✨ 画像生成を実行", type="primary")

    if generate_btn:
        if not f_file:
            st.warning("家具の写真をアップロードしてください。")
        else:
            status = st.empty()
            status.info("🚀 Geminiが空間をデザインしています... (約10〜20秒)")
            
            try:
                # 入力画像の読み込み
                main_img = Image.open(f_file)
                
                # Geminiへのネイティブ生成指示（プロンプト）
                # 家具の形を維持するよう強く指示し、素材や部屋の情報を統合します
                prompt = f"""
                GENERATE_IMAGE:
                Based on the attached images, generate a professional interior design photo.
                1. Target Furniture: Use the exact shape and design of the {f_type} from the first image.
                2. Main Fabric/Color: If a fabric image is provided, use that texture and color for the {f_type}.
                3. Sub Color (Wood): Use {wood_val if not wood_img else 'the texture from the wood image'} for the legs/frames.
                4. Scene: Place this furniture in a {style} {room}.
                5. Background: Floor should be {floor}, walls should be {wall}.
                6. Lighting: Realistic natural soft lighting.
                7. Style: High-end furniture catalog style. 
                Do not modify the structural design of the {f_type}.
                """
                
                # 入力素材のリスト
                inputs = [prompt, main_img]
                if fabric_file:
                    inputs.append(Image.open(fabric_file))
                if wood_img:
                    inputs.append(Image.open(wood_img))

                # --- 実行 ---
                response = model.generate_content(inputs)
                
                # エラーチェック (list index out of range 対策)
                if not response.candidates:
                    st.error("AIからの応答が空でした。安全フィルターに触れた可能性があります。")
                else:
                    # Gemini Native生成の結果から画像を取り出す
                    generated_image = None
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data'):
                            # バイナリデータから画像に復元
                            generated_image = Image.open(io.BytesIO(part.inline_data.data))
                            break
                        elif 'image' in str(type(part)): # SDKのバージョンによる差異
                            generated_image = part
                    
                    if generated_image:
                        status.success("生成が完了しました！")
                        st.image(generated_image, use_container_width=True, caption=f"提案コーディネート ({style})")
                        
                        # ⑧ 満足度・いいねボタン
                        st.write("このコーディネートは参考になりましたか？")
                        if st.button("❤️ いいね！"):
                            st.balloons()
                            st.toast("ありがとうございます！")

                        # 管理者履歴に保存
                        st.session_state.history.append({
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "f_type": f_type,
                            "style": style,
                            "img": generated_image
                        })
                    else:
                        st.warning("画像が生成されませんでした。AIがテキストのみで回答した可能性があります。")
                        st.write(response.text)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
                st.info("※APIの制限（Quota）や、モデル名が環境に合っていない可能性があります。")

# ==========================================
# 🔒 管理者コンソール (利用ログ確認)
# ==========================================
with tab2:
    st.subheader("管理者コンソール")
    pw = st.text_input("パスワードを入力", type="password")
    
    if pw == "hotta-admin": # 管理者パスワード
        if not st.session_state.history:
            st.info("まだ利用データがありません。")
        else:
            st.write(f"現在の総生成数: {len(st.session_state.history)}件")
            for item in reversed(st.session_state.history):
                with st.container(border=True):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image(item['img'], use_container_width=True)
                    with c2:
                        st.write(f"**日時:** {item['time']}")
                        st.write(f"**家具:** {item['f_type']}")
                        st.write(f"**スタイル:** {item['style']}")
    elif pw:
        st.error("パスワードが正しくありません。")
