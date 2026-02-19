import streamlit as st
import requests
import json
import base64
import io
from PIL import Image
from rembg import remove # 背景削除ライブラリ

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio (Composite)", layout="wide")
st.title("🛋️ Room AI Studio (Virtual Staging)")
st.caption("商品をそのまま使い、背景だけを変える「合成モード」")

# --- APIキー確認 ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Secretsに APIキー が設定されていません。")
        st.stop()
except Exception as e:
    st.error(f"設定エラー: {e}")
    st.stop()

# --- 画像処理関数群 ---

# 1. 自動背景切り抜き
def remove_background(input_image):
    # 処理負荷軽減のためリサイズ
    input_image.thumbnail((1000, 1000))
    # rembgで背景削除
    output_image = remove(input_image)
    return output_image

# 2. 画像合成（背景の上に家具を乗せる）
def composite_images(background, foreground):
    bg_w, bg_h = background.size
    fg_w, fg_h = foreground.size
    
    # 家具を背景のサイズに合わせて調整 (背景の幅の70%くらいにする)
    scale = 0.7
    new_w = int(bg_w * scale)
    aspect_ratio = fg_h / fg_w
    new_h = int(new_w * aspect_ratio)
    
    resized_fg = foreground.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 中央・下部に配置
    x = (bg_w - new_w) // 2
    y = bg_h - new_h - 50 # 床から少し浮かせるか、ギリギリに置く
    
    # 合成
    background.paste(resized_fg, (x, y), resized_fg)
    return background

# 3. Google API呼び出し
def generate_background_image(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"}
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        if 'predictions' in result:
            b64_data = result['predictions'][0]['bytesBase64Encoded']
            return Image.open(io.BytesIO(base64.b64decode(b64_data)))
    else:
        st.error(f"背景生成エラー: {response.text}")
        return None

# --- メイン画面 ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. 商品写真")
    uploaded_file = st.file_uploader("家具の写真をアップロード", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        original_img = Image.open(uploaded_file)
        st.image(original_img, width=300, caption="元画像")

with col2:
    st.subheader("2. 背景設定")
    room = st.selectbox("部屋", ["リビング", "ダイニング", "寝室", "オフィス"])
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "インダストリアル", "和モダン", "白基調のシンプル"])
    floor = st.selectbox("床材", ["オークフローリング", "コンクリート", "カーペット", "畳"])
    
    st.divider()
    generate_btn = st.button("✨ 合成スタート", type="primary")

# --- 実行ロジック ---
if generate_btn:
    if not uploaded_file:
        st.warning("写真をアップロードしてください")
    else:
        status = st.empty()
        status.info("✂️ 家具を切り抜いています...")
        
        try:
            # 1. 背景削除
            original_img = Image.open(uploaded_file)
            cutout_img = remove_background(original_img)
            
            # 切り抜き結果の確認表示（サイドバーなどに出しても良いが、一旦メインに）
            with st.expander("切り抜き結果を確認"):
                st.image(cutout_img, width=200, caption="切り抜かれた家具")
            
            status.info(f"🎨 {style}な{room}の背景を描いています...")
            
            # 2. 背景画像の生成 (家具については触れず、部屋だけを描かせる)
            bg_prompt = f"A professional interior photography of an empty {style} {room} with {floor}. The room is spacious, well-lit with natural soft lighting coming from a window. Photorealistic, 4k, architectural digest style. Low angle shot showing the floor clearly."
            
            background_img = generate_background_image(bg_prompt)
            
            if background_img:
                status.info("🔨 合成処理中...")
                
                # 3. 合成
                final_image = composite_images(background_img.copy(), cutout_img)
                
                status.success("完成しました！")
                st.image(final_image, use_container_width=True, caption="合成イメージ")
                
                # ダウンロードボタン
                buf = io.BytesIO()
                final_image.save(buf, format="PNG")
                byte_im = buf.getvalue()
                st.download_button("画像をダウンロード", data=byte_im, file_name="room_ai_result.png", mime="image/png")
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.info("※画像サイズが大きすぎるとメモリ不足で止まることがあります。")
