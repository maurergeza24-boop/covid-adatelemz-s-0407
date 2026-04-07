import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="COVID-19 Precíz Vizualizáció", layout="wide")

# --- OLDALSÁV ---
st.sidebar.title("⚙️ Beállítások")
mode = st.sidebar.radio("Válassz adatforrást:", ["Szimulált adatok", "Google Sheets (Élő adatok)"])

# A Google Sheet CSV export linkje
SHEET_URL = "https://docs.google.com/spreadsheets/d/1e4VEZL1xvsALoOIq9V2SQuICeQrT5MtWfBm32ad7i8Q/export?format=csv&gid=311133316"

# PONTOS kulcsszavak a napi adatokhoz (hogy elkerüljük az összesített adatokat)
mapping_rules = {
    "Az új elhunytak száma naponta": "Napi elhunytak",
    "Új gyógyultak naponta": "Napi gyógyultak",
    "Kórházi ápoltak száma": "Kórházi ápoltak",
    "Lélegeztetőgépen lévők száma": "Lélegeztetőgépen"
}

def clean_and_interpolate(df, columns):
    """0-k helyett átlagolás (lineáris interpoláció) a kért simításhoz"""
    df_res = df.copy()
    for col in columns:
        if pd.api.types.is_numeric_dtype(df_res[col]):
            # A 0-kat NaN-ra cseréljük, hogy az interpoláció működjön
            df_res[col] = df_res[col].replace(0, np.nan)
            # Lineáris interpoláció (előtte-utána átlaga)
            df_res[col] = df_res[col].interpolate(method='linear', limit_direction='both')
            # Kerekítés és visszaalakítás egésszé
            df_res[col] = df_res[col].fillna(0).round().astype(int)
    return df_res

# --- ADATBETÖLTÉS ---
df = None

if mode == "Szimulált adatok":
    dates = pd.date_range(start="2022-01-01", periods=150)
    df = pd.DataFrame({
        'Dátum': dates,
        'Napi elhunytak': np.random.randint(0, 30, 150),
        'Napi gyógyultak': np.random.randint(50, 400, 150),
        'Kórházi ápoltak': np.random.randint(400, 2000, 150),
        'Lélegeztetőgépen': np.random.randint(10, 100, 150)
    })
    st.sidebar.success("Szimulációs üzemmód aktív")

else:
    try:
        # Adatok beolvasása a Google Sheets-ből
        raw_df = pd.read_csv(SHEET_URL)
        
        # Oszlopok keresése és szűrése
        selected_cols = {}
        
        # Dátum keresése
        if 'Dátum' in raw_df.columns:
            selected_cols['Dátum'] = 'Dátum'
        
        # A megadott 4 pontos oszlopnév keresése
        for original_name, friendly_name in mapping_rules.items():
            if original_name in raw_df.columns:
                selected_cols[original_name] = friendly_name
        
        if len(selected_cols) > 1:
            df = raw_df[list(selected_cols.keys())].copy()
            df.columns = [selected_cols[c] for c in df.columns]
            
            # Dátum konvertálása és rendezése
            df['Dátum'] = pd.to_datetime(df['Dátum'], errors='coerce')
            df = df.dropna(subset=['Dátum']).sort_values('Dátum')
            
            # Számmá alakítás (tisztítás a szöveges elemektől, ha lennének)
            for col in mapping_rules.values():
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            st.sidebar.success("Élő adatok betöltve!")
        else:
            st.error("Nem találhatók a pontos oszlopnevek a táblázatban!")
            
    except Exception as e:
        st.error(f"Hiba történt: {e}")

# --- MEGJELENÍTÉS ---
if df is not None:
    st.title(f"📊 Vizualizáció ({mode})")
    
    numeric_options = [c for c in df.columns if c != 'Dátum']
    
    if numeric_options:
        # Simítás alkalmazása (0-k kezelése)
        df_final = clean_and_interpolate(df, numeric_options)
        
        selected_col = st.selectbox("Válassz szempontot:", numeric_options)
        
        # Grafikon rajzolása
        fig = px.line(df_final, x='Dátum', y=selected_col, 
                      title=f"{selected_col} napi alakulása (Simított görbe)",
                      markers=True, 
                      template="plotly_white",
                      color_discrete_sequence=['#1f77b4'])
        
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        # Ellenőrzés gyanánt a legfrissebb érték
        latest_val = df_final[selected_col].iloc[-1]
        st.metric(label=f"Utolsó ismert érték ({selected_col})", value=int(latest_val))
        
        if st.checkbox("Adattáblázat megjelenítése"):
            st.dataframe(df_final)
    else:
        st.warning("Nincs megjeleníthető adat.")
