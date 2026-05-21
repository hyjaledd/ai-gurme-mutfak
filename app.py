import streamlit as st
import requests

# Sayfa yapılandırması
st.set_page_config(page_title="AI Gourmet Kitchen", page_icon="🧑‍🍳", layout="wide")

# --- BACKEND BAĞLANTI ADRESİ ---
BACKEND_URL = "https://ai-gurme-mutfak.onrender.com"

# --- MOBİL UYUMLU PREMIUM HEADER ---
st.markdown("""
    <div style="background: linear-gradient(135deg, #1e1e2f 0%, #0f0f1a 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #2d2d44;">
        <h1 style="color: #ffffff; margin-bottom: 0.4rem; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 1.8rem; letter-spacing: -0.5px; text-align: center;">🧑‍🍳 AI Gourmet Kitchen</h1>
        <p style="color: #8b8ba7; font-size: 0.95rem; margin-bottom: 0; text-align: center;">Kategori Bazlı Akıllı Reçete Sistemi</p>
    </div>
""", unsafe_allow_html=True)

# Hafıza Yönetimi
if "gosterilen_tarifler" not in st.session_state:
    st.session_state.gosterilen_tarifler = []
if "mevcut_tarifler" not in st.session_state:
    st.session_state.mevcut_tarifler = None

# --- KONTROL PANELİ ---
with st.container():
    st.markdown("#### ⚙️ Menü Yapılandırma")
    col_ogun, col_porsiyon, col_kalori = st.columns([1, 1, 1])

    with col_ogun:
        ogun = st.selectbox("⏱️ Öğün", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif", "Tatlı"])

    with col_porsiyon:
        kisi_sayisi = st.number_input("👥 Porsiyon", min_value=1, max_value=20, value=2, step=1)

    with col_kalori:
        kalori_hedefi = st.selectbox("🔥 Kalori (Kişi Başı)", ["Fark Etmez", "Düşük Kalori (<300 kcal)", "Dengeli (300-600 kcal)", "Yüksek Enerji (>600 kcal)"])

    populer_malzemeler = ["Süt", "Beyaz Peynir", "Kaşar Peyniri", "Yumurta", "Tereyağı", "Zeytinyağı", "Un", "Tuz", "Karabiber", "Pul Biber", "Domates", "Biber", "Salça", "Kuru Soğan", "Sarımsak", "Patates", "Yoğurt", "Tavuk", "Kıyma"]
    malzemeler_listesi = st.multiselect("🛒 Envanteriniz", options=populer_malzemeler, default=[])

    if st.button("✨ GURME REÇETELERİ OLUŞTUR", type="primary", use_container_width=True):
        if not malzemeler_listesi:
            st.error("🚨 Lütfen envanter seçin!")
        else:
            with st.spinner("🍳 Reçeteler hazırlanıyor..."):
                payload = {"malzemeler": malzemeler_listesi, "ogun": ogun, "kisi_sayisi": int(kisi_sayisi), "kalori_hedefi": kalori_hedefi, "gosterilen_tarifler": st.session_state.gosterilen_tarifler}
                try:
                    response = requests.post(f"{BACKEND_URL}/tarif-bul", json=payload, timeout=60)
                    if response.status_code == 200:
                        st.session_state.mevcut_tarifler = response.json().get("tarifler", [])
                    else:
                        st.error("Backend hatası oluştu.")
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")

st.write("---")

# --- KATEGORİZE EDİLMİŞ VE TIKLANDIĞINDA AÇILAN TARİF YAPISI ---
if st.session_state.mevcut_tarifler:
    st.markdown("### 📋 Hazırlanan Özel Reçete Listesi")
    st.caption(f"💡 Her bir tarifin üzerine dokunarak **Kişi Başı Kalori**, **Malzemeler** ve **Adımları** görebilirsiniz.")
    
    for idx, tarif in enumerate(st.session_state.mevcut_tarifler):
        adımlar_ham = tarif.get("instructions", [])
        adım_sayisi = len(adımlar_ham) if isinstance(adımlar_ham, (list, dict)) else 5
        
        if   adım_sayisi <= 4: sure_kat = "5-15 Dk (Hızlı)"
        elif adım_sayisi <= 7: sure_kat = "15-30 Dk (Standart)"
        else:                  sure_kat = "30+ Dk (Gurme)"
        
        expander_label = f"🍽️ {tarif.get('title')} — [{sure_kat}]"
        
        with st.expander(expander_label, expanded=False):
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.metric(label="🔥 Kalori (Kişi Başı)", value=tarif.get('calories', 'N/A'))
            with m_col2:
                st.metric(label="👥 Hedef Porsiyon", value=f"{kisi_sayisi} Kişilik")
            
            # --- MALZEME TİPİNİ AKILLICA TEMİZLEYEN GÜVENLİK KALKANI ---
            st.markdown("##### 🛒 Gerekli Malzemeler")
            malzemeler_ham = tarif.get("ingredients", [])
            
            if isinstance(malzemeler_ham, list):
                # Liste içindeki elemanlar sözlük mü yoksa düz yazı mı kontrol et
                temiz_malzemeler = []
                for m in malzemeler_ham:
                    if isinstance(m, dict):
                        # Eğer sözlükse isim ve miktar bilgisini birleştir (Örn: "Tavuk: 200g")
                        isim = m.get("name", m.get("item", str(m)))
                        miktar = m.get("amount", m.get("quantity", ""))
                        temiz_malzemeler.append(f"{isim} ({miktar})" if miktar else isim)
                    else:
                        temiz_malzemeler.append(str(m))
                st.info(", ".join(temiz_malzemeler))
            elif isinstance(malzemeler_ham, dict):
                temiz_malzemeler = [f"{k}: {v}" for k, v in malzemeler_ham.items()]
                st.info(", ".join(temiz_malzemeler))
            else:
                st.info(str(malzemeler_ham))
            
            # Hazırlanış Protokolü
            st.markdown("##### 👨‍🍳 Hazırlanış Protokolü")
            if isinstance(adımlar_ham, list):
                for adim in adımlar_ham:
                    st.write(f"• {adim}")
            elif isinstance(adımlar_ham, dict):
                for k, v in adımlar_ham.items():
                    st.write(f"**{k}:** {v}")
            else:
                st.write(str(adımlar_ham))
            
            st.markdown("<p style='text-align: right; color: #8b8ba7; font-size: 0.8rem;'>AI Gourmet Kitchen © 2026</p>", unsafe_allow_html=True)
