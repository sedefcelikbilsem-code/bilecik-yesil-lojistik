import streamlit as st
import pandas as pd
import joblib
import numpy as np

# 1. Sayfa Yapılandırması ve Başlık
st.set_page_config(page_title="Bilecik Yeşil Lojistik", layout="wide")
st.title("🍀 Toyota Teknik Projeler: Yeşil Rota Karar Destek Sistemi")
st.markdown("---")

# 2. Model ve Verilerin Yüklenmesi
@st.cache_resource # Modelin her seferinde tekrar yüklenip sistemi yavaşlatmasını engeller
def load_assets():
    model = joblib.load('bilecik_emisyon_model.pkl')
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    return model, data

model, mahalle_df = load_assets()

# 3. Yan Menü (Input Paneli)
st.sidebar.header("🚚 Taşıma Parametreleri")
arac_secimi = st.sidebar.selectbox("Araç Tipi", ["Hafif Kamyonet", "Orta Kamyon", "Ağır TIR"])
yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 5.0)

# Araç tipini sayısal veriye çevirme (Modelin eğitilme şekline göre)
arac_map = {"Hafif Kamyonet": 1, "Orta Kamyon": 2, "Ağır TIR": 3}

# 4. Ana Panel (Rota Seçimi)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Rota Belirleme")
    baslangic = st.selectbox("Başlangıç Noktası", mahalle_df['mahalle'].unique())
    varis = st.selectbox("Varış Noktası", mahalle_df['mahalle'].unique())
    mesafe = st.number_input("Tahmini Mesafe (km)", min_value=0.1, value=5.0)

# 5. ML Hesaplama ve Optimizasyon
if st.button("Emisyon Analizini Çalıştır"):
    # Mahalle verilerini çekiyoruz
    mahalle_bilgisi = mahalle_df[mahalle_df['mahalle'] == baslangic].iloc[0]
    
    # Modelin beklediği giriş formatını hazırlıyoruz (Görseldeki Feature Importance sırasına göre)
    # [mesafe, agir_arac, arac_tipi, egim, trafik vb.]
    girdi = np.array([[mesafe, 1 if arac_secimi=="Ağır TIR" else 0, arac_map[arac_secimi], 
                       mahalle_bilgisi['yol_egimi'], yuk, 0.5]]) # 0.5 trafik varsayılan
    
    tahmin = model.predict(girdi)[0]
    
    # Sonuçları Gösterme
    st.markdown("---")
    res1, res2 = st.columns(2)
    
    with res1:
        st.metric(label="Tahmini Karbon Salınımı", value=f"{round(tahmin, 2)} kg CO2")
        st.info(f"Seçilen Mahalle: {baslangic} | Eğim Zorluğu: {mahalle_bilgisi['yol_egimi']}")
    
    with res2:
        # Karşılaştırmalı bir bar grafik
        st.write("📊 Rota Verimlilik Analizi")
        chart_data = pd.DataFrame({
            'Senaryo': ['Senin Rotan', 'Toyota Yeşil Hedef'],
            'Emisyon': [tahmin, tahmin * 0.85] # %15 iyileştirme hedefi
        })
        st.bar_chart(chart_data, x='Senaryo', y='Emisyon', color='#2ecc71')

st.sidebar.markdown("---")
st.sidebar.write("Bilecik BİLSEM - 2026")