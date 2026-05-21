import streamlit as st
import requests

st.set_page_config(page_title="AI Mutfak Robotu", page_icon="🍳", layout="wide")

# --- BACKEND BAĞLANTI ADRESİ ---
BACKEND_URL = "https://ai-gurme-mutfak.onrender.com"

st.title("🍳 Yapay Zeka Destekli Gurme Mutfak Robotu")
st.write("Dolabınızdaki malzemeleri seçin, AI Şef size özel kalori hedefli tarifleri hazırlasın!")

# Hafıza Yönetimi (Session State)
if "gosterilen_tarifler" not in st.session_state:
    st.session_state.gosterilen_tarifler = []
if "mevcut_tarifler" not in st.session_state:
    st.session_state.mevcut_tarifler = None

# Kullanıcı Girdileri
malzemeler_input = st.text_input("Dolaptaki Malzemeler (Virgülle ayırarak yazın):", "Yumurta, Domates, Biber, Kaşar Peyniri")
ogun = st.selectbox("Öğün Seçimi:", ["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Aperatif", "Tatlı"])
kisi_sayisi = st.slider("Kişi Sayısı:", 1, 10, 2)
kalori_hedefi = st.selectbox("Kişi Başı Kalori Hedefi:", ["Fark Etmez", "Düşük Kalori (<300 kcal)", "Dengeli (300-600 kcal)", "Yüksek Enerji (>600 kcal)"])

malzemeler_listesi = [m.strip() for m in malzemeler_input.split(",") if m.strip()]

if st.button("✨ GURME MENÜMÜ HAZIRLA", type="primary"):
    if not malzemeler_listesi:
        st.error("Lütfen en az bir malzeme yazın!")
    else:
        with st.spinner("AI Şef malzemelerinizi inceliyor, harika tarifler tasarlıyor..."):
            payload = {
                "malzemeler": malzemeler_listesi,
                "ogun": ogun,
                "kisi_sayisi": kisi_sayisi,
                "kalori_hedefi": kalori_hedefi,
                "gosterilen_tarifler": st.session_state.gosterilen_tarifler
            }
            
            try:
                response = requests.post(f"{BACKEND_URL}/tarif-bul", json=payload, timeout=60)
                if response.status_code == 200:
                    st.session_state.mevcut_tarifler = response.json().get("tarifler", [])
                    # Beğenilmeyen geçmiş havuzuna isimleri ekle
                    for t in st.session_state.mevcut_tarifler:
                        if t["title"] not in st.session_state.gosterilen_tarifler:
                            st.session_state.gosterilen_tarifler.append(t["title"])
                else:
                    st.error(f"Backend sunucusundan bir hata döndü (Kod: {response.status_code}). Teknik Detay: {response.text}")
            except Exception as e:
                st.error(f"Sunucuya bağlanılamadı. AI Şef şu an uykuda veya güncelleniyor olabilir. Hata: {e}")

# Tarif kartlarını ekrana basma alanı
if st.session_state.mevcut_tarifler:
    st.success("🤖 AI Şefinizin Sizin İçin Seçtiği Özel Menü:")
    cols = st.columns(3)
    
    for idx, tarif in enumerate(st.session_state.mevcut_tarifler):
        with cols[idx % 3]:
            st.image(tarif.get("image_path"), use_container_width=True)
            st.subheader(tarif.get("title", "İsimsiz Gurme Lezzeti"))
            st.markdown(f"🔥 **Kalori Değeri:** {tarif.get('calories', 'Belirtilmedi')}")
            
            st.write("**İçindekiler:**")
            st.write(", ".join(tarif.get("ingredients", [])))
            
            st.write("**Hazırlanışı:**")
            st.write(tarif.get("instructions", "Tarif adımları oluşturulurken bir hata oluştu."))
            st.write("---")
