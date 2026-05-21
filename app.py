import streamlit as st
import requests

st.set_page_config(page_title="AI Gourmet Kitchen", page_icon="🧑‍🍳", layout="wide")

# --- BACKEND BAĞLANTI ADRESİ ---
BACKEND_URL = "https://ai-gurme-mutfak.onrender.com"

# --- PREMIUM HEADER TASARIMI ---
st.markdown("""
    <div style="background: linear-gradient(135deg, #1e1e2f 0%, #0f0f1a 100%); padding: 2.5rem; border-radius: 16px; margin-bottom: 2rem; border: 1px solid #2d2d44;">
        <h1 style="color: #ffffff; margin-bottom: 0.5rem; font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -0.5px;">🧑‍🍳 AI Gourmet Kitchen</h1>
        <p style="color: #8b8ba7; font-size: 1.1rem; margin-bottom: 0;">Profesyonel Yapay Zeka Şefi • Akıllı Kalori ve Menü Yönetim Paneli</p>
    </div>
""", unsafe_allow_html=True)

# Hafıza Yönetimi (Session State)
if "gosterilen_tarifler" not in st.session_state:
    st.session_state.gosterilen_tarifler = []
if "mevcut_tarifler" not in st.session_state:
    st.session_state.mevcut_tarifler = None

# --- KONTROL PANELİ (GİRİŞ ALANI) ---
with st.container():
    st.markdown("#### ⚙️ Menü Yapılandırma")
    col_ogun, col_porsiyon, col_kalori = st.columns(3)

    with col_ogun:
        ogun = st.selectbox("⏱️ Hedef Öğün", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif", "Tatlı"])

    with col_porsiyon:
        kisi_sayisi = st.number_input("👥 Porsiyon Sayısı", min_value=1, max_value=20, value=2, step=1)

    with col_kalori:
        kalori_hedefi = st.selectbox("🔥 Kalori Filtresi", ["Fark Etmez", "Düşük Kalori (<300 kcal)", "Dengeli (300-600 kcal)", "Yüksek Enerji (>600 kcal)"])

    st.write("")
    
    # Seçmeli Malzeme Listesi
    populer_malzemeler = [
        "Süt", "Beyaz Peynir", "Kaşar Peyniri", "Yumurta", "Tereyağı", "Ayçiçek Yağı", 
        "Zeytinyağı", "Un", "Toz Şeker", "Tuz", "Karabiber", "Pul Biber", "Kekik", 
        "Kimyon", "İsot", "Nane", "Domates", "Biber", "Salça", "Kuru Soğan", 
        "Sarımsak", "Patates", "Kapya Biber", "Maydanoz", "Yoğurt", "Tavuk", "Kıyma"
    ]

    malzemeler_listesi = st.multiselect(
        "🛒 Mevcut Malzeme Envanteri", 
        options=populer_malzemeler,
        default=["Yumurta", "Domates", "Biber", "Kaşar Peyniri"]
    )

    st.write("")
    
    # Geniş Premium Buton
    if st.button("✨ GURME REÇETELERİ OLUŞTUR", type="primary", use_container_width=True):
        if not malzemeler_listesi:
            st.error("🚨 Lütfen envanterinizden en az bir malzeme seçin!")
        else:
            with st.spinner("🍳 Yapay zeka şefi mikro-besinleri hesaplıyor ve reçeteleri hazırlıyor..."):
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
                        for t in st.session_state.mevcut_tarifler:
                            if t["title"] not in st.session_state.gosterilen_tarifler:
                                st.session_state.gosterilen_tarifler.append(t["title"])
                    else:
                        st.error(f"Backend sunucusundan hata döndü (Kod: {response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Render backend sunucusuna ulaşılamadı. Sunucu uyanıyor olabilir, lütfen tekrar deneyin. Hata: {e}")

st.write("---")

# --- VERİ ODAKLI PREMİUM TARİF KARTLARI ---
if st.session_state.mevcut_tarifler:
    st.markdown("### 📋 Oluşturulan Özel Menü Protokolü")
    
    # 3 Farklı yemek için yan yana 3 ana dikey kolon açıyoruz
    cols = st.columns(3)
    
    for idx, tarif in enumerate(st.session_state.mevcut_tarifler):
        with cols[idx % 3]:
            # Kartın etrafına temiz, profesyonel bir çerçeve çekiyoruz (HTML stilleri ile)
            st.markdown(f"""
                <div style="background-color: #12121f; padding: 1.5rem; border-radius: 12px; border: 1px solid #232338; margin-bottom: 1rem;">
                    <span style="background-color: #ff4b4b; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">Reçete {idx+1}</span>
                    <h3 style="margin-top: 0.8rem; color: #ffffff; font-family: 'Inter', sans-serif;">{tarif.get('title', 'Özel Gurme Lezzeti')}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Kalori Değerini Şık Bir Veri Kutusu (Metric) Olarak Gösteriyoruz
            st.metric(label="⚡ Enerji Oranı", value=tarif.get('calories', 'Belirtilmedi'))
            
            # İçindekiler Alanı (Temiz listeleme)
            st.markdown("🔗 **Gerekli Malzemeler:**")
            st.info(", ".join(tarif.get("ingredients", [])))
            
            # Hazırlanışı Alanı
            st.markdown("👨‍🍳 **Hazırlanış Protokolü:**")
            st.write(tarif.get("instructions", "Tarif adımları yüklenemedi."))
            st.markdown("<br><hr style='border-top: 1px solid #232338;'><br>", unsafe_allow_html=True)
