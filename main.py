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
    raise ValueError("🚨 API_KEY veya MONGO_URI eksik! Lütfen Render panelinden kontrol edin.")

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
    print("✅ [SİSTEM] MongoDB Atlas Bulut Veritabanına Başarıyla Bağlanıldı!", flush=True)
except Exception as e:
    print(f"🚨 [HATA] MongoDB Bağlantı Hatası: {str(e)}", flush=True)

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
            kaydedilen_isimler = [t.get("title", "İsimsiz") for t in yeni_tarifler]
            tarif_koleksiyonu.insert_many(yeni_tarifler)
            toplam_adet = tarif_koleksiyonu.count_documents({})
            print(f"💾 [DB-KAYIT] {len(yeni_tarifler)} yeni tarif BAŞARIYLA KAYDEDİLDİ! Eklenenler: {kaydedilen_isimler} | Toplam Tarif: {toplam_adet}", flush=True)
    except Exception as e:
        print(f"⚠️ [DB-HATA] Veritabanı kayıt hatası: {e}", flush=True)

@app.post("/tarif-bul")
def tarif_bul(istek: TarifIsteği):
    malzemeler = istek.malzemeler if istek.malzemeler else []
    ogun = istek.ogun if istek.ogun else "Kahvaltı"
    kisi_sayisi = istek.kisi_sayisi if istek.kisi_sayisi else 2
    kalori_hedefi = istek.kalori_hedefi if istek.kalori_hedefi else "Fark Etmez"
    gosterilen_tender = istek.gosterilen_tarifler if istek.gosterilen_tarifler else []

    print(f"🔍 [SİSTEM] {ogun} öğünü için istek geldi. Veritabanı kontrol ediliyor...", flush=True)
    
    db_query = {
        "ogun": ogun,
        "title": {"$nin": gosterilen_tender}
    }
    
    all_candidates = list(tarif_koleksiyonu.find(db_query))
    matching_recipes = []
    
    for recipe in all_candidates:
        recipe_ing_lower = [i.lower() for i in recipe.get("ingredients", [])]
        match_count = 0
        
        for r_ing in recipe_ing_lower:
            for u_mat in malzemeler:
                if u_mat.lower() in r_ing:
                    match_count += 1
                    break
        
        if len(recipe_ing_lower) > 0 and (match_count / len(recipe_ing_lower)) >= 0.7:
            if "_id" in recipe:
                recipe["_id"] = str(recipe["_id"]) 
            matching_recipes.append(recipe)
            if len(matching_recipes) >= 4:
                break

    # Arşivde en az 4 tarif (3 ana + 1 tatlı) varsa direkt DB'den getir
    if len(matching_recipes) >= 4:
        okunan_isimler = [r.get("title", "İsimsiz") for r in matching_recipes]
        print(f"📦 [DB-OKUMA] Arşivden çekilen menü: {okunan_isimler}", flush=True)
        return {"tarifler": matching_recipes}

    print("🍳 [SİSTEM] Arşivde yeterli kombinasyon yok. Gemini 2.5 Pro zorunlu 4'lü menüyü tasarlıyor...", flush=True)
    
    yasakli_listesi = gosterilen_tender + [r["title"] for r in matching_recipes]
    yasakli_metin = ", ".join(yasakli_listesi) if yasakli_listesi else "Yok"
    
    prompt = f"""
    Sen profesyonel bir yapay zeka şefi ve diyetisyensin.
    Müşterinin Malzemeleri: {', '.join(malzemeler)}
    Öğün Tipi: {ogun}
    Porsiyon: {kisi_sayisi} Kişilik
    Kalori Hedefi: {kalori_hedefi}
    
    ⚠️ Yasaklı Yemekler (Bunları ÜRETME): [{yasakli_metin}]
    
    KESİN GÖREV KURALLARI: 
    TAM OLARAK 4 ADET TARİF İÇEREN BİR JSON ARRAY ÜRETMELİSİN. NE EKSİK NE FAZLA!
    - 1., 2. ve 3. Tarifler: Seçilen '{ogun}' öğününe uygun 'Ana Reçete' olmalıdır (is_bonus: false).
    - 4. Tarif: Mutlaka ama mutlaka eldeki malzemelerle yapılabilecek bir 'Bonus Tatlı' olmalıdır (is_bonus: true).
    
    Her tarif objesinin içinde 'title', 'ingredients', 'instructions', 'calories', 'visual_keyword' ve 'is_bonus' (boolean) alanları eksiksiz yer almalıdır.
    YANIT FORMATI SADECE GEÇERLİ BİR JSON ARRAY OLMALIDIR. Markdown (```json) kullanma, sadece saf JSON verisi döndür.
    """

    max_deneme = 5  
    bekleme_suresi = 3 
    
    for deneme in range(max_deneme):
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-pro', 
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            
            raw_text = response.text
            tarifler = json.loads(raw_text)
            
            for t in tarifler:
                t["ogun"] = ogun
                t["image_path"] = "[https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=800&auto=format&fit=crop](https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=800&auto=format&fit=crop)"
                if "is_bonus" not in t:
                    t["is_bonus"] = False
            
            # Garanti Altına Alma: Eğer AI 4 tarif üretti ama tatlı etiketini koymayı unuttuysa, sonuncuyu zorla tatlı yap
            if len(tarifler) >= 4 and not any(x.get("is_bonus") for x in tarifler):
                tarifler[-1]["is_bonus"] = True
            
            veritabanina_kaydet(tarifler)
            
            for t in tarifler:
                if "_id" in t:
                    t["_id"] = str(t["_id"])
            
            return {"tarifler": tarifler}

        except Exception as e:
            if deneme < max_deneme - 1:
                print(f"⚠️ [SİSTEM] API Geçici Pürüz Yaşadı (Deneme {deneme + 1}/{max_deneme}). {bekleme_suresi} saniye sonra tekrar deneniyor...", flush=True)
                time.sleep(bekleme_suresi)
                bekleme_suresi += 3 
            else:
                print(f"🚨 [HATA] TÜM DENEMELER BAŞARISIZ OLDU: {str(e)}", flush=True)
                raise HTTPException(status_code=500, detail=f"Google API Sınırı Aşıldı: {str(e)}")
