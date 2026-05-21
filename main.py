import os
import json
import urllib.parse
import requests
import hashlib
import time
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# --- API AYARLARI ---
API_KEY = "AIzaSyB2lfVZxzXLwFD_Wr9NYJuRshcFXg1lmX8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOSYA_ADI = "pro_tarif_veritabani.json"

class TarifIsteği(BaseModel):
    malzemeler: List[str]
    ogun: str
    kisi_sayisi: int
    kalori_hedefi: str
    gosterilen_tarifler: List[str]

def resim_indir_ve_kaydet(keyword: str, title: str):
    os.makedirs("assets/images", exist_ok=True)
    
    isim_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
    yerel_yol = f"assets/images/tarif_{isim_hash}.jpg"
    
    if os.path.exists(yerel_yol):
        return yerel_yol
        
    try:
        ai_prompt = urllib.parse.quote(f"beautiful colorful digital illustration of {keyword} food, 2d flat vector style, minimalist, appetizing, UI design asset")
        url = f"https://image.pollinations.ai/prompt/{ai_prompt}?width=800&height=500&nologo=true"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=25)
        
        if response.status_code == 200:
            with open(yerel_yol, 'wb') as f:
                f.write(response.content)
            print(f"🎨 AI Ressam Başarıyla Çizdi: {title}")
            return yerel_yol
        else:
            raise Exception(f"HTTP Hata Kodu: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ İllüstrasyon çizilemedi ({title}): {e}")
        # --- ZARİF ACİL DURUM GÖRSELİ (Dark Moody Chef Kitchen) ---
        return "https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=800&auto=format&fit=crop"

def veritabanina_kaydet(yeni_tarifler):
    mevcut_veriler = []
    if os.path.exists(DOSYA_ADI):
        try:
            with open(DOSYA_ADI, "r", encoding="utf-8") as f:
                icerik = f.read().strip()
                if icerik:
                    mevcut_veriler = json.loads(icerik)
        except Exception:
            pass

    mevcut_veriler.extend(yeni_tarifler)
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(mevcut_veriler, f, ensure_ascii=False, indent=2)
    print(f"📈 Veritabanı Büyüdü! Toplam Tarif Sayısı: {len(mevcut_veriler)}")

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

    GÖREVİN:
    Müşterinin seçtiği öğüne uygun TAM 3 FARKLI TARİF üret. 
    Listede olmayan hiçbir ekstra malzemeyi (su, sıvı yağ ve tuz hariç) kullanma.

    SÜRE KATEGORİLERİ:
    1. Pratik (5-15 Dk)
    2. Orta Zorluk (15-30 Dk)
    3. Detaylı (30+ Dk)

    YANIT FORMATI (SADECE GEÇERLİ BİR JSON ARRAY OLMALIDIR):
    [
      {{
        "kategori": "5-15 Dakika",
        "title": "Yemek Adı",
        "duration": "10 dk",
        "calories_per_person": "350 kcal",
        "visual_keyword": "soup", 
        "required_ingredients": ["Ölçülü Malzeme 1"],
        "instructions": ["1. Adım"]
      }},
      {{
        "kategori": "15-30 Dakika",
        "title": "Yemek Adı",
        "duration": "25 dk",
        "calories_per_person": "420 kcal",
        "visual_keyword": "salad",
        "required_ingredients": ["Ölçülü Malzeme 1"],
        "instructions": ["1. Adım"]
      }},
      {{
        "kategori": "30+ Dakika",
        "title": "Yemek Adı",
        "duration": "45 dk",
        "calories_per_person": "600 kcal",
        "visual_keyword": "stew",
        "required_ingredients": ["Ölçülü Malzeme 1"],
        "instructions": ["1. Adım"]
      }}
    ]
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        
        raw_text = response.text
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        tarifler = json.loads(raw_text)
        
        for t in tarifler:
            anahtar_kelime = t.get("visual_keyword", "food")
            yemek_adi = t["title"]
            t["image_path"] = resim_indir_ve_kaydet(anahtar_kelime, yemek_adi)
            time.sleep(2)
        
        veritabanina_kaydet(tarifler)
        return {"tarifler": tarifler}

    except Exception as e:
        print(f"🔥 DETAYLI HATA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Şef tarif üretemedi: {str(e)}")