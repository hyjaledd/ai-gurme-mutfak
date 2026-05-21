import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from google import genai
from google.genai import types

# --- BULUT AYARLARI ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MONGO_URI = os.environ.get("MONGO_URI")

if not API_KEY or not MONGO_URI:
    raise ValueError("🚨 API_KEY veya MONGO_URI eksik! Lütfen Render panelinden kontrol edin.")

# --- YENİ NESİL GEMINI İSTEMCİSİ (GOOGLE-GENAI SÜRÜMÜ) ---
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
    kisi_sayisi: int
    kalori_hedefi: str
    gosterilen_tarifler: List[str]

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
    print(f"🤖 AI Şef Tetiklendi: {istek.ogun} öğünü için tarif hazırlanıyor...")
    yasakli_metin = ", ".join(istek.gosterilen_tarifler) if istek.gosterilen_tarifler else "Yok"
    
    prompt = f"""
    Sen profesyonel bir yapay zeka şefi ve diyetisyensin.
    Müşterinin Dolabındaki Malzemeler: {', '.join(istek.malzemeler)}
    İstediği Öğün Tipi: {istek.ogun}
    Porsiyon: Tam olarak {istek.kisi_sayisi} Kişilik
    Müşterinin Kişi Başı Kalori Hedefi: {istek.kalori_hedefi}
    
    ⚠️ Kesinlikle bu isimlerden farklı 3 yemek üretmelisin: [{yasakli_metin}]
    
    GÖREVİN: Öğüne uygun TAM 3 FARKLI TARİF üret. 
    Her tarif objesinin içinde mutlaka 'title', 'ingredients', 'instructions', 'calories' ve 'visual_keyword' alanları eksiksiz yer almalıdır.
    YANIT FORMATI SADECE GEÇERLİ BİR JSON ARRAY OLMALIDIR. Ekstra hiçbir metin veya markdown işareti ekleme.
    """

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
        
        # Streamlit arayüzünde tasarımın kırılmaması için sabit bir arka plan iştah açıcı görsel linki ekliyoruz
        for t in tarifler:
            t["image_path"] = "https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=800&auto=format&fit=crop"
        
        veritabanina_kaydet(tarifler)
        return {"tarifler": tarifler}

    except Exception as e:
        print(f"🚨 FONKSİYON İÇİNDE HATA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
