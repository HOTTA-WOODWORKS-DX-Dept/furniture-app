import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import io
import time

# --- ページ設定 ---
st.set_page_config(page_title="Furniture AI Studio", layout="wide")

# デザイン調整
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #0068C9; color: white; }
    .reportview-container { background: #f0f2f6; }
</style>
""", unsafe_allow_html=True)

st.title("🛋️ 家具コーディネートAI")
st.caption("通信エラー対策済み・軽量版プロトタイプ")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

# --- 画像を軽くする関数 (1033エラー対策) ---
def resize_image(uploaded_file, max_size=800):
    if uploaded_file is None:
        return None
    img = Image.open(uploaded_file)
    # アスペクト比を維持してリサイズ
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    return img

# --- モデル設定（安定版を優先） ---
@st.cache_resource
def load_model():
    # 1.5-flash は無料枠が最も安定しており、かつ高速です
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_model()

# --- メイン画面構成 ---
tab1, tab2 = st.tabs(["アプリ本体", "管理者コンソール"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. 家具と素材の登録")
        # ① 家具の撮影・アップロード
        f_file = st.file_uploader("家具の写真 (スマホ撮影OK)", type=["jpg", "jpeg", "png"], key="f_up")
        # ② 家具の種類
        f_type = st.selectbox("家具の種類", ["ソファ", "チェア", "テーブル", "ベッド", "収納棚"])
        
        # ③ メイン色（生地など）
        fabric_file = st.file_uploader("生地・メイン色の写真 (任意)", type=["jpg", "jpeg", "png"], key="m_up")
        
        # ④ サブカラー（木部など）
        wood_color = st.selectbox("木部・フレームの色", ["指定なし", "ナチュラル", "ウォールナット", "ホワイト", "ブラック"])

    with col2:
        st.subheader("2. お部屋の設定")
        # ⑤ 置きたい部屋
        room = st.selectbox("置きたい部屋", ["リビング", "ダイニング", "寝室", "子供部屋", "書斎"])
        # ⑥ テイスト・色
        style = st.selectbox("テイスト", ["北欧モダン", "ナチュラル", "ヴィンテージ", "インダストリアル", "和モダン"])
        floor = st.selectbox("床の色", ["ライトブラウン", "ダークブラウン", "ホワイトタイル", "グレー"])
        wall = st.selectbox("壁の色", ["ホワイト", "ライトグレー", "ベージュ", "ブルー(アクセント)"])

        st.divider()
        # ⑦ 生成実行
        generate_btn = st.button("✨ コーディネート画像を生成")

    # 生成処理
    if generate_btn:
        if not f_file:
            st.warning("家具の写真をアップロードしてください。")
        else:
            with st.spinner("AIがコーディネートを分析中..."):
                try:
                    # 1033対策：画像をリサイズして通信量を減らす
                    low_res_f = resize_image(f_file)
                    
                    # プロンプト作成
                    prompt = f"Create a high-quality interior photography prompt. Action: Place the {f_type} from the image into a {style} {room}. Details: {floor} floor, {wall} walls, {wood_color} wood parts. Photorealistic, 8k, natural lighting. Output ONLY the English prompt."
                    
                    inputs = [prompt, low_res_f]
                    if fabric_file:
                        inputs.append(resize_image(fabric_file))
                    
                    # Gemini実行
                    response = model.generate_content(inputs)
                    eng_prompt = response.text.replace('\n', ' ').strip()
                    
                    # 画像生成エンジン(Pollinations)へ
                    safe_prompt = urllib.parse.quote(eng_prompt[:400])
                    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
                    
                    # ⑧ 結果表示
                    st.divider()
                    st.subheader("🖼️ 生成されたコーディネート")
                    st.image(img_url, use_container_width=True)
                    
                    # いいねボタン
                    if st.button("❤️ いいね！"):
                        st.toast("ありがとうございます！")
                        # 本来はここでDBに保存
                        if 'history' not in st.session_state:
                            st.session_state.history = []
                        st.session_state.history.append({"time": time.ctime(), "style": style, "room": room})

                except Exception as e:
                    st.error(f"エラーが発生しました。時間を置いて再度お試しください。")
                    st.caption(f"Detail: {e}")

# --- 管理者コンソール (ログイン機能) ---
with tab2:
    st.subheader("🔒 管理者メニュー")
    pw = st.text_input("パスワードを入力", type="password")
    if pw == "admin123": # 任意のパスワード
        st.success("ログイン中")
        if 'history' in st.session_state:
            st.write("生成ログ (このセッション中のみ)")
            st.table(st.session_state.history)
        else:
            st.info("まだ生成履歴はありません。")
    elif pw:
        st.error("パスワードが違います")
