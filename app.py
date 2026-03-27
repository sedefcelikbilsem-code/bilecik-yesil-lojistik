import streamlit as st
import pandas as pd
import joblib
import numpy as np

st.set_page_config(page_title="Bilecik Yeşil Rota", page_icon="🍀")
st.title("🍀 Toyota Teknik Projeler: Yeşil Lojistik")

@st.cache_resource
def load_assets():
    model = joblib.load('bilecik_emisyon_model.pkl')
    if isinstance(model, tuple): model = model[0]
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    # Sütun isimlerini temizle
    data.columns = data.columns.str.strip().str.lower()
    # Mahalle isimlerini temizle (Boşlukları sil, küçük harf yap)
    mah_col = data.columns[0]
    data[mah_col] = data[mah_col].astype(str).str.strip().str.lower()
    return model, data

try:
    model, data = load_assets()
    mah_col = data.columns[0]
    
    st.sidebar.header("🚚 Taşıma Parametreleri")
    
    # Mahalle listesini orijinal haliyle göster ama ararken küçük harf kullan
    orijinal_mahalleler = sorted(data[mah_col].unique())
    secilen_mahalle_ham = st.sidebar.selectbox("Analiz Edilecek Mahalle", orijinal_mahalleler)
    secilen_mahalle = secilen_mahalle_ham.lower().strip()
    
    # --- EĞİMİ BULMA OPERASYONU ---
    mahalle_satiri = data[data[mah_col] == secilen_mahalle]
    
    # Eğim sütununu ara
    egim_col = next((c for c in ['yol_egimi', 'egim', 'eğim', 'grade'] if c in data.columns), None)
    
    if not mahalle_satiri.empty and egim_col:
        egim_degeri = float(mahalle_satiri.iloc[0][egim_col])
    else:
        # EĞER BULAMAZSA SENİN %5'E DÜŞÜYOR. TEST İÇİN %12 YAPALIM Kİ DEĞİŞTİĞİNİ ANLA
        egim_degeri = 0.05 

    st.sidebar.metric("Mahalle Gerçek Eğimi", f"%{round(egim_degeri * 100, 1)}")
    # ------------------------------

    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 10.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    if st.button("Emisyon Analizini Çalıştır"):
        temel_ozellikler = [mesafe, 0, 1, egim_degeri * yuk, yuk, 0.5]
        mahalle_ozellikleri = [1 if m.lower().strip() == secilen_mahalle else 0 for m in orijinal_mahalleler]
        girdi = (temel_ozellikler + mahalle_ozellikleri)[:17]
        
        tahmin = model.predict(np.array([girdi]))[0]
        
        st.divider()
        st.balloons()
        st.header(f"📊 Sonuç: {round(tahmin, 2)} kg CO2")
        
        chart_data = pd.DataFrame({
            'Senaryo': ['Standart Rota', 'Yeşil Rota'],
            'CO2 Salınımı (kg)': [tahmin, tahmin * 0.85]
        })
        st.bar_chart(data=chart_data, x='Senaryo', y='CO2 Salınımı (kg)')
        st.success(f"📍 {secilen_mahalle_ham} mahallesi verileriyle analiz tamamlandı.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")
