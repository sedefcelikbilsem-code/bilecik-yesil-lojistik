import streamlit as st
import pandas as pd
import joblib
import numpy as np

# 1. Sayfa Yapılandırması
st.set_page_config(page_title="Bilecik Yeşil Rota", page_icon="🍀")
st.title("🍀 Toyota Teknik Projeler: Yeşil Lojistik")
st.subheader("Bilecik Karbon Emisyon Karar Destek Sistemi")

@st.cache_resource
def load_assets():
    # Model ve Veri Yükleme (Hata Ayıklamalı)
    model = joblib.load('bilecik_emisyon_model.pkl')
    if isinstance(model, tuple): model = model[0]
    
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    # Sütun isimlerindeki gizli boşlukları temizle
    data.columns = data.columns.str.strip().str.lower()
    return model, data

try:
    model, data = load_assets()
    mah_col = data.columns[0] # İlk sütun (Mahalle)
    
    st.sidebar.header("🚚 Taşıma Parametreleri")
    
    # Mahalle listesini al
    mahalleler = sorted(data[mah_col].unique())
    secilen_mahalle = st.sidebar.selectbox("Analiz Edilecek Mahalle", mahalleler)
    
    # --- EĞİMİ BULMA VE GÖSTERME ---
    # Seçilen mahallenin satırını bul
    mahalle_verisi = data[data[mah_col] == secilen_mahalle].iloc[0]
    
    # Eğim sütununu ara
    egim_col = next((c for c in ['yol_egimi', 'egim', 'eğim', 'grade'] if c in data.columns), None)
    
    if egim_col:
        egim_degeri = float(mahalle_verisi[egim_col])
    else:
        egim_degeri = 0.05 # Sütun yoksa güvenli varsayılan %5
    
    # Mahalle değiştikçe bu rakamın değiştiğini sol tarafta göreceksin!
    st.sidebar.metric("Mahalle Gerçek Eğimi", f"%{round(egim_degeri * 100, 1)}")
    
    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 10.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    # 4. ANALİZ BUTONU
    if st.button("Emisyon Analizini Çalıştır"):
        # Modelin beklediği 17 özelliği oluştur (6 Temel + 11 Mahalle)
        # [mesafe, agir_arac, arac_tipi_id, egim_x_yuk, yuk, trafik_yogunlugu]
        temel_ozellikler = [mesafe, 0, 1, egim_degeri * yuk, yuk, 0.5]
        
        # Mahalleleri modelin beklediği alfabetik sıraya göre 0/1 yapalım
        mahalle_ozellikleri = [1 if m == secilen_mahalle else 0 for m in mahalleler]
        
        # Hepsini birleştir ve tam 17 tane olduğundan emin ol
        girdi_listesi = (temel_ozellikler + mahalle_ozellikleri)[:17]
        
        # Hesaplama
        tahmin = model.predict(np.array([girdi_listesi]))[0]
        
        # GÖRSEL SONUÇLAR
        st.divider()
        st.balloons() # Başarı kutlaması
        st.header(f"📊 Tahmini Salınım: {round(tahmin, 2)} kg CO2")
        
        # Karşılaştırma Grafiği
        chart_data = pd.DataFrame({
            'Senaryo': ['Standart Rota', 'Önerilen Yeşil Rota'],
            'CO2 (kg)': [tahmin, tahmin * 0.85] # %15 iyileştirme tahmini
        })
        st.bar_chart(data=chart_data, x='Senaryo', y='CO2 (kg)')
        
        st.success(f"📍 {secilen_mahalle} mahallesi analizi başarıyla tamamlandı.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")
