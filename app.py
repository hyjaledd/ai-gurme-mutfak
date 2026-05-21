import streamlit as st
import requests

# --- GÜVENLİ MALZEME OKUMA FONKSİYONU ---
# Yapay zeka malzemeyi 'name', 'item' veya 'ingredient' olarak gönderse bile çökmeden yakalar
def malzemeleri_temizle(malzemeler_ham):
    temiz = []
    if isinstance(malzemeler_ham, list):
        for m in malzemeler_ham:
            if isinstance(m, dict):
                isim = m.get("name", m.get("item", m.get("ingredient", str(m))))
                miktar = m.get("amount", m.get("quantity", m.get("measure", "")))
                temiz.append(f"{isim} {miktar}".strip())
            else:
                temiz.append(str(m))
    elif isinstance(malzemeler_ham, dict):
        temiz = [f"{k}: {v}" for k, v in malzemeler_ham.items()]
    else:
        temiz = [str(malzemeler_ham)]
    return temiz

# Sayfa yapılandırması
st.set_page_config(page_title="AI Gourmet Kitchen", page_icon="🍳", layout="wide")

# --- ADVANCED PREMIUM CSS ENJEKSİYONU ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #b8860b 0%, #ffd700 50%, #b8860b 100%);
        background-size: 200% auto;
        color: #1a1a1a !important;
        border: none;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.05rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 0.6rem 0;
        box-shadow: 0 4px 15px rgba(218, 165, 32, 0.25);
        transition: 0.5s;
    }
    div.stButton > button:first-child:hover {
        background-position: right center;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(218, 165, 32, 0.4);
    }

    .ingredient-tag {
        display: inline-block;
        background-color: #1e2329;
        border: 1px solid #363c46;
        color: #d1d5db;
        padding: 6px 14px;
        border-radius: 20px;
        margin: 4px 6px 4px 0;
        font-size: 0.85rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .premium-metric {
        background: linear-gradient(180deg, #161a22 0%, #11141a 100%);
        border-left: 3px solid #b8860b;
        padding: 1.2rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title {
        color: #8b949e;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        color: #f0f2f6;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .bonus-dessert-box {
        background: linear-gradient(135deg, #1f1911 0%, #14110c 100%);
        border: 2px solid #b8860b;
        padding: 1.2rem;
        border-radius: 12px;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(184, 134, 11, 0.15);
    }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND BAĞLANTI ADRESİ ---
BACKEND_URL = "https://ai-gurme-mutfak.onrender.com"

# --- LÜKS HEADER TASARIMI ---
st.markdown("""
    <div style="background: linear-gradient(135deg, #11141a 0%, #1c212b 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2.5rem; border: 1px solid #2d333f; border-bottom: 3px solid #b8860b; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <h1 style="color: #f0f2f6; margin-bottom: 0.2rem; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 2.4rem; letter-spacing: -1px;">🥂 AI Gourmet Kitchen</h1>
        <p style="color: #8b949e; font-size: 1rem; margin-bottom: 0; font-weight: 500; letter-spacing: 2px;">KİŞİSEL ŞEFİNİZ & DİYETİSYENİNİZ</p>
    </div>
""", unsafe_allow_html=True)

# Hafıza Yönetimi
if "gosterilen_tarifler" not in st.session_state:
    st.session_state.gosterilen_tarifler = []
if "mevcut_tarifler" not in st.session_state:
    st.session_state.mevcut_tarifler = None

# --- KONTROL PANELİ ---
with st.container():
    st.markdown("<h4 style='color: #e2e2e2; margin-bottom: 1rem;'>⚙️ Menü Konfigürasyonu</h4>", unsafe_allow_html=True)
    col_ogun, col_porsiyon, col_kalori = st.columns([1, 1, 1])

    with col_ogun:
        ogun = st.selectbox("⏱️ Öğün", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif", "Tatlı"])

    with col_porsiyon:
        kisi_sayisi = st.number_input("👥 Porsiyon", min_value=1, max_value=20, value=2, step=1)

    with col_kalori:
        kalori_hedefi = st.selectbox("🔥 Kalori (Kişi Başı)", ["Fark Etmez", "Düşük Kalori (<300 kcal)", "Dengeli (300-600 kcal)", "Yüksek Enerji (>600 kcal)"])

    populer_malzemeler = [
        "Süt", "Yoğurt", "Tereyağı", "Kaşar Peyniri", "Beyaz Peynir", "Tulum Peyniri", "Lor Peyniri", "Krem Peynir", "Kaymak", "Kefir",
        "Yumurta", "Dana Kıyma", "Kuşbaşı Et", "Tavuk Göğsü", "Tavuk But", "Sucuk", "Sosis", "Salam", "Pastırma", "Ton Balığı",
        "Un", "Toz Şeker", "Esmer Şeker", "İnce Bulgur", "Pilavlık Bulgur", "Kırmızı Mercimek", "Yeşil Mercimek", "Nohut", "Kuru Fasulye", "Pirinç", "Makarna", "Tel Şehriye", "Arpa Şehriye", "Tarhana", "Yulaf",
        "Ayçiçek Yağı", "Zeytinyağı", "Nar Ekşisi", "Elma Sirkesi", "Üzüm Sirkesi", "Domates Salçası", "Acı Biber Salçası", "Tatlı Biber Salçası", "Soya Sosu", "Mayonez", "Ketçap", "Hardal",
        "Domates", "Sivri Biber", "Kapya Biber", "Kuru Soğan", "Kırmızı Soğan", "Sarımsak", "Patates", "Havuç", "Kabak", "Patlıcan", "Ispanak", "Pırasa", "Limon", "Mantar", "Salatalık", "Marul", "Maydanoz", "Dereotu", "Taze Nane", "Roka", "Yeşil Soğan",
        "Tuz", "Karabiber", "Pul Biber", "İsot", "Kimyon", "Kekik", "Kuru Nane", "Sumak", "Tatlı Toz Biber", "Tarçın", "Zerdeçal", "Köri", "Susam", "Çörek Otu",
        "Ceviz İçi", "Fındık", "Badem", "Siyah Zeytin", "Yeşil Zeytin", "Bal", "Üzüm Pekmezi", "Tahin", "Kabartma Tozu", "Vanilya", "Kuru Maya", "Kakao", "Damla Çikolata", "Galeta Unu"
    ]
    
    malzemeler_listesi = st.multiselect("🛒 Envanteriniz", options=populer_malzemeler, default=[])
    
    st.write("") 
    if st.button("GURME REÇETELERİ OLUŞTUR", use_container_width=True):
        if not malzemeler_listesi:
            st.error("🚨 Lütfen mutfak envanterinizden malzeme seçin!")
        else:
            with st.spinner("🍳 Şefimiz size 3 özel reçete ve 1 bonus tatlı hazırlıyor..."):
                payload = {"malzemeler": malzemeler_listesi, "ogun": ogun, "kisi_sayisi": int(kisi_sayisi), "kalori_hedefi": kalori_hedefi, "gosterilen_tarifler": st.session_state.gosterilen_tarifler}
                try:
                    response = requests.post(f"{BACKEND_URL}/tarif-bul", json=payload, timeout=60)
                    if response.status_code == 200:
                        yeni_tarifler = response.json().get("tarifler", [])
                        st.session_state.mevcut_tarifler = yeni_tarifler
                        
                        # Gösterilenleri hafızaya al ki bir sonraki basışta aynıları gelmesin
                        for t in yeni_tarifler:
                            title = t.get("title")
                            if title and title not in st.session_state.gosterilen_tarifler:
                                st.session_state.gosterilen_tarifler.append(title)
                    else:
                        st.error("Backend hatası oluştu.")
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")

st.write("---")

# --- KATEGORİZE EDİLMİŞ ÖZEL REÇETE GÖSTERİMİ ---
if st.session_state.mevcut_tarifler:
    ana_tarifler = [t for t in st.session_state.mevcut_tarifler if not t.get("is_bonus", False)]
    bonus_tatlilar = [t for t in st.session_state.mevcut_tarifler if t.get("is_bonus", False)]
    
    # --- ADIM A: ANA TARİFLERİN LİSTELENMESİ ---
    st.markdown("<h3 style='color: #b8860b; margin-bottom: 0.5rem;'>📋 Tadım Menüsü</h3>", unsafe_allow_html=True)
    st.caption("Ayrıntılı mutfak protokolünü görmek için reçetelerin üzerine dokunun.")
    st.write("")
    
    for idx, tarif in enumerate(ana_tarifler):
        adımlar_ham = tarif.get("instructions", [])
        adım_sayisi = len(adımlar_ham) if isinstance(adımlar_ham, (list, dict)) else 5
        
        if adım_sayisi <= 4: sure_kat = "5-15 dk"
        elif adım_sayisi <= 7: sure_kat = "15-30 dk"
        else: sure_kat = "30+ dk"
        
        expander_label = f"🍽️ {tarif.get('title')}  |  ⏳ {sure_kat}"
        
        with st.expander(expander_label, expanded=False):
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.markdown(f'<div class="premium-metric"><div class="metric-title">🔥 Enerji Değeri (Kişi Başı)</div><div class="metric-value">{tarif.get("calories", "N/A")}</div></div>', unsafe_allow_html=True)
            with m_col2:
                st.markdown(f'<div class="premium-metric"><div class="metric-title">👥 Hedef Porsiyon</div><div class="metric-value">{kisi_sayisi} Kişilik</div></div>', unsafe_allow_html=True)
            
            st.markdown("<h5 style='color: #e2e2e2;'>🛒 Gerekli Malzemeler</h5>", unsafe_allow_html=True)
            
            temiz_malzemeler = malzemeleri_temizle(tarif.get("ingredients", []))
            
            tags_html = "".join([f"<span class='ingredient-tag'>▪ {m}</span>" for m in temiz_malzemeler])
            st.markdown(f"<div style='margin-bottom: 2rem;'>{tags_html}</div>", unsafe_allow_html=True)
            
            st.markdown("<h5 style='color: #e2e2e2; margin-bottom: 1rem;'>👨‍🍳 Hazırlanış Protokolü</h5>", unsafe_allow_html=True)
            if isinstance(adımlar_ham, list):
                for adim in adımlar_ham: st.write(f"**—** {adim}")
            elif isinstance(adımlar_ham, dict):
                for k, v in adımlar_ham.items(): st.write(f"**{k}:** {v}")
            else: st.write(str(adımlar_ham))

    # --- ADIM B: LÜKS ALTIN KUTUDA BONUS TATLI GÖSTERİMİ ---
    if bonus_tatlilar:
        st.write("")
        st.markdown("<h4 style='color: #ffd700; margin-top: 2rem; margin-bottom: 0.5rem;'>✨ Şefin İkramı (Bonus Reçete)</h4>", unsafe_allow_html=True)
        
        for tatli in bonus_tatlilar:
            t_adımlar = tatli.get("instructions", [])
            t_adım_sayisi = len(t_adımlar) if isinstance(t_adımlar, (list, dict)) else 5
            
            if t_adım_sayisi <= 4: t_sure_kat = "5-15 dk"
            elif t_adım_sayisi <= 7: t_sure_kat = "15-30 dk"
            else: t_sure_kat = "30+ dk"

            expander_tatli_label = f"🎁 {tatli.get('title')}  |  ⏳ {t_sure_kat} (Bonus Tatlı)"
            
            # Kapalı gelmesi için expanded=False yapıldı
            with st.expander(expander_tatli_label, expanded=False): 
                st.markdown('<div class="bonus-dessert-box">', unsafe_allow_html=True)
                
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.markdown(f'<div class="premium-metric" style="border-left-color: #ffd700;"><div class="metric-title" style="color: #ffd700;">🔥 Tatlı Enerji Oranı</div><div class="metric-value">{tatli.get("calories", "N/A")}</div></div>', unsafe_allow_html=True)
                with t_col2:
                    st.markdown(f'<div class="premium-metric" style="border-left-color: #ffd700;"><div class="metric-title" style="color: #ffd700;">🥂 Sunum Protokolü</div><div class="metric-value">{kisi_sayisi} Kişilik İkram</div></div>', unsafe_allow_html=True)
                
                st.markdown("<h5 style='color: #ffd700;'>🛒 Tatlı İçin Gerekli Kiler Malzemeleri</h5>", unsafe_allow_html=True)
                
                t_temiz = malzemeleri_temizle(tatli.get("ingredients", []))
                
                t_tags_html = "".join([f"<span class='ingredient-tag' style='border-color: #b8860b; color: #ffd700;'>✨ {m}</span>" for m in t_temiz])
                st.markdown(f"<div style='margin-bottom: 2rem;'>{t_tags_html}</div>", unsafe_allow_html=True)
                
                st.markdown("<h5 style='color: #ffd700; margin-bottom: 1rem;'>👨‍🍳 Şefin Gizli Tatlı Yapılış Adımları</h5>", unsafe_allow_html=True)
                if isinstance(t_adımlar, list):
                    for adim in t_adımlar: st.write(f"**•** {adim}")
                elif isinstance(t_adımlar, dict):
                    for k, v in t_adımlar.items(): st.write(f"**{k}:** {v}")
                else: st.write(str(t_adımlar))
                
                st.markdown('</div>', unsafe_allow_html=True)
                
    st.markdown("<hr style='border-color: #2d333f; margin-top: 2rem;'><p style='text-align: center; color: #586069; font-size: 0.75rem; letter-spacing: 1px;'>AI GOURMET KITCHEN © 2026</p>", unsafe_allow_html=True)
