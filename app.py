import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Model Checker", layout="wide")
st.title("🛠️ Gemini API モデル診断")
st.caption("あなたのAPIキーで利用可能な全モデルをリストアップします")

# APIキー設定
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("Secretsに APIキー が設定されていません。")
        st.stop()
except Exception as e:
    st.error(f"API設定エラー: {e}")
    st.stop()

# --- 診断実行ボタン ---
if st.button("モデル一覧を取得する", type="primary"):
    try:
        st.info("問い合わせ中...")
        
        # 利用可能なモデルを全取得
        models = list(genai.list_models())
        
        # 結果を表示するためのリスト
        text_models = []
        image_models = []
        vision_models = []
        
        for m in models:
            # モデル名とサポート機能を確認
            methods = m.supported_generation_methods
            name = m.name
            
            # 分類
            if 'generateContent' in methods:
                if 'vision' in name or 'gemini' in name:
                    vision_models.append(name)
                else:
                    text_models.append(name)
            
            if 'predict' in methods or 'generateImage' in methods or 'image' in name:
                image_models.append(name)
        
        # --- 結果表示 ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 テキスト・画像認識 (Gemini)")
            for m in vision_models:
                st.code(m)
                
        with col2:
            st.subheader("🎨 画像生成 (Imagen)")
            if image_models:
                for m in image_models:
                    st.code(m)
            else:
                st.warning("画像生成用モデルが見つかりませんでした。")
                st.caption("※有料プランでも、画像生成API（Imagen）は別途有効化が必要な場合があります。")

        st.success("取得完了")
        
    except Exception as e:
        st.error("エラーが発生しました")
        st.error(e)
        st.write("対策: APIキーが正しいか、Google AI StudioでAPIが有効になっているか確認してください。")
