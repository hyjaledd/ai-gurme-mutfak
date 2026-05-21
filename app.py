import streamlit as st
import requests

# --- PREMIUM SAYFA AYARLARI ---
st.set_page_config(page_title="AI Gourmet Kitchen", layout="centered", page_icon="👨‍🍳")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
        font-family: 'Poppins', sans-serif;
        color: #f0f2f6;
    }

    h1, h2, h3 { color: #FFBF00 !important; font-weight: 600 !important; }

    /* --- YENİ: SEÇİLİ MALZEME ETİKETLERİNİ ALTIN SARISI YAPMA --- */
    span[data-baseweb="tag"] {
        background-color: #FFBF00 !important;
        color: #000000 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    span[data-baseweb="tag"] span {
        color: #000000 !important; /* Kapatma X işareti için */
    }

    .recipe-card {
        background-color: #161b22;
        padding: 25px;
        border-radius: 0 0 20px 20px;
        border: 1px solid #30363d;
        border-top: none;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    .stButton>button {
        background: linear-gradient(90deg, #FFBF00 0%, #FF8C00 100%);
        color: black !important;
        border: none;
        border-radius: 30px;
        padding: 10px 25px;
        font-weight: 600;
        transition: 0.3s;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(255, 191, 0, 0.4);
    }
    
    .recipe-img {
        width: 100%;
        height: 300px;
        object-fit: cover;
        border-radius: 20px 20px 0 0;
        border: 1px solid #30363d;
        border-bottom: none;
    }
</style>
""", unsafe_allow_html=True)

# --- UYGULAMA HAFIZASI (SESSION STATE) ---
if "aktif_menü" not in st.session_state:
    st.session_state.aktif_menü = None
if "gosterilen_tarifler" not in st.session_state:
    st.session_state.gosterilen_tarifler = []

st.title("👨‍🍳 AI Gourmet Kitchen")
st.write("Profesyonel yapay zeka şefiyle mutfağınızda bir sanat eseri yaratın.")

MALZEMELER = [
    "Yumurta", "Süt", "Yoğurt", "Beyaz Peynir", "Kaşar Peyniri", 
    "Tereyağı", "Zeytinyağı", "Ayçiçek Yağı", "Un", "Toz Şeker", 
    "Tuz", "Karabiber", "Pul Biber", "Kimyon", "İsot", 
    "Kekik", "Nane", "Sumak", "Domates Salçası", "Biber Salçası", 
    "Domates", "Kuru Soğan", "Sarımsak", "Sivri Biber", "Kapya Biber", 
    "Patates", "Limon", "Maydanoz", "Pirinç", "Pilavlık Bulgur", 
    "İnce Bulgur", "Kırmızı Mercimek", "Nohut", "Kuru Fasulye", "Makarna", 
    "Tel Şehriye", "Arpa Şehriye", "Ekmek", "Lavaş", "Siyah Zeytin", 
    "Yeşil Zeytin", "Ceviz", "Fındık", "Nar Ekşisi", "Elma Sirkesi", 
    "Üzüm Sirkesi", "Ketçap", "Mayonez", "Hardal", "Sosis", 
    "Sucuk", "Salam", "Tavuk Göğsü", "Kıyma", "Kuşbaşı Et", 
    "Ton Balığı", "Mantar", "Havuç", "Salatalık", "Mısır"
]

st.markdown("---")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("##### 🕒 Öğün Seçimi")
    secilen_ogun = st.selectbox("Öğün", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Atıştırmalık"], label_visibility="collapsed")

with c2:
    st.markdown("##### 👥 Porsiyon")
    kisi_sayisi = st.number_input("Kişi", 1, 10, 2, label_visibility="collapsed")

with c3:
    st.markdown("##### 🔥 Kalori Hedefi")
    kalori_hedefi = st.selectbox("Kalori", ["Fark Etmez", "300 kcal Altı", "300 - 500 kcal", "500+ kcal"], label_visibility="collapsed")

# --- YENİ: AÇILIR-KAPANIR KUTU (EXPANDER) ---
with st.expander("🛒 Dolabınızdaki Malzemeleri Yönetin", expanded=True):
    secilenler = st.multiselect("Malzemeleri seçin:", MALZEMELER, label_visibility="collapsed")

def menü_talep_et():
    payload = {
        "malzemeler": secilenler, 
        "ogun": secilen_ogun,
        "kisi_sayisi": kisi_sayisi,
        "kalori_hedefi": kalori_hedefi,
        "gosterilen_tarifler": st.session_state.gosterilen_tarifler
    }
    response = requests.post("https://ai-gurme-mutfak.onrender.com/tarif-bul", json=payload)
    if response.status_code == 200:
        st.session_state.aktif_menü = response.json()["tarifler"]
        for t in st.session_state.aktif_menü:
            if t["title"] not in st.session_state.gosterilen_tarifler:
                st.session_state.gosterilen_tarifler.append(t["title"])
    else:
        st.error("AI Şef şu an meşgul. Terminali kontrol edin.")

# --- ANA BUTON ---
if st.button("✨ GURME MENÜMÜ HAZIRLA", use_container_width=True):
    if len(secilenler) >= 2:
        st.session_state.gosterilen_tarifler = [] 
        with st.spinner("🍳 Şefimiz mutfakta malzemeleri analiz ediyor..."):
            menü_talep_et()
    else:
        st.warning("En az 2 malzeme seçerek şefimize yardımcı olun.")

# --- MENÜ GÖSTERİM ALANI ---
if st.session_state.aktif_menü:
    st.markdown("### 📋 Bugünün Gurme Menüsü")
    
    tab1, tab2, tab3 = st.tabs(["⚡ PRATİK (5-15 Dk)", "⚖️ DENGELİ (15-30 Dk)", "🏆 USTA İŞİ (30+ Dk)"])
    sekmeler = [tab1, tab2, tab3]
    
    for index, tab in enumerate(sekmeler):
        with tab:
            t = st.session_state.aktif_menü[index]
            
            st.image(t.get("image_path"), use_container_width=True)
            
            st.markdown(f"""
            <div class="recipe-card">
                <h2 style="margin-top:0;">{t['title']}</h2>
                <p style="color:#FFBF00;">⏱️ {t['duration']} | 🔥 {t.get('calories_per_person', 'Hesaplanıyor')}</p>
                <hr style="border:0.5px solid #333;">
                <h4>Gerekenler:</h4>
                <ul>
                    {"".join([f'<li>{m}</li>' for m in t['required_ingredients']])}
                </ul>
                <h4>Hazırlanışı:</h4>
                <ol>
                    {"".join([f'<li>{adim}</li>' for adim in t['instructions']])}
                </ol>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    
    if st.button("❌ Bu Menüyü Beğenmedim, Bana Tamamen Başka Tarifler Sun!", type="secondary", use_container_width=True):
        with st.spinner("🔄 Mevcut tarifler kara listeye alındı, yepyeni alternatifler üretiliyor..."):
            menü_talep_et()
            st.rerun()
