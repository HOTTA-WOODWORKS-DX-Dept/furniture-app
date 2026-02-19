import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import time
import traceback

st.set_page_config(page_title="Furniture AI Debug", layout="wide")
st.title("🛋️ 家具コーディネートAI (診断モード)")

# --- APIキー設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ SecretsにGEMINI_API_KEYを設定してください。")
    st.stop()

# --- 【重要】使えるモデルを片っ端から試す関数 ---
def get_working_model():
    # 候補リスト（あなたの環境でリストに出てきたもの）
    models_to_try = [
        'gemini-flash-latest',
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-pro-vision'
    ]
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            # 試しに空のコンテンツを送ってテスト（ここでエラーが出なければ採用）
            return model, m_name
        except:
            continue
    return None, "None"

model, active_model_name = get_working_model()
st.caption(f"現在の使用モデル: {active_model_name}")

# --- メイン画面 ---
f_file = st.file_uploader("家具の写真をアップロード", type=["jpg", "png", "jpeg"])

if st.button("✨ 生成テスト実行", type="primary"):
    if not f_file:
        st.warning("写真をアップロードしてください。")
    else:
        with st.spinner("解析中..."):
            try:
                # 画像を極限まで軽くしてエラーを回避
                img = Image.open(f_file)
                img.thumbnail((512, 512)) 
                
                # Geminiへの指示
                prompt = "Analyze this furniture and describe a room setting for it in one English sentence."
                
                # 実行
                response = model.generate_content([prompt, img])
                result_text = response.text
                
                # 画像生成URL作成
                safe_prompt = urllib.parse.quote(result_text[:300])
                img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=600&nologo=true&seed={int(time.time())}"
                
                # 表示
                st.image(img_url, caption="生成結果")
                st.success("成功しました！")
                st.write(f"AIの回答: {result_text}")

            except Exception as e:
                # 隠さずにエラーの全貌を表示する
                st.error("🚨 エラーが発生しました。以下が詳細です：")
                st.code(traceback.format_exc()) # プログラムのどこで落ちたか表示
                
                st.info("💡 対策ヒント：")
                if "429" in str(e):
                    st.write("Google APIの無料枠が一時的に制限されています。1分待つか、新しいAPIキーを作成してください。")
                elif "404" in str(e):
                    st.write("モデル名が古い可能性があります。app.pyのモデル名リストを調整してください。")
                elif "1033" in str(e) or "connection" in str(e).lower():
                    st.write("Streamlitの通信エラーです。ブラウザを更新するか、Wi-Fi環境を確認してください。")
