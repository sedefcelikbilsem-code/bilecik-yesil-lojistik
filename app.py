import streamlit as st
import pandas as pd
import joblib
import numpy as np

# 1. Sayfa Ayarları ve Başlık
st.set_page_config(page_title="Bilecik Yeşil Rota", page_icon="🍀")
st.title("🍀 Toyota Teknik Projeler: Yeşil Lojistik")
st.subheader("Bilecik Mahalle Bazlı Karbon Tahminleme Sistemi")

# 2. Model ve Veri Yükleme (Hata Ayıklamalı)
@st.cache_resource
def load_assets():
    # Modeli yükle
    loaded_model = joblib.load('bilecik_emisyon_model.pkl')
    # Eğer model bir tuple içindeyse ilk elemanı al
    model = loaded_model[0] if isinstance(loaded_model, tuple) else loaded_model
    
    # Veriyi yükle ve sütun isimlerini temizle
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    data.columns = data.columns.str.strip().str.lower() # Boşlukları sil ve küçük harf yap
    return model, data

try:
    model, data = load_assets()
    
    # 3. Kullanıcı Giriş Paneli (Kenar Çubuğu)
    st.sidebar.header("🚚 Taşıma Parametreleri")
    
    # Sütun isimlerine göre mahalle listesini çek
    mahalle_sutunu = 'mahalle' if 'mahalle' in data.columns else data.columns[0]
    secilen_mahalle = st.sidebar.selectbox("Analiz Edilecek Mahalle", data[mahalle_sutunu].unique())
    
    arac_tipi = st.sidebar.selectbox("Araç Tipi", ["Hafif Ticari", "Orta Sınıf Kamyon", "Ağır Vasata"])
    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 5.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    # 4. Hesaplama Motoru
    if st.button("Emisyon Analizini Çalıştır"):
        # Seçilen mahalle verisini bul
        mahalle_bilgisi = data[data[mahalle_sutunu] == secilen_mahalle].iloc[0]
        
        # 'yol_egimi' sütununu güvenli oku
        egim_sutunu = 'yol_egimi' if 'yol_egimi' in data.columns else 'egim'
        egim = mahalle_bilgisi.get(egim_sutunu, 0.5) 
        
        # Modelin beklediği 6 özellik (Görsel analizindeki sıralama)
        # [mesafe, agir_arac_mi, arac_tipi_id, egim_x_yuk, yuk, trafik_yogunlugu]
        arac_id = 3 if "Ağır" in arac_tipi else (2 if "Orta" in arac_tipi else 1)
        agir_arac = 1 if arac_id == 3 else 0
        
        girdi = np.array([[mesafe, agir_arac, arac_id, egim * yuk, yuk, 0.5]])
        tahmin = model.predict(girdi)[0]
        
        # 5. Sonuç Ekranı
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tahmini Karbon Salınımı", f"{round(tahmin, 2)} kg CO2")
        with col2:
            tasarruf = tahmin * 0.18 # Modelimizin %18 iyileştirme öngörüsü
            st.metric("Yeşil Rota Tasarrufu", f"{round(tasarruf, 2)} kg CO2", delta="-18%")
            
        st.info(f"📍 {secilen_mahalle} mahallesi için eğim ve yük analizi tamamlandı.")

except Exception as e:
    st.error(f"Sistem Başlatılamadı: {e}")
    st.info("Lütfen GitHub'daki dosya isimlerini (pkl ve csv) kontrol edin.")
