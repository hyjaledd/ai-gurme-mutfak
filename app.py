# --- ESKİ GÜZEL GÖRÜNÜMÜ GERİ GETİREN AKILLI GÖRSEL MOTORU ---
if st.session_state.mevcut_tarifler:
    st.write("---")
    st.success("🧑‍🍳 AI Şefinizin Sizin İçin Tasarladığı Gurme Menü:")
    
    cols = st.columns(3)
    
    # Yemek türlerine göre harika, yüksek çözünürlüklü profesyonel fotoğraf havuzu
    gorsel_havuzu = {
        "yumurta": "https://images.unsplash.com/photo-1525351484163-7529414344d8?q=80&w=600&auto=format&fit=crop",
        "omlet": "https://images.unsplash.com/photo-1494597564530-871f2b93ac55?q=80&w=600&auto=format&fit=crop",
        "menemen": "https://images.unsplash.com/photo-1590412200988-a436bb705300?q=80&w=600&auto=format&fit=crop",
        "kahvalti": "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?q=80&w=600&auto=format&fit=crop",
        "tavuk": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?q=80&w=600&auto=format&fit=crop",
        "et": "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=600&auto=format&fit=crop",
        "kofte": "https://images.unsplash.com/photo-1529042410759-befb1204b468?q=80&w=600&auto=format&fit=crop",
        "makarna": "https://images.unsplash.com/photo-1563379971899-660589a01cc3?q=80&w=600&auto=format&fit=crop",
        "salata": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?q=80&w=600&auto=format&fit=crop",
        "corba": "https://images.unsplash.com/photo-1547592165-e1d17fed6005?q=80&w=600&auto=format&fit=crop",
        "tatli": "https://images.unsplash.com/photo-1551024601-bec78aea704b?q=80&w=600&auto=format&fit=crop",
        "krep": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?q=80&w=600&auto=format&fit=crop",
        "patates": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?q=80&w=600&auto=format&fit=crop",
        "sandvic": "https://images.unsplash.com/photo-1509722747041-616f39b57569?q=80&w=600&auto=format&fit=crop",
        "borek": "https://images.unsplash.com/photo-1608039755401-742074f0548d?q=80&w=600&auto=format&fit=crop"
    }

    for idx, tarif in enumerate(st.session_state.mevcut_tarifler):
        with cols[idx % 3]:
            # Akıllı Eşleştirme: Yemek başlığına bakıp en uygun görseli seçer
            baslik_canli = tarif.get("title", "").lower()
            secilen_gorsel = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=600&auto=format&fit=crop" # Genel yemek görseli (yedek)
            
            for anahtar, link in gorsel_havuzu.items():
                if anahtar in baslik_canli:
                    secilen_gorsel = link
                    break
            
            # Şık Kart Tasarımı
            st.image(secilen_gorsel, use_container_width=True, caption=tarif.get("title"))
            
            # Başlık ve Kalori Alanı (Görsel olarak belirginleştirildi)
            st.markdown(f"### 🍽️ {tarif.get('title', 'Gurme Lezzeti')}")
            st.markdown(f"🔥 **Enerji Değeri:** `{tarif.get('calories', 'Belirtilmedi')}`")
            
            # İçindekiler Alanı
            st.markdown("##### 🛒 İçindekiler")
            st.caption(", ".join(tarif.get("ingredients", [])))
            
            # Hazırlanışı Alanı (Okunabilirliği artırmak için expander içine aldık)
            with st.expander("👨‍🍳 Hazırlanışı ve Adımları Gör", expanded=True):
                st.write(tarif.get("instructions", "Tarif adımları yüklenemedi."))
            st.write("---")
