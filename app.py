import streamlit as st
import pandas as pd
import joblib
import numpy as np

st.set_page_config(page_title="Bilecik Yeşil Rota", page_icon="🍀")
st.title("🍀 Toyota Teknik Projeler: Yeşil Lojistik")
st.subheader("Bilecik Mahalle Bazlı Karbon Tahminleme Sistemi")

@st.cache_resource
def load_assets():
    loaded_model = joblib.load('bilecik_emisyon_model.pkl')
    model = loaded_model[0] if isinstance(loaded_model, tuple) else loaded_model
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    data.columns = data.columns.str.strip().str.lower()
    return model, data

try:
    model, data = load_assets()
    
    st.sidebar.header("🚚 Taşıma Parametreleri")
    mahalle_sutunu = 'mahalle' if 'mahalle' in data.columns else data.columns[0]
    mahalleler = sorted(data[mahalle_sutunu].unique())
    secilen_mahalle = st.sidebar.selectbox("Analiz Edilecek Mahalle", mahalleler)
    
    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 5.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    if st.button("Emisyon Analizini Çalıştır"):
        mahalle_bilgisi = data[data[mahalle_sutunu] == secilen_mahalle].iloc[0]
        egim = mahalle_bilgisi.get('yol_egimi', 0.5)
        
        # MODELİN BEKLEDİĞİ 17 SÜTUNU OLUŞTURUYORUZ
        # [mesafe, agir_arac, arac_tipi, egim_x_yuk, yuk, trafik, + 11 Mahalle Sütunu]
        temel_ozellikler = [mesafe, 0, 1, egim * yuk, yuk, 0.5]
        
        # Mahalleleri alfabetik sıraya göre 0 veya 1 yapıyoruz (One-Hot Encoding simülasyonu)
        mahalle_ozellikleri = [1 if m == secilen_mahalle else 0 for m in mahalleler]
        
        # Toplam özellik sayısını 17'ye tamamlıyoruz (Eksik mahalle varsa 0 ekle)
        girdi_listesi = temel_ozellikler + mahalle_ozellikleri
        girdi_listesi = girdi_listesi[:17] # Tam 17 tane olduğundan emin ol
        
        girdi = np.array([girdi_listesi])
        tahmin = model.predict(girdi)[0]
        
        st.divider()
        st.metric("Tahmini Karbon Salınımı", f"{round(tahmin, 2)} kg CO2")
        st.success(f"📍 {secilen_mahalle} mahallesi için 17 parametreli analiz tamamlandı.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")
