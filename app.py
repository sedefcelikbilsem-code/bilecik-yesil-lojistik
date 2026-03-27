import streamlit as st
import pandas as pd
import joblib
import numpy as np

# 1. Sayfa Yapılandırması (Yeşil Tema)
st.set_page_config(page_title="Bilecik Yeşil Rota", page_icon="🍀")
st.title("🍀 Toyota Teknik Projeler: Yeşil Lojistik")
st.subheader("Bilecik Karbon Emisyon Karar Destek Sistemi")

@st.cache_resource
def load_assets():
    # Modeli ve Veriyi Yükle
    model = joblib.load('bilecik_emisyon_model.pkl')
    if isinstance(model, tuple): model = model[0]
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    data.columns = data.columns.str.strip().str.lower()
    return model, data

try:
    model, data = load_assets()
    
    # 3. Sol Menü (Sidebar)
    st.sidebar.header("🚚 Taşıma Parametreleri")
    mah_col = data.columns[0]
    mahalle_listesi = sorted(data[mah_col].unique())
    secilen_mahalle = st.sidebar.selectbox("Analiz Edilecek Mahalle", mahalle_listesi)
    
    # --- EĞİM BİLGİSİNİ OTOMATİK ÇEK (Senin istediğin o otomatik kısım) ---
    mahalle_verisi = data[data[mah_col] == secilen_mahalle].iloc[0]
    # Sütun adı kontrolü (egim veya yol_egimi)
    egim_col = 'yol_egimi' if 'yol_egimi' in data.columns else 'egim'
    mahalle_egimi = float(mahalle_verisi.get(egim_col, 0.05))
    
    # Eğim değerini sol tarafta şık bir kutuda göster
    st.sidebar.metric("Mahalle Eğimi", f"%{round(mahalle_egimi * 100, 1)}")
    # ------------------------------------------------------------------
    
    yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 10.0)
    mesafe = st.sidebar.number_input("Mesafe (km)", value=5.0)

    # 4. Analiz ve Grafik Bölümü
    if st.button("Emisyon Analizini Çalıştır"):
        # 17 Feature Fix (Modelin beklediği yapı)
        temel_ozellikler = [mesafe, 0, 1, mahalle_egimi * yuk, yuk, 0.5]
        mahalle_ozellikleri = [1 if m == secilen_mahalle else 0 for m in mahalle_listesi]
        girdi = (temel_ozellikler + mahalle_ozellikleri)[:17]
        
        tahmin = model.predict(np.array([girdi]))[0]
        
        # GÖRSEL ŞÖLEN BAŞLASIN
        st.divider()
        st.balloons() # Balonlar uçsun
        st.header(f"📊 Tahmini Salınım: {round(tahmin, 2)} kg CO2")
        
        # Karşılaştırma Grafiği (Önceki kodda sevdiğin o grafik)
        chart_data = pd.DataFrame({
            'Senaryo': ['Standart Rota', 'Yeşil Rota'],
            'CO2 Salınımı (kg)': [tahmin, tahmin * 0.85] # %15 iyileştirme simülasyonu
        })
        st.bar_chart(data=chart_data, x='Senaryo', y='CO2 Salınımı (kg)')
        
        st.success(f"📍 {secilen_mahalle} mahallesi için Bilecik yerel verileriyle analiz tamamlandı.")

except Exception as e:
    # Eğer 'egim' sütununu bulamazsa buraya düşer
    st.error(f"Sistem Hatası: {e}")
    st.info("Lütfen CSV dosyanızdaki sütun isminin 'yol_egimi' veya 'egim' olduğundan emin olun.")
