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
COLORS_FABRIC = {"ホワイト":"#F8F8F8", "アイボリー":"#FFFFF0", "ベージュ":"
