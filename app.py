import streamlit as st
import pandas as pd
import joblib
import numpy as np
import folium
from streamlit_folium import st_folium
import openrouteservice

st.set_page_config(page_title="Bilecik Yeşil Lojistik", layout="wide")
st.title("🍀 Toyota Teknik Projeler: Yeşil Rota Karar Destek Sistemi")
st.markdown("---")

ORS_API_KEY = st.secrets["ors"]["api_key"]
ors_client = openrouteservice.Client(key=ORS_API_KEY)

@st.cache_resource
def load_assets():
    model = joblib.load('bilecik_emisyon_model.pkl')
    data = pd.read_csv('bilecik_mahalle_verileri.csv')
    return model, data

model, mahalle_df = load_assets()

st.sidebar.header("🚚 Taşıma Parametreleri")
arac_secimi = st.sidebar.selectbox("Araç Tipi", ["Hafif Kamyonet", "Orta Kamyon", "Ağır TIR"])
yuk = st.sidebar.slider("Yük Miktarı (Ton)", 0.0, 30.0, 5.0)

arac_map = {"Hafif Kamyonet": 1, "Orta Kamyon": 2, "Ağır TIR": 3}

col1, col2 = st.columns(2)
with col1:
    st.subheader("📍 Rota Belirleme")
    baslangic = st.selectbox("Başlangıç Noktası", mahalle_df['mahalle'].unique())
    varis     = st.selectbox("Varış Noktası",     mahalle_df['mahalle'].unique())
    mesafe    = st.number_input("Tahmini Mesafe (km)", min_value=0.1, value=5.0)

def hesapla_co2(mesafe_km, arac_tipi_str, yuk_ton, mahalle_bilgisi):
    # Modelin beklediği 17 özellik (sıra önemli):
    # yol_egimi, trafik_yogunlugu, yuk_durumu, mesafe_km, arac_tipi,
    # arac_yasi, hiz_kmh, karbon_katsayi, ticaret_yogunlugu, ulasim_skoru,
    # yesil_alan_skoru, egim_x_yuk, trafik_x_hiz, hiz_sapma_optimal,
    # agir_arac, mahalle_trafik, sehir_ici

    yol_egimi        = mahalle_bilgisi['karbon_katsayi']
    trafik_yogunlugu = mahalle_bilgisi.get('ticaret_yogunlugu', 0.5)
    yuk_durumu       = min(yuk_ton / 30.0, 1.0)
    arac_tipi        = arac_map[arac_tipi_str]
    arac_yasi        = 5       # varsayılan ortalama
    hiz_kmh          = 60      # şehir içi ortalama
    karbon_katsayi   = mahalle_bilgisi['karbon_katsayi']
    ticaret_yogunlugu= mahalle_bilgisi.get('ticaret_yogunlugu', 0.5)
    ulasim_skoru     = mahalle_bilgisi.get('ulasim_skoru', 0.5)
    yesil_alan_skoru = mahalle_bilgisi.get('yesil_alan_skoru', 0.5)
    egim_x_yuk       = yol_egimi * yuk_ton
    trafik_x_hiz     = trafik_yogunlugu * hiz_kmh
    hiz_sapma_optimal= abs(hiz_kmh - 80)
    agir_arac        = 1 if arac_tipi_str == "Ağır TIR" else 0
    mahalle_trafik   = yol_egimi * trafik_yogunlugu
    sehir_ici        = 1

    girdi = np.array([[
        yol_egimi, trafik_yogunlugu, yuk_durumu, mesafe_km, arac_tipi,
        arac_yasi, hiz_kmh, karbon_katsayi, ticaret_yogunlugu, ulasim_skoru,
        yesil_alan_skoru, egim_x_yuk, trafik_x_hiz, hiz_sapma_optimal,
        agir_arac, mahalle_trafik, sehir_ici
    ]])
    return model.predict(girdi)[0]

ROTA_ETIKETLERI = ["En Az Emisyon 🌿", "Orta Emisyon 🟡", "En Fazla Emisyon 🔴"]

def co2_rengi(co2_degeri, min_co2, max_co2):
    if max_co2 == min_co2:
        return "green"
    oran = (co2_degeri - min_co2) / (max_co2 - min_co2)
    if oran < 0.4:
        return "green"
    elif oran < 0.7:
        return "orange"
    return "red"

if st.button("🚀 Emisyon Analizini Çalıştır"):

    mahalle_bilgisi = mahalle_df[mahalle_df['mahalle'] == baslangic].iloc[0]
    varis_bilgisi   = mahalle_df[mahalle_df['mahalle'] == varis].iloc[0]

    st.markdown("---")

    tahmin = hesapla_co2(mesafe, arac_secimi, yuk, mahalle_bilgisi)

    res1, res2 = st.columns(2)
    with res1:
        st.metric(label="Tahmini Karbon Salınımı", value=f"{round(tahmin, 2)} kg CO2")
        st.info(f"Seçilen Mahalle: {baslangic} | Karbon Katsayısı: {mahalle_bilgisi['karbon_katsayi']}")
    with res2:
        st.write("📊 Rota Verimlilik Analizi")
        chart_data = pd.DataFrame({
            'Senaryo': ['Senin Rotan', 'Toyota Yeşil Hedef'],
            'Emisyon': [tahmin, tahmin * 0.85]
        })
        st.bar_chart(chart_data, x='Senaryo', y='Emisyon', color='#2ecc71')

    st.markdown("---")
    st.subheader("🗺️ Yeşil Rota Haritası")
    st.caption("Alternatif rotalar emisyon değerine göre: 🟢 Az · 🟡 Orta · 🔴 Fazla")

    try:
        bas_koord = (mahalle_bilgisi['lon'], mahalle_bilgisi['lat'])
        var_koord = (varis_bilgisi['lon'],   varis_bilgisi['lat'])

        with st.spinner("Alternatif rotalar hesaplanıyor..."):
            yanit = ors_client.directions(
                coordinates=[bas_koord, var_koord],
                profile='driving-car',
                format='geojson',
                alternative_routes={"share_factor": 0.6, "target_count": 3}
            )

        rotalar = yanit['features']

        merkez_lat = (mahalle_bilgisi['lat'] + varis_bilgisi['lat']) / 2
        merkez_lon = (mahalle_bilgisi['lon'] + varis_bilgisi['lon']) / 2
        harita = folium.Map(location=[merkez_lat, merkez_lon], zoom_start=13,
                            tiles="OpenStreetMap")

        rota_co2_listesi = []
        for rota in rotalar:
            km  = rota['properties']['summary']['distance'] / 1000
            co2 = hesapla_co2(km, arac_secimi, yuk, mahalle_bilgisi)
            rota_co2_listesi.append((rota, km, co2))

        rota_co2_listesi.sort(key=lambda x: x[2])
        min_co2 = rota_co2_listesi[0][2]
        max_co2 = rota_co2_listesi[-1][2]

        for sira, (rota, km, co2) in enumerate(rota_co2_listesi):
            koordinatlar = [(p[1], p[0]) for p in rota['geometry']['coordinates']]
            renk  = co2_rengi(co2, min_co2, max_co2)
            kalin = 7 if sira == 0 else 4
            popup_html = f"""
            <div style="font-family:sans-serif;min-width:160px">
                <b>{ROTA_ETIKETLERI[min(sira,2)]}</b><br>
                🛣️ Mesafe: <b>{km:.1f} km</b><br>
                💨 CO₂: <b>{co2:.2f} kg</b><br>
                {"⭐ <b>Önerilen rota</b>" if sira == 0 else ""}
            </div>"""
            folium.PolyLine(
                koordinatlar, color=renk, weight=kalin, opacity=0.85,
                tooltip=f"Rota {sira+1}: {co2:.1f} kg CO₂",
                popup=folium.Popup(popup_html, max_width=220)
            ).add_to(harita)

        folium.Marker(
            [mahalle_bilgisi['lat'], mahalle_bilgisi['lon']],
            tooltip=f"🟢 Başlangıç: {baslangic}",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(harita)
        folium.Marker(
            [varis_bilgisi['lat'], varis_bilgisi['lon']],
            tooltip=f"🔴 Varış: {varis}",
            icon=folium.Icon(color='red', icon='flag', prefix='fa')
        ).add_to(harita)

        st_folium(harita, width=None, height=500, returned_objects=[])

        st.subheader("📋 Rota Karşılaştırması")
        tablo_verisi = []
        for sira, (rota, km, co2) in enumerate(rota_co2_listesi):
            sure_dk  = rota['properties']['summary']['duration'] / 60
            tasarruf = rota_co2_listesi[-1][2] - co2
            tablo_verisi.append({
                "Sıra"         : f"Rota {sira+1}",
                "Durum"        : ROTA_ETIKETLERI[min(sira, 2)],
                "Mesafe (km)"  : f"{km:.1f}",
                "Süre (dk)"    : f"{sure_dk:.0f}",
                "CO₂ (kg)"     : f"{co2:.2f}",
                "Tasarruf (kg)": f"{tasarruf:.2f}" if tasarruf > 0 else "—"
            })

        st.dataframe(pd.DataFrame(tablo_verisi), use_container_width=True, hide_index=True)

        en_iyi_km  = rota_co2_listesi[0][1]
        en_iyi_co2 = rota_co2_listesi[0][2]
        tasarruf   = rota_co2_listesi[-1][2] - en_iyi_co2
        st.success(
            f"✅ Önerilen rota **{en_iyi_km:.1f} km** uzunluğunda, "
            f"**{en_iyi_co2:.2f} kg CO₂** üretiyor. "
            f"En kötü rotaya göre **{tasarruf:.2f} kg** daha az emisyon!"
        )

    except openrouteservice.exceptions.ApiError as hata:
        st.error(f"ORS API hatası: {hata}")
    except KeyError as e:
        st.warning(f"CSV'de eksik sütun: {e}")

st.sidebar.markdown("---")
st.sidebar.write("Bilecik BİLSEM - 2026")
