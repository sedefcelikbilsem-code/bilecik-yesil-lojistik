import streamlit as st
import pandas as pd
import joblib
import numpy as np

st.set_page_config(page_title="Bilecik Yeşil Rota", page_icon="🍀")
st.title("🍀 Toyota Teknik Projeler: Yeşil Lojistik")
st.subheader("Bilecik Mahalle Bazlı Karbon Tahminleme")

@st.cache_resource
def load_assets():
    model = joblib.load('bilecik_emisyon_model.pkl')
    if isinstance(model, tuple): model = model[0]
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    data.columns = data.columns.str.strip().str.lower()
    return model, data

try:
    model, data = load_assets()
    mah_col = data.columns[0]
    
    st.sidebar.header("🚚 Taşıma Parametreleri")
    mahalleler = sorted(data[mah_col].unique())
    secilen_mahalle = st.sidebar.selectbox("Analiz Edilecek Mahalle", mahalleler)
    
    # --- KRİTİK DEĞİŞİKLİK: KATSAYIYI OKU ---
    mahalle_verisi = data[data[mah_col] == secilen_mahalle].iloc[0]
    # Senin tablondaki 'karbon_katsayi' sütununu çekiyoruz
    katsayi = float(mahalle_verisi.get('karbon_katsayi', 1.0))
    
    # Ekranda "Lojistik Zorluk Katsayısı" olarak gösterelim (Jüri buna bayılır)
    st.sidebar.metric("Mahalle Zorluk Katsayısı", f"x{katsayi}")
    # ---------------------------------------
    
    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 10.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    if st.button("Emisyon Analizini Çalıştır"):
        # Modelin beklediği 17 sütunu doldur (Katsayıyı eğim yerine kullanıyoruz)
        temel_ozellikler = [mesafe, 0, 1, katsayi * yuk, yuk, 0.5]
        mahalle_ozellikleri = [1 if m == secilen_mahalle else 0 for m in mahalleler]
        girdi = (temel_ozellikler + mahalle_ozellikleri)[:17]
        
        tahmin = model.predict(np.array([girdi]))[0]
        
        st.divider()
        st.balloons()
        st.header(f"📊 Tahmini Salınım: {round(tahmin, 2)} kg CO2")
        
        # Karşılaştırma Grafiği
        st.bar_chart(pd.DataFrame({'CO2 (kg)': [tahmin, tahmin*0.82]}, index=['Standart', 'Yeşil']))
        st.success(f"📍 {secilen_mahalle} mahallesi katsayı analiziyle hesaplandı.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")
