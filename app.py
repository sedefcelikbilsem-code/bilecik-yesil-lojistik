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
    
    # --- YENİ EKLENEN KISIM: Eğim Bilgisi ---
    mahalle_bilgisi = data[data[mahalle_sutunu] == secilen_mahalle].iloc[0]
    egim_sutunu = 'yol_egimi' if 'yol_egimi' in data.columns else 'egim'
    mahalle_egimi = mahalle_bilgisi.get(egim_sutunu, 0.5)
    
    # Eğim değerini sol tarafta gösteriyoruz
    st.sidebar.info(f"📍 Seçilen Mahalle Eğimi: %{round(mahalle_egimi * 100, 1)}")
    # ---------------------------------------
    
    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 5.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    if st.button("Emisyon Analizini Çalıştır"):
        # 17 Feature Fix
        temel_ozellikler = [mesafe, 0, 1, mahalle_egimi * yuk, yuk, 0.5]
        mahalle_ozellikleri = [1 if m == secilen_mahalle else 0 for m in mahalleler]
        girdi_listesi = (temel_ozellikler + mahalle_ozellikleri)[:17]
        
        girdi = np.array([girdi_listesi])
        tahmin = model.predict(girdi)[0]
        
        st.divider()
        st.balloons()
        st.metric("Tahmini Karbon Salınımı", f"{round(tahmin, 2)} kg CO2")
        st.success(f"📍 {secilen_mahalle} mahallesi analizi tamamlandı.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")
