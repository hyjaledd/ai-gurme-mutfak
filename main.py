import os
import json
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from google import genai
from google.genai import types

# --- BULUT AYARLARI ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MONGO_URI = os.environ.get("MONGO_URI")

if not API_KEY or not MONGO_URI:
    raise ValueError("🚨 API_KEY veya MONGO_URI eksik!")

# --- YENİ NESİL GEMINI İSTEMCİSİ ---
ai_client = genai.Client(api_key=API_KEY)

# --- BULUT VERİTABANI BAĞLANTI KÖPRÜSÜ ---
try:
    client = MongoClient(
        MONGO_URI, 
        serverSelectionTimeoutMS=5000, 
        connectTimeoutMS=5000,
        tlsAllowInvalidCertificates=True
    )
    db = client["gurme_mutfak_db"]          
    tarif_koleksiyonu = db["tarifler"]     
    client.admin.command('ping')
    print("✅ MÜJDE: MongoDB Atlas Bulut Veritabanına Başarıyla Bağlanıldı!")
except Exception as e:
    print(f"🚨 MongoDB Bağlantı Hatası: {str(e)}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TarifIsteği(BaseModel):
    malzemeler: List[str]
    ogun: str
    kisi_sayisi: Optional[int] = 2          
    kalori_hedefi: Optional[str] = "Fark Etmez" 
    gosterilen_tarifler: Optional[List[str]] = [] 

def veritabanina_kaydet(yeni_tarifler):
    try:
        if yeni_tarifler:
            tarif_koleksiyonu.insert_many(yeni_tarifler)
            toplam_adet = tarif_koleksiyonu.count_documents({})
            print(f"📈 Bulut Veritabanı Güncellendi! Toplam Tarif Sayısı: {toplam_adet}")
    except Exception as e:
        print(f"⚠️ Veritabanı kayıt hatası: {e}")

@app.post("/tarif-bul")
def tarif_bul(istek: TarifIsteği):
    malzemeler = istek.malzemeler if istek.malzemeler else []
    ogun = istek.ogun if istek.ogun else "Kahvaltı"
    kisi_sayisi = istek.kisi_sayisi if istek.kisi_sayisi else 2
    kalori_hedefi = istek.kalori_hedefi if istek.kalori_hedefi else "Fark Etmez"
    gosterilenler = istek.gosterilen_tarifler if istek.gosterilen_tarifler else []

    print(f"🤖 AI Şef Tetiklendi: {ogun} öğünü için tarif hazırlanıyor...")
    yasakli_metin = ", ".join(gosterilenler) if gosterilenler else "Yok"
    
    prompt = f"""
    Sen profesyonel bir yapay zeka şefi ve diyetisyensin.
    Müşterinin Dolabındaki Malzemeler: {', '.join(malzemeler)}
    İstediği Öğün Tipi: {ogun}
    Porsiyon: Tam olarak {kisi_sayisi} Kişilik
    Müşterinin Kişi Başı Kalori Hedefi: {kalori_hedefi}
    
    ⚠️ Kesinlikle bu isimlerden farklı 3 yemek üretmelisin: [{yasakli_metin}]
    
    GÖREVİN: Öğüne uygun TAM 3 FARKLI TARİF üret. 
    Her tarif objesinin içinde mutlaka 'title', 'ingredients', 'instructions', 'calories' ve 'visual_keyword' alanları eksiksiz yer almalıdır.
    YANIT FORMATI SADECE GEÇERLİ BİR JSON ARRAY OLMALIDIR. Ekstra hiçbir metin veya markdown işareti ekleme.
    """

    # --- GOOGLE 503 HATASI İÇİN AKILLI RETRY (YENİDEN DENEME) MOTORU ---
    max_deneme = 3
    bekleme_suresi = 2 # Saniye cinsinden
    
    for deneme in range(max_deneme):
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            
            raw_text = response.text
            tarifler = json.loads(raw_text)
            
            for t in tarifler:
                t["image_path"] = "https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=800&auto=format&fit=crop"
            
            veritabanina_kaydet(tarifler)
            
            for t in tarifler:
                if "_id" in t:
                    t["_id"] = str(t["_id"])
            
            # Eğer başarılı olduysa döngüden çık ve veriyi gönder
            return {"tarifler": tarifler}

        except Exception as e:
            # Eğer hata Google 503 veya başka bir şeyse ve hâlâ deneme hakkımız varsa bekle ve tekrar et
            if deneme < max_deneme - 1:
                print(f"⚠️ Google API meşgul (Deneme {deneme + 1}/{max_deneme}). {bekleme_suresi} saniye sonra tekrar deneniyor... Hata: {str(e)}")
                time.sleep(bekleme_suresi)
                bekleme_suresi *= 2 # Üstel bekleme (Önce 2sn, sonra 4sn bekleyecek)
            else:
                # Tüm denemeler bittiyse ve hâlâ patlıyorsa son çare olarak hatayı fırlat
                print(f"🚨 TÜM DENEMELER BAŞARISIZ OLDU: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Google API Yoğunluk Sınırı Aşıldı: {str(e)}")
