import os
import json
import re
import urllib.parse
import requests
import hashlib
import time
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient

# --- CRITICAL FIX: SUNUCU AÇILIRKEN KLASÖRÜ ANINDA OLUŞTUR ---
# Klasör açılışta var olacağı için FastAPI artık çökmeyecek.
os.makedirs("assets/images", exist_ok=True)

# --- GÜVENLİ BULUT AYARLARI ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MONGO_URI = os.environ.get("MONGO_URI")

if not API_KEY:
    raise ValueError("🚨 GEMINI_API_KEY bulunamadı!")
if not MONGO_URI:
    raise ValueError("🚨 MONGO_URI bulunamadı!")

# --- YAPAY ZEKA YAPILANDIRMASI ---
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- BULUT VERİTABANI BAĞLANTI KÖPRÜSÜ (TIMEOUT KORUMALI) ---
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["gurme_mutfak_db"]          
tarif_koleksiyonu = db["tarifler"]     

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RENDER_URL = "https://ai-gurme-mutfak.onrender.com"

class TarifIsteği(BaseModel):
    malzemeler: List[str]
    ogun: str
    kisi_sayisi: int
    kalori_hedefi: str
    gosterilen_tarifler: List[str]

# --- AI RESSAM MOTORU ---
def resim_indir_ve_kaydet(keyword: str, title: str):
    isim_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
    dosya_adi = f"tarif_{isim_hash}.jpg"
    yerel_yol = f"assets/images/{dosya_adi}"
    web_url = f"{RENDER_URL}/static/{dosya_adi}"
    
    if os.path.exists(yerel_yol):
        return web_url
        
    try:
        ai_prompt = urllib.parse.quote(f"beautiful colorful digital illustration of {keyword} food, 2d flat vector style, minimalist, appetizing, UI design asset")
        url = f"https://image.pollinations.ai/prompt/{ai_prompt}?width=800&height=500&nologo=true"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            with open(yerel_yol, 'wb') as f:
                f.write(response.content)
            print(f"🎨 AI Ressam Başarıyla Çizdi: {title}")
            return web_url
        else:
            raise Exception(f"HTTP Hata Kodu: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ İllüstrasyon çizilemedi ({title}): {e}")
        return "https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=800&auto=format&fit=crop"

# --- OTONOM BULUT VERİTABANI GÜNCELLEME FONKSİYONU ---
def veritabanina_kaydet(yeni_tarifler):
    try:
        if yeni_tarifler:
            tarif_koleksiyonu.insert_many(yeni_tarifler)
            toplam_adet = tarif_koleksiyonu.count_documents({})
            print(f"📈 Bulut Veritabanı Güncellendi! Toplam Ölümsüz Tarif Sayısı: {toplam_adet}")
    except Exception as e:
        print(f"⚠️ Veritabanına kaydedilirken hata oluştu: {e}")

@app.post("/tarif-bul")
def tarif_bul(istek: TarifIsteği):
    print(f"🤖 AI Şef Tetiklendi: {istek.kisi_sayisi} Kişilik {istek.ogun}...")
    yasakli_metin = ", ".join(istek.gosterilen_tarifler) if istek.gosterilen_tarifler else "Yok"
    
    prompt = f"""
    Sen profesyonel bir yapay zeka şefi ve diyetisyensin.
    Müşterinin Dolabındaki Malzemeler: {', '.join(istek.malzemeler)}
    İstediği Öğün Tipi: {istek.ogun}
    Porsiyon / Hedef Kitle: Tam olarak {istek.kisi_sayisi} Kişilik
    Müşterinin Kişi Başı Kalori Hedefi: {istek.kalori_hedefi}
    
    ⚠️ KRİTİK KURAL: Müşteri şu yemekleri zaten gördü ve BEĞENMEDİ. Kesinlikle bu isimlerden farklı 3 yemek üretmelisin:
    [{yasakli_metin}]

    GÖREVİN: Müşterinin seçtiği öğüne uygun TAM 3 FARKLI TARİF üret. 
    YANIT FORMATI SADECE GEÇERLİ BİR JSON ARRAY OLMALIDIR.
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        
        raw_text = response.text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            
        tarifler = json.loads(raw_text)
        
        for t in tarifler:
            anahtar_kelime = t.get("visual_keyword", "food")
            yemek_adi = t["title"]
            t["image_path"] = resim_indir_ve_kaydet(anahtar_kelime, yemek_adi)
            time.sleep(2)
        
        veritabanina_kaydet(tarifler)
        return {"tarifler": tarifler}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/static", StaticFiles(directory="assets/images"), name="static")
