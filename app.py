import streamlit as st
import requests

# Mobil uyumluluk için geniş yerleşimi koruyoruz ancak alt bileşenleri esnetiyoruz
st.set_page_config(page_title="AI Gourmet Kitchen", page_icon="🧑‍🍳", layout="wide")

# --- BACKEND BAĞLANTI ADRESİ ---
BACKEND_URL = "https://ai-gurme-mutfak.onrender.com"

# --- MOBİL UYUMLU PREMIUM HEADER ---
st.markdown("""
    <div style="background: linear-gradient(135deg, #1e1e2f 0%, #0f0f1a 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #2d2d44;">
        <h1 style="color: #ffffff; margin-bottom: 0.4rem; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 1.8rem; letter-spacing: -0.5px; text-align: center;">🧑‍🍳 AI Gourmet Kitchen</h1>
        <p style="color: #8b8ba7; font-size: 0.95rem; margin-bottom: 0; text-align: center;">Profesyonel Şef ve Diyetisyen Reçete Yönetim Paneli</p>
    </div>
""", unsafe_allow_html=True)

# Hafıza Yönetimi (Session State)
if "gosterilen_tarifler" not in st.session_state:
    st.session_state.gosterilen_tarifler = []
if "mevcut_tarifler" not in st.session_state:
    st.session_state.mevcut_tarifler = None

# --- KONTROL PANELİ (MOBİL İÇİN DİKEY HİZALANABİLİR DÜZEN) ---
with st.container():
    st.markdown("#### ⚙️ Menü Konfigürasyonu")
    
    # Küçük ekranlarda (Mobilde) alt alta, büyük ekranlarda yan yana otomatik esneyen kolonlar
    col_ogun, col_porsiyon, col_kalori = st.columns([1, 1, 1])

    with col_ogun:
        ogun = st.selectbox(
            "⏱️ Hedef Öğün Tipi", 
            ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif", "Tatlı"],
            help="Yayap zeka şefinin mutfak protokolünü ve malzeme ağırlıklarını optimize edeceği öğün türü."
        )

    with col_porsiyon:
        kisi_sayisi = st.number_input(
            "👥 Toplam Porsiyon", 
            min_value=1, max_value=20, value=2, step=1,
            help="Malzeme miktarları ve veritabanı kayıtları bu porsiyon sayısına göre dinamik olarak çarpılacaktır."
        )

    with col_kalori:
        kalori_hedefi = st.selectbox(
            "🔥 Kalori Filtresi (Kişi Başı)", 
            ["Fark Etmez", "Düşük Kalori (<300 kcal)", "Dengeli (300-600 kcal)", "Yüksek Enerji (>600 kcal)"],
            help="⚠️ ÖNEMLİ: Belirtilen kalori limitleri toplam menü için değil, porsiyon başına düşen KİŞİ BAŞI enerji değerleridir."
        )

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
        default=["Yumurta", "Domates", "Biber", "Kaşar Peyniri"],
        help="Dolabınızda bulunan aktif malzemeler. Şefimiz bu malzemeleri ana omurga olarak kabul edecektir."
    )

    st.write("")
    
    if st.button("✨ GURME REÇETELERİ OLUŞTUR", type="primary", use_container_width=True):
        if not malzemeler_listesi:
            st.error("🚨 Lütfen envanterinizden en az bir malzeme seçin!")
        else:
            with st.spinner("🍳 Yapay zeka şefi mikro-besinleri hesaplıyor..."):
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

# --- MOBİL ÖNCELİKLİ (SADE, DİKEY VE DENGELİ) TARİF LİSTELEME ---
if st.session_state.mevcut_tarifler:
    st.markdown("### 📋 Oluşturulan Özel Menü Protokolü")
    st.caption(f"💡 Bilgilendirme: Aşağıdaki makro besin ve kalori değerleri **{kisi_sayisi} Kişilik** porsiyona göre ayarlanmış olup, enerji oranları **Kişi Başı** baz alınarak hesaplanmıştır.")
    st.write("")
    
    # Mobilde 3 kolon yan yana sıkışıp yazıları bozmasın diye tek bir dikey akış (Single Column Card) mimarisi kullanıyoruz.
    # Bu mimari mobilde kusursuz bir "Kaydırılabilir Feed" (Scrollable Feed) deneyimi sunar.
    for idx, tarif in enumerate(st.session_state.mevcut_tarifler):
        
        # Her bir tarifi şık ve izole bir blok içerisine alıyoruz
        with st.container():
            st.markdown(f"""
                <div style="background-color: #12121f; padding: 1rem; border-radius: 10px; border: 1px solid #232338; margin-top: 0.5rem; margin-bottom: 0.5rem;">
                    <span style="background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase;">Reçete {idx+1}</span>
                    <h3 style="margin-top: 0.4rem; margin-bottom: 0.2rem; color: #ffffff; font-family: 'Inter', sans-serif; font-size: 1.25rem;">{tarif.get('title', 'Özel Reçete')}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Mobil ekranlarda yer kaplamayan şık yan yana ufak metrik satırı
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.metric(label="🔥 Enerji (Kişi Başı)", value=tarif.get('calories', 'Belirtilmedi'))
            with m_col2:
                st.metric(label="👥 Hedef Kitle", value=f"{kisi_sayisi} Kişilik")
            
            st.markdown("🔗 **Reçete İçeriği ve Kompozisyonu:**")
            st.info(", ".join(tarif.get("ingredients", [])))
            
            # Adım sayısına göre dinamik süre hesabı
            adımlar_ham = tarif.get("instructions", [])
            adım_sayisi = len(adımlar_ham) if isinstance(adımlar_ham, (list, dict)) else 5
            
            if   adım_sayisi <= 4: sure_etiketi = "⏱️ Süre: Fast-Track (5-15 Dk)"
            elif adım_sayisi <= 7: sure_etiketi = "⏱️ Süre: Standart (15-30 Dk)"
            else:                  sure_etiketi = "⏱️ Süre: Gurme (30+ Dk)"
            
            # Tamamen mobil parmak hareketlerine (Touch) duyarlı expander yapısı
            with st.expander(f"{sure_etiketi} — Reçete Adımlarını Aç/Kapat", expanded=False):
                st.markdown("##### 👨‍🍳 Hazırlanış Protokolü")
                if isinstance(adımlar_ham, list):
                    for adim in adımlar_ham:
                        st.write(f"• {adim}")
                elif isinstance(adımlar_ham, dict):
                    for k, v in adımlar_ham.items():
                        st.write(f"**Adım {int(k)+1 if k.isdigit() else k}:** {v}")
                else:
                    st.write(str(adımlar_ham))
            
            # Kartlar arası görsel ayrım şeridi
            st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
