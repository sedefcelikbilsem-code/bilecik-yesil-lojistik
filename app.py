import streamlit as st
import pandas as pd
import joblib
import numpy as np

# Sayfa Başlığı
st.set_page_config(page_title="Bilecik Yeşil Rota", page_icon="🍀")
st.title("🍀 Toyota Teknik Projeler: Yeşil Lojistik")

@st.cache_resource
def load_assets():
    # Model ve Veri Yükleme
    model = joblib.load('bilecik_emisyon_model.pkl')
    if isinstance(model, tuple): model = model[0]
    
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    
    # VERİ TEMİZLİĞİ: Sütun ve Mahalle isimlerini standart hale getiriyoruz
    data.columns = data.columns.str.strip().str.lower()
    # Mahalle sütunundaki tüm isimlerin başındaki/sonundaki boşlukları sil
    data.iloc[:, 0] = data.iloc[:, 0].astype(str).str.strip()
    
    return model, data

try:
    model, data = load_assets()
    
    st.sidebar.header("🚚 Taşıma Parametreleri")
    
    # Mahalle sütununu bul
    mahalle_sutunu = data.columns[0]
    mahalle_listesi = sorted(data[mahalle_sutunu].unique())
    
    secilen_mahalle = st.sidebar.selectbox("Analiz Edilecek Mahalle", mahalle_listesi)
    
    # --- DİNAMİK EĞİM ÇEKME ---
    # Seçilen mahalleyi tam eşleşme ile bul
    mahalle_satiri = data[data[mahalle_sutunu] == secilen_mahalle].iloc[0]
    
    # Eğim sütununu bul (yol_egimi veya egim)
    egim_col = 'yol_egimi' if 'yol_egimi' in data.columns else 'egim'
    
    # EĞİM DEĞERİNİ ÇEK (Eğer veri 0.5 ise bu %50 demektir, Bilecik verilerine göre düzenle)
    guncel_egim = float(mahalle_satiri[egim_col])
    
    # Eğim değerini sol menüde göster (Mahalle değiştikçe bu rakam DEĞİŞMELİ)
    st.sidebar.metric("Mahalle Eğimi", f"%{round(guncel_egim * 100, 1)}")
    # --------------------------

    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 10.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    if st.button("Emisyon Analizini Çalıştır"):
        # 17 Feature Yapısı
        temel_ozellikler = [mesafe, 0, 1, guncel_egim * yuk, yuk, 0.5]
        mahalle_ozellikleri = [1 if m == secilen_mahalle else 0 for m in mahalle_listesi]
        girdi = (temel_ozellikler + mahalle_ozellikleri)[:17]
        
        tahmin = model.predict(np.array([girdi]))[0]
        
        st.divider()
        st.balloons()
        st.header(f"📊 Tahmini Salınım: {round(tahmin, 2)} kg CO2")
        st.info(f"💡 {secilen_mahalle} mahallesi verileri başarıyla işlendi.")

except Exception as e:
    st.error(f"Veri Eşleşme Hatası: {e}")
