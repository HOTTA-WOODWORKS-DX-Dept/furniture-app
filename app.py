import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="centered", initial_sidebar_state="collapsed")

# --- Apple風 洗練されたカスタムCSS ---
st.markdown("""
<style>
    /* 全体のフォントと背景 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }
    
    /* ボタンのApple風スタイリング */
    .stButton>button {
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
    
    /* プライマリボタン（生成など） */
    [data-testid="baseButton-primary"] { background-color: #000000; color: #ffffff; }
    
    /* セカンダリボタン（戻る、リセットなど） */
    [data-testid="baseButton-secondary"] { background-color: #f5f5f7; color: #1d1d1f; border: 1px solid #d2d2d7; }
    
    /* Expander（折りたたみ）のクリーン化 */
    .streamlit-expanderHeader { font-weight: 500; color: #1d1d1f; }
    
    /* 画像の角丸 */
    img { border-radius: 12px; }
    
    /* Coming Soon カード */
    .coming-soon-card {
        background-color: #f5f5f7;
        border-radius: 16px;
        padding: 40px 20px;
        text-align: center;
        color: #86868b;
        border: 2px dashed #d2d2d7;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- API設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-3-pro-image-preview') # または環境に合わせて変更
except:
    st.error("APIキーの設定を確認してください。")
    st.stop()

# --- セッション状態の初期化（画面遷移とデータ保存用） ---
if 'page' not in st.session_state: st.session_state.page = 'front'
if 'history' not in st.session_state: st.session_state.history = []
if 'current_result' not in st.session_state: st.session_state.current_result = None

# --- ページ遷移関数 ---
def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.current_result = None # 画面移動時に結果をクリア
    st.rerun()

# ==========================================
# 📱 1. フロントページ
# ==========================================
if st.session_state.page == 'front':
    st.markdown("<h1 style='text-align: center; font-weight: 700; margin-bottom: 50px;'>Room AI Studio</h1>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='color: #1d1d1f;'>家具の種類を選択してください</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='text-align:center; padding: 20px; background: #ffffff; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        st.markdown("<h3>🛋️</h3>", unsafe_allow_html=True)
        st.markdown("<h4>Sofa</h4>", unsafe_allow_html=True)
        if st.button("ソファを選択", use_container_width=True, type="primary"):
            go_to('sofa')
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class='coming-soon-card'>
            <h3>🪑</h3>
            <h4>Dining Table</h4>
            <p>Coming Soon...</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    st.divider()
    col_admin, _ = st.columns([1, 3])
    with col_admin:
        if st.button("🔒 管理者コンソール", use_container_width=True):
            go_to('admin')

# ==========================================
# 🛋️ 2. ソファ コーディネート画面
# ==========================================
elif st.session_state.page == 'sofa':
    if st.button("← フロントページに戻る"): go_to('front')
    
    st.markdown("<h2>Sofa Configuration</h2>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### 1. ベースとなるソファ画像")
        f_file = st.file_uploader("写真をアップロード", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
        if f_file: st.image(f_file, width=150)

    with st.container(border=True):
        st.markdown("#### 2. 素材の変更")
        
        with st.expander("✨ 張地（ファブリック/レザー）", expanded=True):
            fabric_choice = st.radio("カラーを選択", ["⚪️ アイボリー", "🟤 キャメル", "⚫️ ブラック", "🛋️ グレーファブリック", "🟦 ネイビーファブリック"], horizontal=True)
            st.caption("または画像をアップロード")
            fabric_file = st.file_uploader("張地の画像", type=["jpg", "png"], key="up_fab")
            if fabric_file: st.image(fabric_file, width=80)

        with st.expander("🪵 フレーム（木部/脚部）", expanded=True):
            frame_choice = st.radio("素材を選択", ["🪵 ナチュラルオーク", "🪵 ウォールナット", "💿 シルバー(金属)", "🟡 真鍮(金属)", "⚫️ アイアン(金属)"], horizontal=True)
            st.caption("または画像をアップロード")
            frame_file = st.file_uploader("フレームの画像", type=["jpg", "png"], key="up_frame")
            if frame_file: st.image(frame_file, width=80)

    with st.container(border=True):
        st.markdown("#### 3. 空間の設定")
        room = st.selectbox("配置する部屋", ["リビングルーム", "ベッドルーム", "書斎", "カフェスペース"])
        style = st.selectbox("テイスト", ["北欧ナチュラル", "モダン", "ヴィンテージ", "和風", "コンテンポラリー"])

    # ボタンエリア
    col_g, col_r = st.columns(2)
    with col_g:
        generate_btn = st.button("✨ 画像を生成する", type="primary", use_container_width=True)
    with col_r:
        if st.button("🔄 設定をリセット", use_container_width=True):
            go_to('sofa') # 画面リロードで初期化

    # --- 画像生成処理 ---
    if generate_btn:
        if not f_file:
            st.error("ベースとなるソファ画像をアップロードしてください。")
        else:
            with st.spinner("Apple Silicon... ではなく Gemini が画像を処理中..."):
                try:
                    main_img = Image.open(f_file)
                    
                    # プロンプトの組み立て
                    fab_desc = "the uploaded fabric image" if fabric_file else fabric_choice
                    frame_desc = "the uploaded frame image" if frame_file else frame_choice
                    
                    prompt = f"""
                    GENERATE_IMAGE: Create a high-end, photorealistic interior design catalog photo.
                    Furniture: The sofa from the main attached image. KEEP ITS EXACT SHAPE.
                    Upholstery: Change the sofa's upholstery to {fab_desc}.
                    Frame/Legs: Change the frame/legs to {frame_desc}.
                    Scene: Place it in a {style} style {room}.
                    Lighting: Natural, soft, cinematic lighting. Architectural digest style.
                    """
                    
                    inputs = [prompt, main_img]
                    if fabric_file: inputs.append(Image.open(fabric_file))
                    if frame_file: inputs.append(Image.open(frame_file))

                    response = model.generate_content(inputs)
                    
                    gen_img = None
                    if response.candidates:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'inline_data'):
                                gen_img = Image.open(io.BytesIO(part.inline_data.data))
                                break
                            elif 'image' in str(type(part)):
                                gen_img = part
                                
                    if gen_img:
                        # セッションに結果を一時保存（再生成・評価のため）
                        st.session_state.current_result = {
                            "id": str(time.time()),
                            "image": gen_img,
                            "style": style,
                            "room": room,
                            "fabric": fab_desc,
                            "frame": frame_desc,
                            "rating": 0,
                            "saved": False,
                            "regenerated": False
                        }
                    else:
                        st.error("画像の生成に失敗しました。")
                except Exception as e:
                    st.error(f"エラー: {e}")

    # --- 生成結果の表示エリア ---
    if st.session_state.current_result:
        st.divider()
        st.markdown("### 生成結果")
        
        res = st.session_state.current_result
        
        # 大きすぎないサイズ（width=500）で中央配置
        col_img1, col_img2, col_img3 = st.columns([1, 4, 1])
        with col_img2:
            st.image(res["image"], width=500, caption=f"{res['style']} × {res['room']}")
            
            # 評価とアクション
            st.markdown("**このコーディネートの評価**")
            rating = st.radio("1:不満 〜 5:大満足", [1, 2, 3, 4, 5], horizontal=True, index=2, label_visibility="collapsed")
            res["rating"] = rating
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("💾 画像を保管", use_container_width=True):
                    res["saved"] = True
                    # 履歴に追加
                    st.session_state.history.append(res.copy())
                    st.success("保管しました！")
            with col_act2:
                if st.button("🔄 再作成（リトライ）", use_container_width=True):
                    res["regenerated"] = True
                    st.session_state.history.append(res.copy()) # 再作成前のデータも履歴に残す
                    st.info("上部の「画像を生成する」ボタンをもう一度押してください。")

# ==========================================
# 🔒 3. 管理者コンソール
# ==========================================
elif st.session_state.page == 'admin':
    if st.button("← フロントページに戻る"): go_to('front')
    
    st.markdown("<h2>Admin Console</h2>", unsafe_allow_html=True)
    pw = st.text_input("アクセスパスワード", type="password")
    
    if pw == "hotta-admin":
        st.success("認証成功")
        if not st.session_state.history:
            st.info("保管または再作成された履歴はまだありません。")
        else:
            st.write(f"総記録数: {len(st.session_state.history)}件")
            for i, log in enumerate(reversed(st.session_state.history)):
                with st.container(border=True):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image(log["image"], width=200)
                    with c2:
                        st.write(f"**設定:** {log['style']} / {log['room']}")
                        st.write(f"**素材:** 張地({log['fabric']}) | フレーム({log['frame']})")
                        st.write(f"**評価:** {'⭐' * log['rating']} ({log['rating']}/5)")
                        
                        status_badges = []
                        if log['saved']: status_badges.append("💾 保管済み")
                        if log['regenerated']: status_badges.append("🔄 再作成実行")
                        st.write(" **アクション:** " + " / ".join(status_badges))
    elif pw:
        st.error("パスワードが違います。")
