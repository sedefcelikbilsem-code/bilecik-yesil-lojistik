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
    # Modeli ve Veriyi Yükle
    model = joblib.load('bilecik_emisyon_model.pkl')
    if isinstance(model, tuple): model = model[0]
    
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    
    # VERİ TEMİZLİĞİ: Sütun isimlerini tamamen temizle (küçük harf ve boşluksuz)
    data.columns = [str(c).strip().lower() for c in data.columns]
    
    # Mahalle isimlerini de temizle (eşleşme hatasını önlemek için)
    mah_col = data.columns[0]
    data[mah_col] = data[mah_col].astype(str).str.strip().str.lower()
    
    return model, data

try:
    model, data = load_assets()
    mah_col = data.columns[0] # İlk sütun (Mahalle)
    
    st.sidebar.header("🚚 Taşıma Parametreleri")
    
    # Mahalle listesini orijinal haliyle (Title Case) gösterelim
    orijinal_mahalleler = sorted(data[mah_col].unique())
    secilen_mahalle_ham = st.sidebar.selectbox("Analiz Edilecek Mahalle", [m.title() for m in orijinal_mahalleler])
    
    # Arama yaparken tekrar küçük harfe çevirelim (Tam eşleşme garantisi)
    secilen_mahalle_search = secilen_mahalle_ham.lower().strip()
    
    # --- EĞİMİ BULMA VE GÖSTERME (Hata Avcısı Versiyon) ---
    mahalle_satiri = data[data[mah_col] == secilen_mahalle_search]
    
    # Eğim sütununu bulmak için anahtar kelimeleri tara
    egim_keywords = ['egim', 'yol_egimi', 'eğim', 'grade', 'slope']
    found_egim_col = next((c for c in data.columns if any(k in c for k in egim_keywords)), None)
    
    if not mahalle_satiri.empty and found_egim_col:
        egim_degeri = float(mahalle_satiri.iloc[0][found_egim_col])
    else:
        # Eğer hala %5 görüyorsan bil ki CSV dosyasında eşleşme yok demektir
        egim_degeri = 0.05 

    # Sol menüde eğimi göster (Mahalle değiştikçe bu rakamın değiştiğini görmelisin!)
    st.sidebar.metric("Mahalle Gerçek Eğimi", f"%{round(egim_degeri * 100, 1)}")
    # -----------------------------------------------------

    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 10.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    # 4. Analiz Butonu
    if st.button("Emisyon Analizini Çalıştır"):
        # Modelin beklediği 17 özelliği oluştur
        temel_ozellikler = [mesafe, 0, 1, egim_degeri * yuk, yuk, 0.5]
        
        # Mahalleleri modelin beklediği sıraya göre (alfabetik) 0/1 yapalım
        mahalle_ozellikleri = [1 if m == secilen_mahalle_search else 0 for m in orijinal_mahalleler]
        
        # Hepsini birleştir ve 17 tanesini al
        girdi_listesi = (temel_ozellikler + mahalle_ozellikleri)[:17]
        
        tahmin = model.predict(np.array([girdi_listesi]))[0]
        
        # GÖRSEL SONUÇLAR
        st.divider()
        st.balloons()
        st.header(f"📊 Tahmini Salınım: {round(tahmin, 2)} kg CO2")
        
        # Karşılaştırma Grafiği
        chart_data = pd.DataFrame({
            'Senaryo': ['Standart Rota', 'Yeşil Rota'],
            'CO2 (kg)': [tahmin, tahmin * 0.82]
        })
        st.bar_chart(data=chart_data, x='Senaryo', y='CO2 (kg)')
        st.success(f"📍 {secilen_mahalle_ham} mahallesi analizi başarıyla tamamlandı.")

except Exception as e:
    st.error(f"Sistem Hatası: {e}")
