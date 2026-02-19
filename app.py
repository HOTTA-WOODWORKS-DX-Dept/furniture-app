import streamlit as st
import google.generativeai as genai

st.title("🛠 モデル診断ツール")

# APIキー設定
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.success("✅ APIキーは認識されています")
except:
    st.error("APIキー設定エラー")
    st.stop()

if st.button("いま使えるモデル一覧を表示"):
    try:
        st.write("サーバーに問い合わせ中...")
        models = genai.list_models()
        found_flash = False
        
        st.markdown("### 利用可能なモデル:")
        for m in models:
            # 画像生成やテキスト生成ができるモデルだけ表示
            if 'generateContent' in m.supported_generation_methods:
                st.write(f"- `{m.name}`")
                if "flash" in m.name:
                    found_flash = True
        
        if not found_flash:
            st.error("⚠️ `gemini-1.5-flash` がリストにありません。requirements.txt が読み込まれていない可能性が高いです。")
            st.info("対策: GitHubのファイル名が `requirements.txt` (すべて小文字) か確認してください。")
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
