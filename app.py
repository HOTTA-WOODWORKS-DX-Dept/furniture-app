import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import io
import time
import base64
import sqlite3
import os

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="centered", initial_sidebar_state="collapsed")

# ==========================================
# 💾 データベース設定 (スマホ・PC間 同期用)
# ==========================================
DB_FILE = "room_ai_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id TEXT PRIMARY KEY, timestamp REAL, base_img TEXT, gen_img TEXT, desc TEXT, rating INTEGER, action TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM history WHERE id=?", (data['id'],))
    if c.fetchone():
        c.execute("UPDATE history SET rating=?, action=? WHERE id=?", (data['rating'], data['action'], data['id']))
    else:
        c.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (data['id'], data['timestamp'], data['base_img_b64'], data['gen_img_b64'], data['desc'], data['rating'], data['action']))
    conn.commit()
    conn.close()

def load_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY timestamp ASC")
    rows = c.fetchall()
    conn.close()
    
    history_list = []
    for row in rows:
        history_list.append({
            'id': row[0], 'timestamp': row[1], 'base_img_b64': row[2], 
            'gen_img_b64': row[3], 'desc': row[4], 'rating': row[5], 'action': row[6]
        })
    return history_list

init_db()

# ==========================================
# 🎨 カラー・画像データ
# ==========================================
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

# ==========================================
# 💅 動的CSS生成 (ボタンの画像化ハック)
# ==========================================
dynamic_css = ""

# フロントページ用
dynamic_css += """
div[data-testid="element-container"]:has(.marker-front-sofa) + div[data-testid="element-container"] button { background: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url('https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&q=80&w=500&h=500') center/cover !important; width: 100% !important; aspect-ratio: 1/1 !important; border-radius: 16px !important; border: none !important; position: relative !important; }
div[data-testid="element-container"]:has(.marker-front-sofa) + div[data-testid="element-container"] button p { display: none !important; }
div[data-testid="element-container"]:has(.marker-front-sofa) + div[data-testid="element-container"] button::after { content: 'SOFA'; color: white; font-size: 24px; font-weight: bold; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }

div[data-testid="element-container"]:has(.marker-front-dining) + div[data-testid="element-container"] button { background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1577140917170-285929fb55b7?auto=format&fit=crop&q=80&w=500&h=500') center/cover !important; width: 100% !important; aspect-ratio: 1/1 !important; border-radius: 16px !important; border: none !important; cursor: default !important; position: relative !important; }
div[data-testid="element-container"]:has(.marker-front-dining) + div[data-testid="element-container"] button p { display: none !important; }
div[data-testid="element-container"]:has(.marker-front-dining) + div[data-testid="element-container"] button::after { content: 'Coming Soon\\A DINING'; white-space: pre; text-align: center; color: white; font-size: 20px; font-weight: bold; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
"""

# 素材・内装用の色ブロック
def add_color_css(prefix, color_dict):
    css = ""
    for name, hexcode in color_dict.items():
        css += f"""
        div[data-testid="element-container"]:has(.marker-{prefix}-{name}) + div[data-testid="element-container"] button {{ background-color: {hexcode} !important; width: 100% !important; aspect-ratio: 1/1 !important; border-radius: 8px !important; border: 1px solid #e5e5ea !important; padding: 0 !important; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.03) !important; position: relative !important; overflow: visible !important; }}
        div[data-testid="element-container"]:has(.marker-{prefix}-{name}) + div[data-testid="element-container"] button p {{ display: none !important; }}
        div[data-testid="element-container"]:has(.marker-{prefix}-{name}) + div[data-testid="element-container"] button::after {{ content: '{name}'; position: absolute; bottom: -24px; left: 50%; transform: translateX(-50%); font-size: 11px; color: #515154; white-space: nowrap; font-weight: normal; }}
        """
    return css

dynamic_css += add_color_css("FB", COLORS_FABRIC)
dynamic_css += add_color_css("LT", COLORS_LEATHER)
dynamic_css += add_color_css("WD", COLORS_WOOD)
dynamic_css += add_color_css("MT", COLORS_METAL)
dynamic_css += add_color_css("IN", COLORS_INT)

# テイスト画像用のブロック
for name, url in STYLES.items():
    dynamic_css += f"""
    div[data-testid="element-container"]:has(.marker-ST-{name}) + div[data-testid="element-container"] button {{ background: url('{url}') center/cover !important; width: 100% !important; aspect-ratio: 1/1 !important; border-radius: 12px !important; border: none !important; padding: 0 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; position: relative !important; overflow: visible !important; }}
    div[data-testid="element-container"]:has(.marker-ST-{name}) + div[data-testid="element-container"] button p {{ display: none !important; }}
    div[data-testid="element-container"]:has(.marker-ST-{name}) + div[data-testid="element-container"] button::after {{ content: '{name}'; position: absolute; bottom: -24px; left: 50%; transform: translateX(-50%); font-size: 11px; color: #515154; white-space: nowrap; font-weight: normal; }}
    """

# --- ベースCSS ---
st.markdown(f"""
<style>
    /* フォント・背景 */
    html, body, [class*="css"] {{ font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Kaku Gothic ProN", sans-serif; color: #1d1d1f; background-color: #fbfbfd; }}
    h1, h2, h3, h4 {{ font-weight: 600; letter-spacing: -0.02em; }}
    *:focus, *:active {{ outline: none !important; box-shadow: none !important; }}

    /* ファイルアップローダーの日本語化 */
    [data-testid="stFileUploadDropzone"] div div::before {{ content: "ここに画像をドラッグ＆ドロップ、またはファイルを選択"; display: block; font-size: 14px; color: #1d1d1f; font-weight: 500; text-align: center; margin-bottom: 10px; }}
    [data-testid="stFileUploadDropzone"] div div span {{ display: none; }}
    [data-testid="stFileUploadDropzone"] small {{ display: none; }}
    
    /* 生成ボタン (ブルーを廃止しダークグレーへ) */
    button[kind="primary"] {{ background-color: #1d1d1f !important; color: #ffffff !important; border: none !important; border-radius: 24px !important; padding: 14px 24px !important; font-size: 16px !important; font-weight: 600 !important; transition: transform 0.2s ease; }}
    button[kind="primary"]:hover {{ opacity: 0.8; transform: scale(1.02); }}

    /* 通常・戻るボタン */
    button[kind="secondary"]:not(:has(p:contains('_'))) {{ border-radius: 12px !important; border: 1px solid #d2d2d7 !important; background-color: #ffffff !important; color: #1d1d1f !important; font-weight: 500 !important; }}
    
    /* スワイプバー（スライダー）の色をグレーに */
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stSliderTrack"] > div:first-child {{ background-color: #86868b !important; }}
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {{ background-color: #1d1d1f !important; border-color: #1d1d1f !important; }}

    hr {{ margin: 40px 0; border-color: #e5e5ea; }}
    .section-title {{ font-size: 16px; font-weight: 600; color: #1d1d1f; margin-bottom: 12px; margin-top: 32px; }}
    .helper-text {{ font-size: 13px; color: #86868b; margin-top: -10px; margin-bottom: 24px; }}
    .select-prompt {{ font-size: 14px; font-weight: 500; color: #515154; margin-bottom: 12px; margin-top: 8px; }}
</style>
{dynamic_css}
""", unsafe_allow_html=True)

# --- API設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-3-pro-image-preview')
except:
    st.error("API設定を確認してください。")
    st.stop()

# --- 画像処理関数 ---
def pil_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def b64_to_pil(b64_str):
    return Image.open(io.BytesIO(base64.b64decode(b64_str)))

def crop_to_4_3_and_watermark(img):
    w, h = img.size
    target_ratio = 4 / 3
    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        img = img.crop(((w - new_w) / 2, 0, (w - new_w) / 2 + new_w, h))
    else:
        new_h = int(w / target_ratio)
        img = img.crop((0, (h - new_h) / 2, w, (h - new_h) / 2 + new_h))
    
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("LiberationSans-Regular.ttf", int(img.height * 0.025)) 
    except: font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "HOTTA WOODWORKS-DX", font=font)
    x, y = img.width - (bbox[2]-bbox[0]) - 20, img.height - (bbox[3]-bbox[1]) - 20
    draw.text((x+1, y+1), "HOTTA WOODWORKS-DX", font=font, fill=(0,0,0,100))
    draw.text((x, y), "HOTTA WOODWORKS-DX", font=font, fill=(255,255,255,220))
    return img

# --- セッション状態 ---
if 'page' not in st.session_state: st.session_state.page = 'front'
if 'gallery' not in st.session_state: st.session_state.gallery = [] 
if 'auto_gen' not in st.session_state: st.session_state.auto_gen = False
for k in ['fabric', 'frame', 'style', 'floor', 'wall', 'fitting', 'up_fab', 'up_frame']:
    if k not in st.session_state: st.session_state[k] = None

def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.gallery = []
    for k in ['fabric', 'frame', 'style', 'floor', 'wall', 'fitting', 'up_fab', 'up_frame']:
        st.session_state[k] = None
    st.rerun()

# --- UI部品関数 (1/4サイズ グリッド) ---
def render_grid(options_dict, prefix, state_key):
    items = list(options_dict.items())
    # 1/4サイズ（4列配置）
    for i in range(0, len(items), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(items):
                name, val = items[i + j]
                with cols[j]:
                    st.markdown(f'<div class="marker-{prefix}-{name}" style="display:none;"></div>', unsafe_allow_html=True)
                    if st.button(f"{prefix}_{name}", key=f"btn_{prefix}_{name}"):
                        st.session_state[state_key] = {"name": name, "val": val, "type": "preset"}
                        st.rerun()
                    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True) # 文字用スペース

def render_selected(label, selection, state_key):
    st.markdown(f"<div class='section-title'>{label}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 3, 2])
    with c1:
        if selection["type"] == "preset":
            if "http" in selection["val"]:
                st.markdown(f'<div style="background-image:url({selection["val"]}); background-size:cover; width:100%; aspect-ratio:1/1; border-radius:8px;"></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background-color:{selection["val"]}; width:100%; aspect-ratio:1/1; border-radius:8px; border:1px solid #e5e5ea;"></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background-color:#f5f5f7; width:100%; aspect-ratio:1/1; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:10px; color:#86868b; border:1px solid #e5e5ea;">独自画像</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p style='font-size:14px; margin-top:8px;'>{selection['name']}</p>", unsafe_allow_html=True)
    with c3:
        if st.button("変更", key=f"chg_{state_key}"):
            st.session_state[state_key] = None
            if state_key == "floor": st.session_state.wall = st.session_state.fitting = None
            elif state_key == "wall": st.session_state.fitting = None
            st.rerun()

# ==========================================
# 🏠 1. フロントページ
# ==========================================
if st.session_state.page == 'front':
    st.markdown("<h1 style='margin-top: 40px;'>Room AI Studio</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="marker-front-sofa" style="display:none;"></div>', unsafe_allow_html=True)
        if st.button("FRONT_SOFA", key="f_sofa"): go_to('sofa')
    with col2:
        st.markdown('<div class="marker-front-dining" style="display:none;"></div>', unsafe_allow_html=True)
        st.button("FRONT_DINING", key="f_dining", disabled=True)
    
    st.divider()
    col_admin, _ = st.columns([1, 2])
    with col_admin:
        if st.button("管理者画面", use_container_width=True): go_to('admin')

# ==========================================
# 🛋️ 2. ソファ・コーディネート画面
# ==========================================
elif st.session_state.page == 'sofa':
    st.markdown("<h2>家具の設定</h2>", unsafe_allow_html=True)
    st.markdown("<div class='helper-text'>ベースとなる家具の写真をアップロードし、各素材や空間のテイストを選択してください。</div>", unsafe_allow_html=True)
    
    f_file = st.file_uploader("ベース画像", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if f_file: st.image(f_file, width=150)
    
    st.divider()

    # --- 素材 ---
    if not st.session_state.fabric:
        st.markdown("<div class='section-title'>張地</div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["布", "革"])
        with t1: render_grid(COLORS_FABRIC, "FB", "fabric")
        with t2: render_grid(COLORS_LEATHER, "LT", "fabric")
        st.write("")
        up_fab = st.file_uploader("独自の画像をアップロード (張地)", type=["jpg", "png"], key="ufab", label_visibility="collapsed")
        if up_fab:
            st.session_state.fabric = {"name": "独自アップロード画像", "val": up_fab, "type": "upload"}
            st.session_state.up_fab = pil_to_b64(Image.open(up_fab))
            st.rerun()
    else:
        render_selected("張地", st.session_state.fabric, "fabric")

    st.write("")
    
    if not st.session_state.frame:
        st.markdown("<div class='section-title'>フレーム</div>", unsafe_allow_html=True)
        t3, t4 = st.tabs(["木材", "金属"])
        with t3: render_grid(COLORS_WOOD, "WD", "frame")
        with t4: render_grid(COLORS_METAL, "MT", "frame")
        st.write("")
        up_frm = st.file_uploader("独自の画像をアップロード (フレーム)", type=["jpg", "png"], key="ufrm", label_visibility="collapsed")
        if up_frm:
            st.session_state.frame = {"name": "独自アップロード画像", "val": up_frm, "type": "upload"}
            st.session_state.up_frame = pil_to_b64(Image.open(up_frm))
            st.rerun()
    else:
        render_selected("フレーム", st.session_state.frame, "frame")

    st.divider()

    # --- 空間 ---
    if not st.session_state.style:
        st.markdown("<div class='section-title'>空間テイスト</div>", unsafe_allow_html=True)
        # スタイル画像も1/4配置
        items = list(STYLES.items())
        for i in range(0, len(items), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(items):
                    name, url = items[i + j]
                    with cols[j]:
                        st.markdown(f'<div class="marker-ST-{name}" style="display:none;"></div>', unsafe_allow_html=True)
                        if st.button(f"ST_{name}", key=f"style_{name}"):
                            st.session_state.style = {"name": name, "url": url, "type": "style"}
                            st.rerun()
                        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
    else:
        render_selected("空間テイスト", st.session_state.style, "style")

    st.write("")

    # --- 内装 ---
    if not st.session_state.floor:
        st.markdown("<div class='select-prompt'>床を選択</div>", unsafe_allow_html=True)
        render_grid(COLORS_INT, "IN", "floor")
    else:
        render_selected("床", st.session_state.floor, "floor")

    if st.session_state.floor:
        if not st.session_state.wall:
            st.markdown("<div class='select-prompt'>壁を選択</div>", unsafe_allow_html=True)
            render_grid(COLORS_INT, "IN", "wall")
        else:
            render_selected("壁", st.session_state.wall, "wall")

    if st.session_state.wall:
        if not st.session_state.fitting:
            st.markdown("<div class='select-prompt'>建具を選択</div>", unsafe_allow_html=True)
            render_grid(COLORS_INT, "IN", "fitting")
        else:
            render_selected("建具", st.session_state.fitting, "fitting")

    st.divider()

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        gen_clicked = st.button("画像を生成", type="primary", use_container_width=True)
    with c_btn2:
        if st.button("設定をリセット", use_container_width=True): go_to('sofa')

    if gen_clicked or st.session_state.auto_gen:
        st.session_state.auto_gen = False
        if not f_file:
            st.error("ベース画像をアップロードしてください。")
        else:
            with st.spinner("AIで画像を生成しています..."):
                try:
                    main_img = Image.open(f_file)
                    
                    fab_p = st.session_state.fabric["name"] if st.session_state.fabric else "appropriate color"
                    frame_p = st.session_state.frame["name"] if st.session_state.frame else "appropriate material"
                    style_p = st.session_state.style["name"] if st.session_state.style else "modern"
                    floor_p = st.session_state.floor["name"] if st.session_state.floor else "matching"
                    wall_p = st.session_state.wall["name"] if st.session_state.wall else "matching"
                    fitting_p = st.session_state.fitting["name"] if st.session_state.fitting else "matching"
                    
                    prompt = f"""
                    GENERATE_IMAGE: Create a highly realistic interior design photo. Aspect Ratio: 4:3.
                    Furniture: The sofa from the first attached image. Maintain exact shape.
                    Upholstery: {fab_p}. Frame/Legs: {frame_p}.
                    Style: {style_p} interior.
                    Interior: Floor: {floor_p}, Walls: {wall_p}, Doors/Fittings: {fitting_p}.
                    """
                    
                    inputs = [prompt, main_img]
                    if st.session_state.up_fab: inputs.append(b64_to_pil(st.session_state.up_fab))
                    if st.session_state.up_frame: inputs.append(b64_to_pil(st.session_state.up_frame))
                    
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
                        final_img = crop_to_4_3_and_watermark(gen_img)
                        new_log = {
                            "id": str(time.time()),
                            "timestamp": time.time(),
                            "base_img_b64": pil_to_b64(main_img.copy()), 
                            "gen_img_b64": pil_to_b64(final_img),
                            "desc": f"{style_p} / 張地:{fab_p} / フレーム:{frame_p}",
                            "rating": 0, "action": "閲覧のみ"
                        }
                        st.session_state.gallery.append(new_log)
                        # 生成された直後もDBに仮保存（スマホから離脱しても残るように）
                        save_to_db(new_log)
                    else:
                        st.error("生成に失敗しました。")
                except Exception as e:
                    st.error(f"エラー: {e}")

    # --- ギャラリー・評価 ---
    if st.session_state.gallery:
        st.divider()
        st.markdown("<h2>生成結果</h2>", unsafe_allow_html=True)
        
        total = len(st.session_state.gallery)
        idx = 0
        if total > 1:
            idx = st.slider("スワイプして履歴を確認", 1, total, total) - 1
            
        res = st.session_state.gallery[idx]
        display_img = b64_to_pil(res["gen_img_b64"])
        
        c_img1, c_img2, c_img3 = st.columns([1, 4, 1])
        with c_img2:
            st.image(display_img, use_container_width=True)
            st.caption(res["desc"])
            
            st.write("")
            st.markdown("<p style='text-align:center; font-weight:600; font-size:14px;'>画像を評価すると保存や再作成出来ます</p>", unsafe_allow_html=True)
            
            # 初期選択なしにするため index=None
            rating = st.radio("評価", [1, 2, 3, 4, 5], index=None, horizontal=True, label_visibility="collapsed", key=f"rate_{res['id']}")
            
            if rating is not None:
                res["rating"] = rating
                st.write("")
                col_a, col_b = st.columns(2)
                with col_a:
                    buf = io.BytesIO()
                    display_img.save(buf, format="PNG")
                    if st.download_button("保存", data=buf.getvalue(), file_name=f"room_ai_{int(time.time())}.png", mime="image/png", use_container_width=True):
                        res["action"] = "保存"
                        save_to_db(res) # DBに同期
                        st.success("保存完了")
                with col_b:
                    if st.button("再作成", use_container_width=True, key=f"retry_{res['id']}"):
                        res["action"] = "再作成"
                        save_to_db(res) # DBに同期
                        st.session_state.auto_gen = True
                        st.rerun()

    st.divider()
    if st.button("フロントページに戻る", use_container_width=True): go_to('front')

# ==========================================
# 🔒 3. 管理者画面 (DBから読み込み)
# ==========================================
elif st.session_state.page == 'admin':
    st.markdown("<h2>管理者画面</h2>", unsafe_allow_html=True)
    pw = st.text_input("パスワード", type="password")
    
    if pw == "hotta-admin":
        st.write("")
        # 常に最新のDBから読み込む（スマホからのデータ同期）
        history_data = load_from_db()
        
        if not history_data:
            st.markdown("<p style='color: #86868b;'>保存されたデータはありません。</p>", unsafe_allow_html=True)
        else:
            st.write(f"記録数: {len(history_data)}件")
            for log in reversed(history_data):
                # 評価が行われたもの、またはアクションがあるものを表示
                st.markdown("<div style='padding: 24px; background-color: #ffffff; border: 1px solid #e5e5ea; border-radius: 16px; margin-bottom: 24px;'>", unsafe_allow_html=True)
                
                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    st.markdown("<p style='font-size:12px; color:#86868b; margin-bottom:4px;'>ベース画像</p>", unsafe_allow_html=True)
                    st.image(b64_to_pil(log["base_img_b64"]), use_container_width=True)
                with img_col2:
                    st.markdown("<p style='font-size:12px; color:#86868b; margin-bottom:4px;'>生成結果</p>", unsafe_allow_html=True)
                    st.image(b64_to_pil(log["gen_img_b64"]), use_container_width=True)
                
                st.write("")
                st.markdown(f"<span style='font-weight:600;'>設定詳細:</span> {log['desc']}", unsafe_allow_html=True)
                # 評価0の場合は「未評価」と表示
                rating_disp = f"{log['rating']} / 5" if log['rating'] > 0 else "未評価"
                st.markdown(f"<span style='font-weight:600;'>評価:</span> {rating_disp}", unsafe_allow_html=True)
                st.markdown(f"<span style='font-weight:600;'>アクション:</span> {log['action']}", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    elif pw:
        st.error("パスワードが違います。")
        
    st.divider()
    if st.button("フロントページに戻る", use_container_width=True): go_to('front')
