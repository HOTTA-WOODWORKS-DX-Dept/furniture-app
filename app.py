import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="centered", initial_sidebar_state="collapsed")

# --- Apple風 ミニマルCSS ---
st.markdown("""
<style>
    /* 全体のフォント設定（SF Pro / ヒラギノ角ゴ） */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Hiragino Sans", sans-serif;
        color: #1d1d1f;
        background-color: #fbfbfd;
    }
    
    h1, h2, h3, h4 { font-weight: 600; letter-spacing: -0.02em; }
    
    /* Streamlit特有の赤いフォーカスリング（選択表示）を無効化 */
    *:focus, *:active {
        outline: none !important;
        box-shadow: none !important;
    }

    /* * [セカンダリボタン]
     * グリッドアイテム、戻る、変更、リセットなどのボタン
     * 枠線を完全に消し、テキストリンクのように振る舞わせる
     */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #1d1d1f !important;
        padding: 0 !important;
        font-size: 13px !important;
        min-height: auto !important;
    }
    button[kind="secondary"]:hover {
        color: #0071e3 !important; /* Appleのリンクブルー */
        opacity: 0.8;
    }
    
    /* * [プライマリボタン]
     * 画像生成、保存、再作成など、目立たせる主要アクション
     */
    button[kind="primary"] {
        background-color: #0071e3 !important; 
        color: #ffffff !important; 
        border: none !important;
        border-radius: 20px !important; /* 丸みを帯びたピル型 */
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: transform 0.2s ease, background-color 0.2s ease;
    }
    button[kind="primary"]:hover {
        background-color: #0077ed !important;
        transform: scale(1.02);
    }

    img { border-radius: 12px; }
    hr { margin: 40px 0; border-color: #e5e5ea; }
    
    /* 選択を促すテキストのスタイル */
    .section-title { font-size: 16px; font-weight: 600; color: #1d1d1f; margin-bottom: 12px; margin-top: 24px; }
    .select-prompt { font-size: 18px; font-weight: 600; color: #1d1d1f; margin-bottom: 16px; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# --- API設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-3-pro-image-preview')
except:
    st.error("API設定を確認してください。")
    st.stop()

# --- セッション状態 ---
if 'page' not in st.session_state: st.session_state.page = 'front'
if 'history' not in st.session_state: st.session_state.history = []
if 'gallery' not in st.session_state: st.session_state.gallery = [] 
if 'auto_gen' not in st.session_state: st.session_state.auto_gen = False

# 選択状態の管理
for k in ['fabric', 'frame', 'style', 'floor', 'wall', 'fitting']:
    if k not in st.session_state: st.session_state[k] = None

def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.gallery = []
    for k in ['fabric', 'frame', 'style', 'floor', 'wall', 'fitting']:
        st.session_state[k] = None
    st.rerun()

# --- カラーと画像の定義 ---
COLORS_FABRIC = {"ホワイト":"#F8F8F8", "アイボリー":"#FFFFF0", "ベージュ":"#F5F5DC", "ライトグレー":"#D3D3D3", "ダークグレー":"#696969", "ブラック":"#202020", "ネイビー":"#191970", "グリーン":"#556B2F", "マスタード":"#FFDB58", "テラコッタ":"#E2725B"}
COLORS_LEATHER = {"ブラック":"#1A1A1A", "ブラウン":"#5C4033", "キャメル":"#C19A6B", "アイボリー":"#FAF0E6", "ワイン":"#722F37"}
COLORS_WOOD = {"ナチュラルオーク":"#D2B48C", "ホワイトアッシュ":"#F5DEB3", "ウォールナット":"#5C4033", "チェリー":"#D2691E", "チーク":"#CD853F", "マホガニー":"#C04000", "ブラック":"#1A1A1A", "ホワイト":"#F8F8FF"}
COLORS_METAL = {"シルバー":"#C0C0C0", "ステンレス":"#B0C4DE", "真鍮":"#B5A642", "銅":"#B87333", "マットブラック":"#2F4F4F"}
COLORS_INT = {"ホワイト":"#FFFFFF", "アイボリー":"#FFFFF0", "ベージュ":"#F5F5DC", "ライトオーク":"#DEB887", "ウォールナット":"#5C4033", "ダークブラウン":"#3E2723", "ライトグレー":"#D3D3D3", "ダークグレー":"#696969", "ブラック":"#1C1C1C", "アクセントブルー":"#2C3E50"}

STYLES = {
    "北欧ナチュラル": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&q=60&w=300",
    "モダン": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&q=60&w=300",
    "ヴィンテージ": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&q=60&w=300",
    "和風": "https://images.unsplash.com/photo-1615873968403-89e068629265?auto=format&fit=crop&q=60&w=300",
    "コンテンポラリー": "https://images.unsplash.com/photo-1600607686527-6fb886090705?auto=format&fit=crop&q=60&w=300"
}

# --- UI部品関数 ---
def render_color_grid(options_dict, state_key, unique_id):
    items = list(options_dict.items())
    for i in range(0, len(items), 8):
        cols = st.columns(8)
        for j in range(8):
            if i + j < len(items):
                name, color = items[i + j]
                with cols[j]:
                    st.markdown(f'<div style="background-color:{color}; width:100%; aspect-ratio:1/1; border-radius:8px; border:1px solid #d2d2d7; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.03); margin-bottom:4px;"></div>', unsafe_allow_html=True)
                    if st.button(name, key=f"{state_key}_{unique_id}_{name}", use_container_width=True):
                        st.session_state[state_key] = name
                        st.rerun()

def render_style_grid():
    items = list(STYLES.items())
    cols = st.columns(5)
    for i, (name, url) in enumerate(items):
        with cols[i]:
            st.markdown(f'<div style="background-image:url({url}); background-size:cover; background-position:center; width:100%; aspect-ratio:1/1; border-radius:12px; margin-bottom:4px;"></div>', unsafe_allow_html=True)
            if st.button(name, key=f"style_{name}", use_container_width=True):
                st.session_state.style = name
                st.rerun()

def render_selected_state(label, value, state_key):
    st.markdown(f"""
    <div style="background-color: #f5f5f7; padding: 12px 16px; border-radius: 12px; font-size: 14px; color: #1d1d1f; margin-bottom: 8px;">
        <span style="font-weight: 600;">{label}</span> : <span style="color: #515154;">{value}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("変更", key=f"change_{state_key}"):
        st.session_state[state_key] = None
        if state_key == "floor":
            st.session_state.wall = None
            st.session_state.fitting = None
        elif state_key == "wall":
            st.session_state.fitting = None
        st.rerun()

# --- 画像処理関数 ---
def crop_to_4_3_and_watermark(img):
    w, h = img.size
    target_ratio = 4 / 3
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) / 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_ratio < target_ratio:
        new_h = int(w / target_ratio)
        top = (h - new_h) / 2
        img = img.crop((0, top, w, top + new_h))
    
    draw = ImageDraw.Draw(img)
    text = "HOTTA WOODWORKS-DX"
    try:
        font = ImageFont.truetype("LiberationSans-Regular.ttf", int(img.height * 0.025)) 
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = img.width - tw - 20, img.height - th - 20
    
    draw.text((x+1, y+1), text, font=font, fill=(0,0,0,100))
    draw.text((x, y), text, font=font, fill=(255,255,255,220))
    return img

# ==========================================
# 1. フロントページ
# ==========================================
if st.session_state.page == 'front':
    st.markdown("<h1 style='margin-top: 40px;'>Room AI Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#86868b; margin-bottom:40px;'>カテゴリを選択</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.image("https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=500&h=500", use_container_width=True)
        if st.button("ソファ", use_container_width=True, type="primary"):
            go_to('sofa')
            
    with col2:
        st.markdown("""
        <div style='position:relative; text-align:center; color:white;'>
            <img src='https://images.unsplash.com/photo-1577140917170-285929fb55b7?auto=format&fit=crop&q=80&w=500&h=500' style='width:100%; border-radius:16px; opacity:0.5;'>
            <div style='position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:20px; font-weight:600; color:#1d1d1f;'>Coming Soon</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("ダイニングテーブル", use_container_width=True, disabled=True)
    
    st.divider()
    if st.button("管理者画面"): go_to('admin')

# ==========================================
# 2. ソファ・コーディネート画面
# ==========================================
elif st.session_state.page == 'sofa':
    if st.button("戻る"): go_to('front')
    
    st.markdown("<h2>家具の設定</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-title'>ベース画像</div>", unsafe_allow_html=True)
    f_file = st.file_uploader("ベースとなる家具画像をアップロード", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if f_file: st.image(f_file, width=150)
    
    st.divider()

    st.markdown("<h2>素材</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-title'>張地</div>", unsafe_allow_html=True)
    if not st.session_state.fabric:
        t_col1, t_col2 = st.tabs(["布", "革"])
        with t_col1: render_color_grid(COLORS_FABRIC, "fabric", "fab")
        with t_col2: render_color_grid(COLORS_LEATHER, "fabric", "lea")
    else:
        render_selected_state("張地", st.session_state.fabric, "fabric")

    st.write("")
    
    st.markdown("<div class='section-title'>フレーム</div>", unsafe_allow_html=True)
    if not st.session_state.frame:
        t_col3, t_col4 = st.tabs(["木材", "金属"])
        with t_col3: render_color_grid(COLORS_WOOD, "frame", "wood")
        with t_col4: render_color_grid(COLORS_METAL, "frame", "metal")
    else:
        render_selected_state("フレーム", st.session_state.frame, "frame")

    st.divider()

    st.markdown("<h2>空間</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-title'>テイスト</div>", unsafe_allow_html=True)
    if not st.session_state.style:
        render_style_grid()
    else:
        render_selected_state("テイスト", st.session_state.style, "style")

    st.write("")

    st.markdown("<h2>内装</h2>", unsafe_allow_html=True)
    
    if not st.session_state.floor:
        st.markdown("<div class='select-prompt'>床を選択してください</div>", unsafe_allow_html=True)
        render_color_grid(COLORS_INT, "floor", "fl")
    else:
        render_selected_state("床", st.session_state.floor, "floor")

    if st.session_state.floor:
        if not st.session_state.wall:
            st.markdown("<div class='select-prompt'>壁を選択してください</div>", unsafe_allow_html=True)
            render_color_grid(COLORS_INT, "wall", "wa")
        else:
            render_selected_state("壁", st.session_state.wall, "wall")

    if st.session_state.wall:
        if not st.session_state.fitting:
            st.markdown("<div class='select-prompt'>建具を選択してください</div>", unsafe_allow_html=True)
            render_color_grid(COLORS_INT, "fitting", "fi")
        else:
            render_selected_state("建具", st.session_state.fitting, "fitting")

    st.divider()

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        gen_clicked = st.button("画像を生成", type="primary", use_container_width=True)
    with c_btn2:
        if st.button("設定をリセット", use_container_width=True):
            go_to('sofa')

    should_generate = gen_clicked or st.session_state.auto_gen

    if should_generate:
        st.session_state.auto_gen = False
        if not f_file:
            st.error("ベース画像をアップロードしてください。")
        else:
            with st.spinner("AIが空間を構築しています..."):
                try:
                    main_img = Image.open(f_file)
                    
                    fab_p = st.session_state.fabric or "appropriate color"
                    frame_p = st.session_state.frame or "appropriate material"
                    style_p = st.session_state.style or "modern"
                    floor_p = st.session_state.floor or "matching"
                    wall_p = st.session_state.wall or "matching"
                    fitting_p = st.session_state.fitting or "matching"
                    
                    prompt = f"""
                    GENERATE_IMAGE: Create a highly realistic, architectural digest style interior design photo. Aspect Ratio: 4:3.
                    Furniture: The sofa from the attached image. Maintain exact shape.
                    Upholstery: {fab_p}. Frame/Legs: {frame_p}.
                    Style: {style_p} interior.
                    Interior Details: Floor: {floor_p}, Walls: {wall_p}, Doors/Fittings: {fitting_p}.
                    Lighting: Natural cinematic lighting.
                    """
                    
                    response = model.generate_content([prompt, main_img])
                    
                    gen_img = None
                    if response.candidates:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'inline_data'):
                                gen_img = Image.open(io.BytesIO(part.inline_data.data))
                                break
                            elif 'image' in str(type(part)):
                                gen_img = part
                                
                    if gen_img:
                        final_img = crop_to_4_3_and_watermark(gen_img)
                        
                        st.session_state.gallery.append({
                            "id": str(time.time()),
                            "base_image": main_img.copy(), 
                            "image": final_img,
                            "desc": f"{style_p} / 張地:{fab_p} / 床:{floor_p}",
                            "rating": None
                        })
                    else:
                        st.error("生成に失敗しました。")
                except Exception as e:
                    st.error(f"エラー: {e}")

    if st.session_state.gallery:
        st.divider()
        st.markdown("<h2>生成結果</h2>", unsafe_allow_html=True)
        
        total_imgs = len(st.session_state.gallery)
        current_idx = 0
        if total_imgs > 1:
            current_idx = st.slider("スワイプして履歴を確認", 1, total_imgs, total_imgs) - 1
            
        res = st.session_state.gallery[current_idx]
        
        c_img1, c_img2, c_img3 = st.columns([1, 4, 1])
        with c_img2:
            st.image(res["image"], use_container_width=True)
            st.caption(res["desc"])
            
            st.write("")
            st.markdown("<p style='text-align:center; font-weight:600; font-size:14px;'>画像を評価すると保存や再作成出来ます</p>", unsafe_allow_html=True)
            
            rating = st.radio("評価", [1, 2, 3, 4, 5], index=None, horizontal=True, label_visibility="collapsed", key=f"rate_{res['id']}")
            
            if rating is not None:
                res["rating"] = rating
                st.write("")
                col_a, col_b = st.columns(2)
                with col_a:
                    buf = io.BytesIO()
                    res["image"].save(buf, format="PNG")
                    if st.download_button("保存", data=buf.getvalue(), file_name=f"room_ai_{int(time.time())}.png", mime="image/png", use_container_width=True, type="primary"):
                        log_data = res.copy()
                        log_data["action"] = "保存"
                        st.session_state.history.append(log_data)
                
                with col_b:
                    if st.button("再作成", use_container_width=True, type="primary", key=f"retry_{res['id']}"):
                        log_data = res.copy()
                        log_data["action"] = "再作成"
                        st.session_state.history.append(log_data)
                        
                        st.session_state.auto_gen = True
                        st.rerun()

# ==========================================
# 3. 管理者画面
# ==========================================
elif st.session_state.page == 'admin':
    if st.button("戻る"): go_to('front')
    
    st.markdown("<h2>管理者画面</h2>", unsafe_allow_html=True)
    pw = st.text_input("パスワード", type="password")
    
    if pw == "hotta-admin":
        st.write("")
        if not st.session_state.history:
            st.markdown("<p style='color: #86868b;'>保存または再作成されたデータはありません。</p>", unsafe_allow_html=True)
        else:
            st.write(f"記録数: {len(st.session_state.history)}件")
            for log in reversed(st.session_state.history):
                st.markdown("<div style='padding: 24px; background-color: #ffffff; border: 1px solid #e5e5ea; border-radius: 16px; margin-bottom: 24px;'>", unsafe_allow_html=True)
                
                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    st.markdown("<p style='font-size:12px; color:#86868b; margin-bottom:4px;'>ベース画像</p>", unsafe_allow_html=True)
                    # エラー対策：古い履歴データに base_image がない場合をチェック
                    if "base_image" in log:
                        st.image(log["base_image"], use_container_width=True)
                    else:
                        st.caption("※以前のバージョンのため画像なし")
                with img_col2:
                    st.markdown("<p style='font-size:12px; color:#86868b; margin-bottom:4px;'>生成結果</p>", unsafe_allow_html=True)
                    st.image(log["image"], use_container_width=True)
                
                st.write("")
                st.markdown(f"<span style='font-weight:600;'>設定詳細:</span> {log['desc']}", unsafe_allow_html=True)
                st.markdown(f"<span style='font-weight:600;'>評価:</span> {log['rating']} / 5", unsafe_allow_html=True)
                st.markdown(f"<span style='font-weight:600;'>実行アクション:</span> <span style='color:#0071e3;'>{log['action']}</span>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    elif pw:
        st.error("パスワードが違います。")
