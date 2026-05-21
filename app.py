import streamlit as st
import requests

st.set_page_config(page_title="AI Gourmet Kitchen", page_icon="🍳", layout="wide")

# --- BACKEND BAĞLANTI ADRESİ ---
BACKEND_URL = "https://ai-gurme-mutfak.onrender.com"

# Sayfa Başlığı ve Tasarımı
st.title("🧑‍🍳 AI Gourmet Kitchen")
st.markdown("##### Profesyonel yapay zeka şefiyle mutfağınızda bir sanat eseri yaratın.")
st.write("---")

# Hafıza Yönetimi (Session State)
if "gosterilen_tarifler" not in st.session_state:
    st.session_state.gosterilen_tarifler = []
if "mevcut_tarifler" not in st.session_state:
    st.session_state.mevcut_tarifler = None

# Giriş Bölümü: Öğün, Porsiyon ve Kalori Seçimi (Yan Yana Üç Kolon)
col_ogun, col_porsiyon, col_kalori = st.columns(3)

with col_ogun:
    ogun = st.selectbox("⏱️ Öğün Seçimi", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif", "Tatlı"])

with col_porsiyon:
    kisi_sayisi = st.number_input("👥 Porsiyon", min_value=1, max_value=20, value=2, step=1)

with col_kalori:
    kalori_hedefi = st.selectbox("🔥 Kalori Hedefi", ["Fark Etmez", "Düşük Kalori (<300 kcal)", "Dengeli (300-600 kcal)", "Yüksek Enerji (>600 kcal)"])

st.write("")

# --- ESKİ SEÇMELİ MALZEME LİSTESİ (GERİ GELDİ) ---
populer_malzemeler = [
    "Süt", "Beyaz Peynir", "Kaşar Peyniri", "Yumurta", "Tereyağı", "Ayçiçek Yağı", 
    "Zeytinyağı", "Un", "Toz Şeker", "Tuz", "Karabiber", "Pul Biber", "Kekik", 
    "Kimyon", "İsot", "Nane", "Domates", "Biber", "Salça", "Kuru Soğan", 
    "Sarımsak", "Patates", "Kapya Biber", "Maydanoz", "Yoğurt", "Tavuk", "Kıyma"
]

malzemeler_listesi = st.multiselect(
    "🛒 Dolabınızdaki Malzemeleri Yönetin", 
    options=populer_malzemeler,
    default=["Yumurta", "Domates", "Biber", "Kaşar Peyniri"] # İlk açılışta seçili gelecekler
)

st.write("")

# Menü Hazırlama Butonu
if st.button("✨ GURME MENÜMÜ HAZIRLA", type="primary", use_container_width=True):
    if not malzemeler_listesi:
        st.error("🚨 Lütfen dolabınızdan en az bir malzeme seçin!")
    else:
        with st.spinner("🍳 Şefimiz mutfakta malzemeleri analiz ediyor..."):
            payload = {
                "malzemeler": malzemeler_listesi,
                "ogun": ogun,
                "kisi_sayisi": int(kisi_sayisi),
                "kalori_hedefi": kalori_hedefi,
                "gosterilen_tarifler": st.session_state.gosterilen_tarifler
            }
            
            try:
                response = requests.post(f"{BACKEND_URL}/tarif-bul", json=payload, timeout=60)
                if response.status_code == 200:
                    st.session_state.mevcut_tarifler = response.json().get("tarifler", [])
                    # Beğenilmeyen geçmiş havuzuna ekle ki bir sonraki basışta farklı yemek gelsin
                    for t in st.session_state.mevcut_tarifler:
                        if t["title"] not in st.session_state.gosterilen_tarifler:
                            st.session_state.gosterilen_tarifler.append(t["title"])
                else:
                    st.error(f"Backend sunucusundan hata döndü (Kod: {response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Render backend sunucusuna ulaşılamadı. Sunucu uyanıyor olabilir, lütfen 10 saniye sonra tekrar deneyin. Hata: {e}")

st.write("")

# Tarif Kartlarını Grid (3 Kolon) Şeklinde Ekrana Basma
if st.session_state.mevcut_tarifler:
    st.success("🤖 AI Şefinizin Sizin İçin Seçtiği Özel Menü:")
    cols = st.columns(3)
    
    for idx, tarif in enumerate(st.session_state.mevcut_tarifler):
        with cols[idx % 3]:
            # Arka planda kırılma olmasın diye sabit gelen iştah açıcı görseli basıyoruz
            st.image(tarif.get("image_path"), use_container_width=True)
            st.subheader(tarif.get("title", "Gurme Lezzet"))
            st.markdown(f"🔥 **Kalori:** {tarif.get('calories', 'Belirtilmedi')}")
            
            st.write("**🛒 Malzemeler:**")
            st.caption(", ".join(tarif.get("ingredients", [])))
            
            st.write("**👨‍🍳 Hazırlanışı:**")
            st.write(tarif.get("instructions", "Tarif adımları yüklenemedi."))
            st.write("---")
