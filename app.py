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
# 💅 安全なベースCSS
# ==========================================
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Hiragino Kaku Gothic ProN", sans-serif; color: #1d1d1f; background-color: #fbfbfd; }
    h1, h2, h3, h4 { font-weight: 600; letter-spacing: -0.02em; }
    *:focus, *:active { outline: none !important; box-shadow: none !important; }

    /* アップローダーの日本語化 */
    [data-testid="stFileUploadDropzone"] div div::before { content: "ここに画像をドラッグ＆ドロップ、またはファイルを選択"; display: block; font-size: 14px; color: #1d1d1f; font-weight: 500; text-align: center; margin-bottom: 10px; }
    [data-testid="stFileUploadDropzone"] div div span { display: none; }
    [data-testid="stFileUploadDropzone"] small { display: none; }
    
    /* 生成ボタン */
    button[kind="primary"] { background-color: #1d1d1f !important; color: #ffffff !important; border: none !important; border-radius: 24px !important; padding: 14px 24px !important; font-size: 16px !important; font-weight: 600 !important; transition: transform 0.2s ease; }
    button[kind="primary"]:hover { opacity: 0.8; transform: scale(1.02); }

    /* 通常ボタン（選択肢用） */
    button[kind="secondary"] { border-radius: 8px !important; border: 1px solid #d2d2d7 !important; background-color: #ffffff !important; color: #1d1d1f !important; font-size: 12px !important; padding: 4px 8px !important; }
    
    /* スライダーをグレーに */
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stSliderTrack"] > div:first-child { background-color: #86868b !important; }
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] { background-color: #1d1d1f !important; border-color: #1d1d1f !important; }

    hr { margin: 40px 0; border-color: #e5e5ea; }
    .section-title { font-size: 16px; font-weight: 600; color: #1d1d1f; margin-bottom: 12px; margin-top: 32px; }
    .helper-text { font-size: 13px; color: #86868b; margin-top: -10px; margin-bottom: 24px; }
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

# --- 安全なUI部品関数 (エラーフリー版) ---
def render_color_grid(options_dict, state_key):
    items = list(options_dict.items())
    for i in range(0, len(items), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(items):
                name, color = items[i + j]
                with cols[j]:
                    st.markdown(f'<div style="background-color:{color}; width:100%; aspect-ratio:1/1; border-radius:8px; border:1px solid #e5e5ea; margin-bottom:8px;"></div>', unsafe_allow_html=True)
                    if st.button(name, key=f"btn_{state_key}_{name}", use_container_width=True):
                        st.session_state[state_key] = {"name": name, "val": color, "type": "preset"}
                        st.rerun()

def render_style_grid():
    items = list(STYLES.items())
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(items):
                name, url = items[i + j]
                with cols[j]:
                    st.markdown(f'<div style="background-image:url({url}); background-size:cover; width:100%; aspect-ratio:1/1; border-radius:12px; margin-bottom:8px;"></div>', unsafe_allow_html=True)
                    if st.button(name, key=f"btn_style_{name}", use_container_width=True):
                        st.session_state.style = {"name": name, "url": url, "type": "style"}
                        st.rerun()

def render_selected(label, selection, state_key):
    st.markdown(f"<div class='section-title'>{label}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 3, 2])
    with c1:
        if selection["type"] == "preset":
            st.markdown(f'<div style="background-color:{selection["val"]}; width:100%; aspect-ratio:1/1; border-radius:8px; border:1px solid #e5e5ea;"></div>', unsafe_allow_html=True)
        elif selection["type"] == "style":
            st.markdown(f'<div style="background-image:url({selection["url"]}); background-size:cover; width:100%; aspect-ratio:1/1; border-radius:8px;"></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background-color:#f5f5f7; width:100%; aspect-ratio:1/1; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:10px; color:#86868b; border:1px solid #e5e5ea;">画像</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"<p style='font-size:14px; margin-top:8px; font-weight:500;'>{selection['name']}</p>", unsafe_allow_html=True)
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
    
    col1, col
