import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="COVID-19 Magyarország", layout="wide")

st.title("🦠 Koronavírus Adatvizualizáció")

# Oszlopok megfeleltetése a csatolt fájl alapján
column_map = {
    'Az új elhunytak száma naponta': 'Új elhunytak',
    'Új gyógyultak naponta': 'Új gyógyultak',
    'Kórházi ápoltak száma': 'Kórházi ápoltak',
    'Lélegeztetőgépen lévők száma': 'Lélegeztetőgépen'
}

# Fájl beolvasása (Streamlit feltöltő vagy helyi fájl)
uploaded_file = st.sidebar.file_uploader("Válaszd ki a korona_hun.xlsx-et vagy a CSV-t", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Beolvasás (ha CSV, akkor read_csv, ha Excel, akkor read_excel)
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Dátum konvertálása
    df['Dátum'] = pd.to_datetime(df['Dátum'])
    
    # Csak a releváns oszlopok megtartása
    available_cols = [col for col in column_map.keys() if col in df.columns]
    plot_df = df[['Dátum'] + available_cols].copy()

    # --- ADATSIMÍTÁS (A kért logika: 0 értékek helyett átlagolás) ---
    for col in available_cols:
        # A 0 értékek ideiglenes cseréje NaN-ra a számoláshoz
        plot_df[col] = plot_df[col].replace(0, np.nan)
        # Lineáris interpoláció (előtte-utána átlaga)
        plot_df[col] = plot_df[col].interpolate(method='linear', limit_direction='both')
        # Visszaalakítás kerekített számokká
        plot_df[col] = plot_df[col].fillna(0).astype(int)

    # Megjelenítés
    selected_display_name = st.selectbox("Válassz szempontot:", [column_map[c] for c in available_cols])
    
    # Visszakeressük az eredeti oszlopnevet a megjelenített név alapján
    actual_col = [k for k, v in column_map.items() if v == selected_display_name][0]

    fig = px.line(plot_df, x='Dátum', y=actual_col, title=f"{selected_display_name} idősoros alakulása")
    st.plotly_chart(fig, use_container_width=True)
    
    st.success("Adatsimítás (nullák átlagolása) elvégezve.")
else:
    st.info("Kérlek töltsd fel a fájlt a bal oldali menüben a kezdéshez.")
