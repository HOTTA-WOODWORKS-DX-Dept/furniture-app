import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# --- ページ設定 (Appleライクなミニマル設定) ---
st.set_page_config(page_title="Room AI Studio", layout="centered", initial_sidebar_state="collapsed")

# --- 洗練されたカスタムCSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@300;400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #1d1d1f;
        background-color: #fbfbfd;
    }
    
    /* 見出しのスタイル */
    h1, h2, h3, h4 { font-weight: 500; letter-spacing: -0.5px; }
    h1 { font-size: 40px; text-align: center; margin-bottom: 40px; }
    
    /* ボタンのApple風スタイリング */
    .stButton>button {
        border-radius: 8px;
        font-weight: 400;
        transition: all 0.2s ease;
        border: 1px solid #d2d2d7;
        background-color: #ffffff;
        color: #1d1d1f;
        padding: 10px 20px;
    }
    .stButton>button:hover { background-color: #f5f5f7; border-color: #86868b; }
    
    /* プライマリボタン（生成など） */
    [data-testid="baseButton-primary"] { background-color: #1d1d1f; color: #ffffff; border: none; }
    [data-testid="baseButton-primary"]:hover { background-color: #424245; }
    
    /* 区切り線 */
    hr { margin: 40px 0; border-color: #e5e5ea; }
    
    /* 画像の角丸 */
    img { border-radius: 8px; }
    
    /* 選択肢（Radio）のクリーン化 */
    div[role="radiogroup"] > label { margin-right: 15px; font-weight: 400; }
</style>
""", unsafe_allow_html=True)

# --- API設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-3-pro-image-preview')
except:
    st.error("API Error: Please check your configuration.")
    st.stop()

# --- セッション状態の管理 ---
if 'page' not in st.session_state: st.session_state.page = 'front'
if 'history' not in st.session_state: st.session_state.history = []
if 'current_result' not in st.session_state: st.session_state.current_result = None
if 'auto_generate' not in st.session_state: st.session_state.auto_generate = False

def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.current_result = None
    st.session_state.auto_generate = False
    st.rerun()

# --- 素材・カラーリスト ---
COLORS_FABRIC = ["オフホワイト", "ベージュ", "ライトグレー", "ミディアムグレー", "チャコールグレー", "ブラック", "ネイビー", "オリーブグリーン", "マスタード", "テラコッタ"]
COLORS_LEATHER = ["ブラック", "ダークブラウン", "キャメル", "アイボリー", "バーガンディ"]
COLORS_WOOD = ["ナチュラルオーク", "ホワイトアッシュ", "ウォールナット", "チェリー", "チーク", "マホガニー", "ブラックアッシュ", "ホワイトウォッシュ"]
COLORS_METAL = ["シルバー", "ステンレス", "真鍮(ブラス)", "コッパー(銅)", "マットブラック"]
COLORS_INTERIOR = ["ピュアホワイト", "アイボリー", "ライトグレー", "ダークグレー", "ナチュラルウッド", "ダークウッド", "コンクリート", "ブラック", "ネイビー", "アクセントクロス"]

# ==========================================
# 1. フロントページ
# ==========================================
if st.session_state.page == 'front':
    st.markdown("<h1>Room AI Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #86868b; margin-bottom: 40px;'>Select a category to begin.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.image("https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=500", caption="Sofa", use_container_width=True)
        if st.button("Configure Sofa", use_container_width=True, type="primary"):
            go_to('sofa')
            
    with col2:
        st.image("https://images.unsplash.com/photo-1577140917170-285929fb55b7?auto=format&fit=crop&q=80&w=500", caption="Dining Table", use_container_width=True)
        st.button("Coming Soon", use_container_width=True, disabled=True)
    
    st.divider()
    col_admin, _ = st.columns([1, 3])
    with col_admin:
        if st.button("Admin Console", use_container_width=True):
            go_to('admin')

# ==========================================
# 2. コンフィギュレーター画面 (Sofa)
# ==========================================
elif st.session_state.page == 'sofa':
    if st.button("Back"): go_to('front')
    
    st.markdown("<h2 style='margin-bottom: 30px;'>Sofa Configuration</h2>", unsafe_allow_html=True)
    
    # 1. ベース画像
    st.markdown("#### Base Image")
    f_file = st.file_uploader("Upload base sofa image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if f_file: st.image(f_file, width=150)
    
    st.divider()

    # 2. 素材設定
    st.markdown("#### Materials")
    
    # 張地
    st.write("Upholstery (張地)")
    mat_type = st.radio("Type", ["Fabric", "Leather", "Custom Image"], horizontal=True, label_visibility="collapsed")
    fab_desc = ""
    if mat_type == "Fabric":
        fab_desc = st.selectbox("Color", COLORS_FABRIC, label_visibility="collapsed") + " Fabric"
    elif mat_type == "Leather":
        fab_desc = st.selectbox("Color", COLORS_LEATHER, label_visibility="collapsed") + " Leather"
    else:
        fabric_file = st.file_uploader("Upload custom fabric", type=["jpg", "png"], label_visibility="collapsed")
        if fabric_file: st.image(fabric_file, width=80)
        fab_desc = "uploaded custom fabric"
        
    st.write("")
    
    # フレーム
    st.write("Frame (フレーム)")
    frame_type = st.radio("Type", ["Wood", "Metal", "Custom Image"], horizontal=True, key="ft", label_visibility="collapsed")
    frame_desc = ""
    if frame_type == "Wood":
        frame_desc = st.selectbox("Color", COLORS_WOOD, key="fw", label_visibility="collapsed") + " Wood"
    elif frame_type == "Metal":
        frame_desc = st.selectbox("Color", COLORS_METAL, key="fm", label_visibility="collapsed") + " Metal"
    else:
        frame_file = st.file_uploader("Upload custom frame", type=["jpg", "png"], key="fu", label_visibility="collapsed")
        if frame_file: st.image(frame_file, width=80)
        frame_desc = "uploaded custom frame"

    st.divider()

    # 3. 空間設定
    st.markdown("#### Environment")
    
    st.write("Style (テイスト)")
    # スタイルの画像プレビュー（シミュレーション用）
    style_cols = st.columns(5)
    style_names = ["北欧ナチュラル", "モダン", "ヴィンテージ", "和風", "コンテンポラリー"]
    style_urls = [
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&q=60&w=200",
        "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&q=60&w=200",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&q=60&w=200",
        "https://images.unsplash.com/photo-1615873968403-89e068629265?auto=format&fit=crop&q=60&w=200",
        "https://images.unsplash.com/photo-1600607686527-6fb886090705?auto=format&fit=crop&q=60&w=200"
    ]
    for i, col in enumerate(style_cols):
        with col:
            st.image(style_urls[i], use_container_width=True)
    
    style = st.radio("Select Style", style_names, horizontal=True, label_visibility="collapsed")
    
    st.write("")
    col_int1, col_int2, col_int3 = st.columns(3)
    with col_int1:
        floor = st.selectbox("Floor (床)", COLORS_INTERIOR, index=4)
    with col_int2:
        wall = st.selectbox("Wall (壁)", COLORS_INTERIOR, index=0)
    with col_int3:
        fitting = st.selectbox("Fittings (建具)", COLORS_INTERIOR, index=4)

    st.write("")
    st.write("")
    
    # 実行トリガーの判定（ボタン押下 or リトライフラグ）
    generate_clicked = st.button("Generate Image", type="primary", use_container_width=True)
    if st.button("Reset Settings", use_container_width=True):
        go_to('sofa')
        
    should_generate = generate_clicked or st.session_state.auto_generate

    # --- 画像生成処理 ---
    if should_generate:
        st.session_state.auto_generate = False # 実行後はフラグを戻す
        
        if not f_file:
            st.error("Base image is required.")
        else:
            with st.spinner("Processing image..."):
                try:
                    main_img = Image.open(f_file)
                    
                    prompt = f"""
                    GENERATE_IMAGE: Create a highly realistic, architectural digest style interior design photo.
                    Main Subject: The sofa from the attached image. Maintain its exact shape and structure.
                    Upholstery: {fab_desc}.
                    Frame/Legs: {frame_desc}.
                    Scene Style: {style} interior design.
                    Background Details: {floor} floor, {wall} walls, {fitting} doors/fittings.
                    Lighting: Natural, soft, cinematic lighting.
                    """
                    
                    inputs = [prompt, main_img]
                    if mat_type == "Custom Image" and fabric_file: inputs.append(Image.open(fabric_file))
                    if frame_type == "Custom Image" and frame_file: inputs.append(Image.open(frame_file))

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
                        st.session_state.current_result = {
                            "id": str(time.time()),
                            "image": gen_img,
                            "style": style,
                            "fabric": fab_desc,
                            "frame": frame_desc,
                            "floor": floor,
                            "wall": wall,
                            "fitting": fitting,
                            "rating": None, # 初期状態は未評価
                            "saved": False,
                            "regenerated": False
                        }
                    else:
                        st.error("Failed to generate image.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- 生成結果 ---
    if st.session_state.current_result:
        st.divider()
        res = st.session_state.current_result
        
        col_img1, col_img2, col_img3 = st.columns([1, 4, 1])
        with col_img2:
            st.image(res["image"], use_container_width=True)
            
            st.write("")
            st.markdown("<p style='text-align:center; font-size:14px; color:#86868b;'>How would you rate this result?</p>", unsafe_allow_html=True)
            
            # 初期未選択状態の評価ラジオボタン
            rating = st.radio("Rating", [1, 2, 3, 4, 5], index=None, horizontal=True, label_visibility="collapsed")
            if rating is not None:
                res["rating"] = rating
            
            st.write("")
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                # 端末依存せず確実にDL/保存できる標準機能
                buf = io.BytesIO()
                res["image"].save(buf, format="PNG")
                if st.download_button("Save Image", data=buf.getvalue(), file_name="room_ai_studio.png", mime="image/png", use_container_width=True):
                    res["saved"] = True
                    st.session_state.history.append(res.copy())
            
            with col_act2:
                if st.button("Retry", use_container_width=True):
                    res["regenerated"] = True
                    st.session_state.history.append(res.copy())
                    st.session_state.auto_generate = True # 次のロードで自動生成
                    st.rerun()

# ==========================================
# 3. 管理者コンソール
# ==========================================
elif st.session_state.page == 'admin':
    if st.button("Back to Home"): go_to('front')
    
    st.markdown("<h2>Admin Console</h2>", unsafe_allow_html=True)
    pw = st.text_input("Password", type="password")
    
    if pw == "hotta-admin":
        st.write("")
        if not st.session_state.history:
            st.markdown("<p style='color: #86868b;'>No records found.</p>", unsafe_allow_html=True)
        else:
            st.write(f"Total Records: {len(st.session_state.history)}")
            for i, log in enumerate(reversed(st.session_state.history)):
                st.markdown("<div style='padding: 20px; background-color: #ffffff; border: 1px solid #e5e5ea; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.image(log["image"], use_container_width=True)
                with c2:
                    st.markdown(f"**Style:** {log['style']}")
                    st.markdown(f"**Materials:** Upholstery ({log['fabric']}) / Frame ({log['frame']})")
                    st.markdown(f"**Interior:** Floor ({log['floor']}) / Wall ({log['wall']}) / Fittings ({log['fitting']})")
                    
                    rating_display = f"{log['rating']}/5" if log['rating'] else "Unrated"
                    st.markdown(f"**Rating:** {rating_display}")
                    
                    status = []
                    if log['saved']: status.append("Saved")
                    if log['regenerated']: status.append("Retried")
                    st.markdown(f"**Status:** {' / '.join(status) if status else 'Previewed Only'}")
                st.markdown("</div>", unsafe_allow_html=True)
    elif pw:
        st.error("Incorrect password.")
