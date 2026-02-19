import streamlit as st
import requests
import json
import base64
import time
import urllib.parse

# --- ページ設定 ---
st.set_page_config(page_title="Room AI (Direct)", layout="wide")
st.title("🛋️ Room AI Studio")
st.caption("REST APIモード - 1033エラー回避版")

# --- APIキー確認 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("SecretsにAPIキーがありません")
    st.stop()

# --- 画像をBase64に変換する関数 ---
def image_to_base64(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode('utf-8')
    return base64_str

# --- メイン画面 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 家具画像")
    f_file = st.file_uploader("家具をアップロード", type=["jpg", "png", "jpeg"])
    if f_file:
        st.image(f_file, width=300, caption="送信画像")

with col2:
    st.subheader("2. 設定")
    room = st.selectbox("部屋", ["リビング", "ダイニング", "寝室"])
    style = st.selectbox("スタイル", ["北欧モダン", "ヴィンテージ", "インダストリアル"])
    
    generate_btn = st.button("✨ 生成スタート", type="primary")

if generate_btn:
    if not f_file:
        st.warning("画像をアップロードしてください")
    else:
        status = st.empty()
        status.info("🚀 Googleサーバーへ問い合わせ中...")
        
        try:
            # 1. 画像データ準備
            base64_image = image_to_base64(f_file)
            mime_type = f_file.type
            
            # 2. モデルURL (ここを修正しました！)
            # gemini-1.5-flash ではなく、実績のある gemini-flash-latest を指定
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
            
            # 3. データ作成
            payload = {
                "contents": [{
                    "parts": [
                        {"text": f"Describe this furniture shape and write a short English prompt to place it in a {style} {room}. Output ONLY the prompt. No intro."},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_image
                            }
                        }
                    ]
                }]
            }
            headers = {'Content-Type': 'application/json'}
            
            # 4. 送信実行
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # 5. 結果処理
            if response.status_code == 200:
                result = response.json()
                try:
                    # テキストを取り出す
                    eng_prompt = result['candidates'][0]['content']['parts'][0]['text']
                    clean_prompt = eng_prompt.replace('\n', ' ').strip()[:400]
                    
                    status.success("解析成功！画像を表示します")
                    
                    # 画像生成URL作成
                    encoded = urllib.parse.quote(clean_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=768&nologo=true&seed={int(time.time())}&model=flux"
                    
                    # 表示
                    st.image(img_url, use_container_width=True)
                    st.markdown(f"[画像が表示されない場合はこちら]({img_url})")
                    
                except Exception as parse_error:
                    st.error("AIの応答解析に失敗しました")
                    st.write(result)
            else:
                # エラー時の詳細表示
                st.error(f"APIエラー: {response.status_code}")
                st.write(response.text)
                
        except Exception as e:
            st.error(f"通信エラー: {e}")
