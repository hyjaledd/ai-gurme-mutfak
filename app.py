import streamlit as st
import requests

st.set_page_config(page_title="AI Gourmet Kitchen", page_icon="🧑‍🍳", layout="wide")

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

# --- KONTROL PANELİ ---
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
    
    if st.button("✨ GURME REÇETELERİ OLUŞTUR", type="primary", use_container_width=True):
        if not malzemeler_listesi:
            st.error("🚨 Lütfen envanterinizden en az bir malzeme seçin!")
        else:
            with st.spinner("🍳 Yapay zeka şefi reçeteleri hazırlıyor..."):
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
                    st.error(f"Render sunucusuna ulaşılamadı. Hata: {e}")

st.write("---")

# --- ESKİ GÜZEL VE SEÇMELİ YAPI (GERİ GELDİ) ---
if st.session_state.mevcut_tarifler:
    st.markdown("### 📋 Oluşturulan Özel Menü Protokolü")
    
    cols = st.columns(3)
    
    for idx, tarif in enumerate(st.session_state.mevcut_tarifler):
        with cols[idx % 3]:
            # Şık Kart Başlığı
            st.markdown(f"""
                <div style="background-color: #12121f; padding: 1.2rem; border-radius: 12px; border: 1px solid #232338; margin-bottom: 1rem;">
                    <span style="background-color: #ff4b4b; color: white; padding: 3px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: bold;">REÇETE {idx+1}</span>
                    <h3 style="margin-top: 0.6rem; color: #ffffff; font-family: 'Inter', sans-serif; font-size: 1.3rem;">{tarif.get('title', 'Özel Reçete')}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Kalori Metriği
            st.metric(label="⚡ Enerji Oranı", value=tarif.get('calories', 'Belirtilmedi'))
            
            # Gerekli Malzemeler Şeridi
            st.markdown("🔗 **Gerekli Malzemeler:**")
            st.info(", ".join(tarif.get("ingredients", [])))
            
            # --- HAZIRLANIŞ SÜRESİ KATEGORİLERİ VE TIKLAYINCA AÇILAN EXPANDER YAPISI ---
            # Reçetenin içindeki adım sayısına göre otomatik gerçekçi bir süre kategorisi belirliyoruz
            adımlar_ham = tarif.get("instructions", [])
            adım_sayisi = len(adımlar_ham) if isinstance(adımlar_ham, list) else 5
            
            if adım_sayisi <= 4:
                sure_etiketi = "⏱️ Hazırlanış: 5-15 Dakika"
            elif adım_sayisi <= 7:
                sure_etiketi = "⏱️ Hazırlanış: 15-30 Dakika"
            else:
                sure_etiketi = "⏱️ Hazırlanış: 30+ Dakika"
            
            # Tıklayınca açılan kutu (Expander)
            with st.expander(sure_etiketi, expanded=False):
                st.markdown("##### 👨‍🍳 Hazırlanış Adımları")
                
                # Bilgisayar çıktısı gibi duran o ham dict/list görüntüsünü temizliyoruz
                if isinstance(adımlar_ham, list):
                    for adim in adımlar_ham:
                        st.write(f"• {adim}")
                elif isinstance(adımlar_ham, dict):
                    for k, v in adımlar_ham.items():
                        st.write(f"**Adım {int(k)+1 if k.isdigit() else k}:** {v}")
                else:
                    # Eğer veri düz metin olarak geldiyse doğrudan şık bir fontla yazdır
                    st.write(str(adımlar_ham))
            
            st.markdown("<br>", unsafe_allow_html=True)
