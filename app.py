import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="COVID-19 Vizualizáció", layout="wide")

# --- OLDALSÁV ---
st.sidebar.title("⚙️ Beállítások")
mode = st.sidebar.radio("Válassz adatforrás megtekintéséhez:", ["Szimulált adatok", "Google Sheets (Élő adatok)"])

# A kért Google Sheet link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1e4VEZL1xvsALoOIq9V2SQuICeQrT5MtWfBm32ad7i8Q/export?format=csv&gid=311133316"

# Keresett kulcsszavak és a hozzájuk rendelt szép név
mapping_rules = {
    "elhunyt": "Új elhunytak száma",
    "gyógyult": "Új gyógyultak száma",
    "kórház": "Kórházi ápoltak száma",
    "lélegeztető": "Lélegeztetőgépen lévők"
}

def clean_and_interpolate(df, columns):
    """0-k helyett átlagolás (lineáris interpoláció)"""
    df_res = df.copy()
    for col in columns:
        if pd.api.types.is_numeric_dtype(df_res[col]):
            df_res[col] = df_res[col].replace(0, np.nan)
            df_res[col] = df_res[col].interpolate(method='linear', limit_direction='both')
            df_res[col] = df_res[col].fillna(0).round().astype(int)
    return df_res

# --- ADATBETÖLTÉS ---
df = None

if mode == "Szimulált adatok":
    dates = pd.date_range(start="2022-01-01", periods=150)
    df = pd.DataFrame({
        'Dátum': dates,
        'Új elhunytak száma': np.random.randint(0, 30, 150),
        'Új gyógyultak száma': np.random.randint(50, 400, 150),
        'Kórházi ápoltak száma': np.random.randint(400, 2000, 150),
        'Lélegeztetőgépen lévők': np.random.randint(10, 100, 150)
    })
    # Teszt nullák
    for c in df.columns[1:]:
        df.loc[np.random.choice(df.index, 10), c] = 0
    st.sidebar.success("Szimulációs üzemmód aktív")

else:
    try:
        # Adatok beolvasása
        raw_df = pd.read_csv(SHEET_URL)
        
        # Tisztított DataFrame összeállítása
        clean_cols = {}
        
        # 1. Dátum keresése
        date_col = next((c for c in raw_df.columns if 'dátum' in str(c).lower()), None)
        if date_col:
            clean_cols[date_col] = 'Dátum'
        
        # 2. A kért 4 szempont keresése (csak az első találatot vesszük mindegyikből)
        for key, friendly_name in mapping_rules.items():
            found = next((c for c in raw_df.columns if key in str(c).lower()), None)
            if found and found not in clean_cols:
                clean_cols[found] = friendly_name
        
        if len(clean_cols) > 1:
            # Csak a megtalált és egyedivé tett oszlopokat tartjuk meg
            df = raw_df[list(clean_cols.keys())].copy()
            df.columns = [clean_cols[c] for c in df.columns]
            
            # Dátum típus kényszerítése
            df['Dátum'] = pd.to_datetime(df['Dátum'], errors='coerce')
            df = df.dropna(subset=['Dátum']).sort_values('Dátum')
            
            st.sidebar.success("Adatok betöltve a Google Sheets-ből!")
        else:
            st.error("Nem találhatók a kért adatoszlopok a táblázatban.")
            
    except Exception as e:
        st.error(f"Hiba történt: {e}")

# --- MEGJELENÍTÉS ---
if df is not None:
    st.title(f"📊 Adatvizualizáció ({mode})")
    
    # Kizárjuk a Dátumot a választható listából
    numeric_options = [c for c in df.columns if c != 'Dátum']
    
    if numeric_options:
        # Adatsimítás alkalmazása (0-k kezelése)
        df_final = clean_and_interpolate(df, numeric_options)
        
        selected_col = st.selectbox("Válaszd ki a megjelenítendő adatot:", numeric_options)
        
        # Interaktív Plotly grafikon
        fig = px.line(df_final, x='Dátum', y=selected_col, 
                      title=f"{selected_col} alakulása (Interpolált adatokkal)",
                      markers=True, 
                      template="plotly_white",
                      color_discrete_sequence=['#1f77b4'])
        
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        if st.checkbox("Táblázatos nézet"):
            st.dataframe(df_final)
    else:
        st.warning("Nincs megjeleníthető numerikus adat.")
