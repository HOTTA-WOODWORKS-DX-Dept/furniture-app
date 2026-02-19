import streamlit as st
import requests
import json
import base64
import io
import time
from PIL import Image

# --- ページ設定 ---
st.set_page_config(page_title="Room AI Studio", layout="wide")
st.title("🛋️ Room AI Studio (Google Native)")
st.caption("Powered by Google Gemini & Imagen 4.0 Fast")

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

# --- 画像処理関数 ---
def image_to_base64(uploaded_file):
    img = Image.open(uploaded_file)
    # 通信負荷を下げるためリサイズ
    img.thumbnail((800, 800))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 【重要】API通信関数（自動リトライ機能付き） ---
def call_google_api(url, payload, description):
    headers = {'Content-Type': 'application/json'}
    max_retries = 3 # 3回まで再挑戦する
    
    for i in range(max_retries):
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # 429エラーなら、少し待ってから再挑戦
            wait_time = (i + 1) * 2 # 2秒, 4秒, 6秒と待つ時間を増やす
            st.warning(f"混雑中... {wait_time}秒待機して再試行します ({i+1}/{max_retries})")
            time.sleep(wait_time)
            continue
        else:
            # その他のエラーは即座に報告
            st.error(f"{description} エラー: {response.status_code}")
            st.code(response.text)
            return None
            
    st.error(f"{description} 失敗: リトライ回数を超えました。")
    return None

# --- メイン画面 ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. 家具を撮影")
    uploaded_file = st.file_uploader("家具の写真", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, width=300, caption="解析対象")

with col2:
    st.subheader("2. コーディネート設定")
    room = st.selectbox("部屋", ["リビング", "ダイニング", "寝室", "オフィス"])
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "インダストリアル", "和モダン"])
    
    st.divider()
    generate_btn = st.button("✨ 生成スタート", type="primary")

# --- 実行ロジック ---
if generate_btn:
    if not uploaded_file:
        st.warning("写真をアップロードしてください")
    else:
        status = st.empty()
        status.info("🚀 家具を分析中... (Gemini Flash)")
        
        try:
            # ---------------------------------------------------------
            # Step 1: Gemini (Vision) でプロンプト作成
            # ---------------------------------------------------------
            # 安定版の 'gemini-flash-latest' を使用
            vision_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
            
            base64_img = image_to_base64(uploaded_file)
            
            vision_payload = {
                "contents": [{
                    "parts": [
                        {"text": f"Describe this furniture. Then write a high-quality English prompt for an image generator to place this furniture in a {style} {room}. The prompt should specify 'cinematic lighting, photorealistic, 4k'. Output ONLY the prompt text."},
                        {"inline_data": {"mime_type": "image/jpeg", "data": base64_img}}
                    ]
                }]
            }
            
            vision_result = call_google_api(vision_url, vision_payload, "Gemini Vision")
            
            if vision_result:
                # プロンプト抽出
                try:
                    prompt_text = vision_result['candidates'][0]['content']['parts'][0]['text']
                    clean_prompt = prompt_text.replace('\n', ' ').strip()
                    
                    status.info("🎨 画像を描画中... (Imagen 4.0 Fast)")
                    
                    # ---------------------------------------------------------
                    # Step 2: Imagen (Generation) で画像生成
                    # ---------------------------------------------------------
                    # 高速版の 'imagen-4.0-fast-generate-001' を使用
                    imagen_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={api_key}"
                    
                    imagen_payload = {
                        "instances": [
                            {"prompt": clean_prompt}
                        ],
                        "parameters": {
                            "sampleCount": 1,
                            "aspectRatio": "4:3"
                        }
                    }
                    
                    imagen_result = call_google_api(imagen_url, imagen_payload, "Imagen Generation")
                    
                    if imagen_result:
                        # 画像データ抽出
                        if 'predictions' in imagen_result:
                            b64_data = imagen_result['predictions'][0]['bytesBase64Encoded']
                            image_data = base64.b64decode(b64_data)
                            final_image = Image.open(io.BytesIO(image_data))
                            
                            status.success("生成完了！")
                            st.image(final_image, use_container_width=True, caption=f"Generated by Google Imagen 4.0 ({style})")
                            
                            with st.expander("プロンプト詳細"):
                                st.write(clean_prompt)
                        else:
                            st.error("画像データの取得に失敗しました。")
                            st.write(imagen_result)
                            
                except Exception as e:
                    st.error(f"データ解析エラー: {e}")
                    
        except Exception as
