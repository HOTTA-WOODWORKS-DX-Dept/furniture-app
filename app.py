import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io
import time
import json
import base64
import os

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="centered", initial_sidebar_state="collapsed")

# --- データの永続化（スマホ・PC間の同期システム） ---
HISTORY_FILE = "history_db.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history_list):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history_list, f)

def pil_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def b64_to_pil(b64_str):
    return Image.open(io.BytesIO(base64.b64decode(b64_str)))

# --- セッション状態 ---
if 'page' not in st.session_state: st.session_state.page = 'front'
if 'history' not in st.session_state: st.session_state.history = load_history()
if 'gallery' not in st.session_state: st.session_state.gallery = [] 
if 'auto_gen' not in st.session_state: st.session_state.auto_gen = False

for k in ['fabric', 'frame', 'style', 'floor', 'wall', 'fitting']:
    if k not in st.session_state: st.session_state[k] = None

def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.gallery = []
    for k in ['fabric', 'frame', 'style', 'floor', 'wall', 'fitting']:
        st.session_state[k] = None
    st.rerun()

# --- Apple風 ミニマル & レスポンシブ CSS ---
st.markdown("""
<style>
    /* 全体のフォント設定 */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Kaku Gothic ProN", sans-serif;
        color: #1d1d1f;
        background-color: #fbfbfd;
    }
    
    h1, h2, h3, h4 { font-weight: 600; letter-spacing: -0.02em; }
    
    /* 赤い枠線（フォーカス）の無効化 */
    *:focus, *:active { outline: none !important; box-shadow: none !important; }

    /* --- ボタンのスタイリング（ブルーを廃止し、グレー・ブラックへ） --- */
    button[kind="primary"] {
        background-color: #1d1d1f !important; /* Apple風ダークグレー */
        color: #ffffff !important; 
        border: none !important;
        border-radius: 20px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        transition: transform 0.2s ease, opacity 0.2s ease;
    }
    button[kind="primary"]:hover { opacity: 0.8; transform: scale(1.02); }

    /* 通常ボタン・戻るボタン・変更ボタン */
    button[kind="secondary"] {
        border-radius: 12px !important;
        border: 1px solid #d2d2d7 !important;
        background-color: #ffffff !important;
        color: #1d1d1f !important;
    }
    
    /* --- マテリアル選択用のボタン（文字の枠を消し、小さくする） --- */
    div.material-btn button {
        border: none !important;
        background-color: transparent !important;
        font-size: 11px !important;
        padding: 0 !important;
        color: #515154 !important;
        min-height: 0 !important;
    }
    
    /* --- フロントページの画像ボタン --- */
    div.front-sofa button {
        background: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url('https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=500&h=500') center/cover;
        height: 200px; color: white !important; font-size: 24px !important; font-weight: bold !important; border: none !important; border-radius: 16px !important;
    }
    div.front-dining button {
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1577140917170-285929fb55b7?auto=format&fit=crop&q=80&w=500&h=500') center/cover;
        height: 200px; color: white !important; font-size: 20px !important; font-weight: bold !important; border: none !important; border-radius: 16px !important; cursor: default !important;
    }

    /* --- スマホでアイコンが巨大化するのを防ぐ（グリッド維持） --- */
    @media (max-width: 640px) {
        [data-testid="column"] {
            min-width: 20% !important; /* 1行に4〜5個並べる */
            flex: 0 0 20% !important;
        }
    }
    
    img { border-radius: 12px; }
    hr { margin: 40px 0; border-color: #e5e5ea; }
    .section-title { font-size: 15px; font-weight: 600; color: #1d1d1f; margin-bottom: 8px; margin-top: 24px; }
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
    # 1/4サイズ感（1行に5〜6個配置。CSSでスマホ時は自動調整）
    cols = st.columns(6)
    for i, (name, color) in enumerate(items):
        with cols[i % 6]:
            # 色の四角
            st.markdown(f'<div style="background-color:{color}; width:100%; aspect-ratio:1/1; border-radius:8px; border:1px solid #e5e5ea; margin-bottom:4px;"></div>', unsafe_allow_html=True)
            # 文字枠なしボタン
            st.markdown('<div class="material-btn">', unsafe_allow_html=True)
            if st.button(name, key=f"{state_key}_{unique_id}_{name}", use_container_width=True):
                st.session_state[state_key] = {"name": name, "color": color, "type": "color"}
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def render_style_grid():
    items = list(STYLES.items())
    cols = st.columns(3) # テイストは少し大きめに（3列）
    for i, (name, url) in enumerate(items):
        with cols[i % 3]:
            st.markdown(f'<div style="background-image:url({url}); background-size:cover; background-position:center; width:100%; aspect-ratio:1/1; border-radius:12px; margin-bottom:4px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="material-btn">', unsafe_allow_html=True)
            if st.button(name, key=f"style_{name}", use_container_width=True):
                st.session_state.style = {"name": name, "url": url, "type": "style"}
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def render_selected_state(label, selection, state_key):
    # 選択後もアイコンや画像を表示し続ける
    st.markdown(f"<div class='section-title'>{label}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 2])
    with c1:
        if selection["type"] == "color":
            st.markdown(f'<div style="background-color:{selection["color"]}; width:100%; aspect-ratio:1/1; border-radius:8px; border:1px solid #e5e5ea;"></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background-image:url({selection["url"]}); background-size:cover; background-position:center; width:100%; aspect-ratio:1/1; border-radius:8px;"></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p style='font-size:14px; margin-top:10px;'>{selection['name']}</p>", unsafe_allow_html=True)
    with c3:
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
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="front-sofa">', unsafe_allow_html=True)
        if st.button("SOFA", use_container_width=True): go_to('sofa')
        st.markdown('</div>', unsafe_allow_html=True)
            
    with col2:
        st.markdown('<div class="front-dining">', unsafe_allow_html=True)
        st.button("Coming Soon\nDining Table", use_container_width=True, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    col_admin, _ = st.columns([1, 3])
    with col_admin:
        if st.button("管理者画面"): go_to('admin')

# ==========================================
# 2. ソファ・コーディネート画面
# ==========================================
elif st.session_state.page == 'sofa':
    st.markdown("<h2>家具の設定</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-title'>ベース画像</div>", unsafe_allow_html=True)
    f_file = st.file_uploader("ベースとなる家具画像をアップロード", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if f_file: st.image(f_file, width=150)
    
    st.divider()

    st.markdown("<h2>素材</h2>", unsafe_allow_html=True)
    
    if not st.session_state.fabric:
        st.markdown("<div class='section-title'>張地</div>", unsafe_allow_html=True)
        t_col1, t_col2 = st.tabs(["布", "革"])
        with t_col1: render_color_grid(COLORS_FABRIC, "fabric", "fab")
        with t_col2: render_color_grid(COLORS_LEATHER, "fabric", "lea")
    else:
        render_selected_state("張地", st.session_state.fabric, "fabric")

    st.write("")
    
    if not st.session_state.frame:
        st.markdown("<div class='section-title'>フレーム</div>", unsafe_allow_html=True)
        t_col3, t_col4 = st.tabs(["木材", "金属"])
        with t_col3: render_color_grid(COLORS_WOOD, "frame", "wood")
        with t_col4: render_color_grid(COLORS_METAL, "frame", "metal")
    else:
        render_selected_state("フレーム", st.session_state.frame, "frame")

    st.divider()

    st.markdown("<h2>空間</h2>", unsafe_allow_html=True)
    
    if not st.session_state.style:
        st.markdown("<div class='section-title'>テイスト</div>", unsafe_allow_html=True)
        render_style_grid()
    else:
        render_selected_state("テイスト", st.session_state.style, "style")

    st.write("")

    st.markdown("<h2>内装</h2>", unsafe_allow_html=True)
    
    if not st.session_state.floor:
        st.markdown("<div class='section-title' style='color:#0071e3;'>床を選択してください</div>", unsafe_allow_html=True)
        render_color_grid(COLORS_INT, "floor", "fl")
    else:
        render_selected_state("床", st.session_state.floor, "floor")

    if st.session_state.floor:
        if not st.session_state.wall:
            st.markdown("<div class='section-title' style='color:#0071e3;'>壁を選択してください</div>", unsafe_allow_html=True)
            render_color_grid(COLORS_INT, "wall", "wa")
        else:
            render_selected_state("壁", st.session_state.wall, "wall")

    if st.session_state.wall:
        if not st.session_state.fitting:
            st.markdown("<div class='section-title' style='color:#0071e3;'>建具を選択してください</div>", unsafe_allow_html=True)
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
            with st.spinner("Processing..."):
                try:
                    main_img = Image.open(f_file)
                    
                    fab_p = st.session_state.fabric["name"] if st.session_state.fabric else "appropriate color"
                    frame_p = st.session_state.frame["name"] if st.session_state.frame else "appropriate material"
                    style_p = st.session_state.style["name"] if st.session_state.style else "modern"
                    floor_p = st.session_state.floor["name"] if st.session_state.floor else "matching"
                    wall_p = st.session_state.wall["name"] if st.session_state.wall else "matching"
                    fitting_p = st.session_state.fitting["name"] if st.session_state.fitting else "matching"
                    
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
                            "base_img_b64": pil_to_b64(main_img.copy()), 
                            "gen_img_b64": pil_to_b64(final_img),
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
        display_img = b64_to_pil(res["gen_img_b64"])
        
        c_img1, c_img2, c_img3 = st.columns([1, 4, 1])
        with c_img2:
            st.image(display_img, use_container_width=True)
            st.caption(res["desc"])
            
            st.write("")
            st.markdown("<p style='text-align:center; font-weight:500; font-size:14px;'>画像を評価すると保存や再作成出来ます</p>", unsafe_allow_html=True)
            
            rating = st.radio("評価", [1, 2, 3, 4, 5], index=None, horizontal=True, label_visibility="collapsed", key=f"rate_{res['id']}")
            
            if rating is not None:
                res["rating"] = rating
                st.write("")
                col_a, col_b = st.columns(2)
                with col_a:
                    buf = io.BytesIO()
                    display_img.save(buf, format="PNG")
                    if st.download_button("画像を保管", data=buf.getvalue(), file_name=f"room_ai_{int(time.time())}.png", mime="image/png", use_container_width=True):
                        log_data = res.copy()
                        log_data["action"] = "保存"
                        st.session_state.history.append(log_data)
                        save_history(st.session_state.history) # JSONに保存（同期）
                
                with col_b:
                    if st.button("再作成", use_container_width=True, key=f"retry_{res['id']}"):
                        log_data = res.copy()
                        log_data["action"] = "再作成"
                        st.session_state.history.append(log_data)
                        save_history(st.session_state.history) # JSONに保存（同期）
                        
                        st.session_state.auto_gen = True
                        st.rerun()
                        
    # 戻るボタンは最下部
    st.divider()
    if st.button("戻る", use_container_width=True): go_to('front')

# ==========================================
# 3. 管理者画面
# ==========================================
elif st.session_state.page == 'admin':
    st.markdown("<h2>管理者画面</h2>", unsafe_allow_html=True)
    pw = st.text_input("パスワード", type="password")
    
    if pw == "hotta-admin":
        st.write("")
        # 最新の履歴をJSONから読み込む（スマホからのデータ同期）
        st.session_state.history = load_history()
        
        if not st.session_state.history:
            st.markdown("<p style='color: #86868b;'>保存または再作成されたデータはありません。</p>", unsafe_allow_html=True)
        else:
            st.write(f"記録数: {len(st.session_state.history)}件")
            for log in reversed(st.session_state.history):
                st.markdown("<div style='padding: 24px; background-color: #ffffff; border: 1px solid #e5e5ea; border-radius: 16px; margin-bottom: 24px;'>", unsafe_allow_html=True)
                
                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    st.markdown("<p style='font-size:12px; color:#86868b; margin-bottom:4px;'>ベース画像</p>", unsafe_allow_html=True)
                    if "base_img_b64" in log:
                        st.image(b64_to_pil(log["base_img_b64"]), use_container_width=True)
                    else:
                        st.caption("※旧データ")
                with img_col2:
                    st.markdown("<p style='font-size:12px; color:#86868b; margin-bottom:4px;'>生成結果</p>", unsafe_allow_html=True)
                    if "gen_img_b64" in log:
                        st.image(b64_to_pil(log["gen_img_b64"]), use_container_width=True)
                
                st.write("")
                st.markdown(f"<span style='font-weight:500;'>設定詳細:</span> {log['desc']}", unsafe_allow_html=True)
                st.markdown(f"<span style='font-weight:500;'>評価:</span> {log['rating']} / 5", unsafe_allow_html=True)
                st.markdown(f"<span style='font-weight:500;'>アクション:</span> {log['action']}", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    elif pw:
        st.error("パスワードが違います。")
        
    # 戻るボタンは最下部
    st.divider()
    if st.button("戻る", use_container_width=True): go_to('front')
