import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="COVID-19 Vizualizáció", layout="wide")

# --- OLDALSÁV: ADATFORRÁS ---
st.sidebar.title("⚙️ Beállítások")
mode = st.sidebar.radio("Válassz adatforrást:", ["Szimulált adatok", "Google Sheets (Élő adatok)"])

# Google Sheets URL (a megadott táblázat CSV export linkje)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1e4VEZL1xvsALoOIq9V2SQuICeQrT5MtWfBm32ad7i8Q/export?format=csv&gid=311133316"

# Oszlopok kulcsszavai a beazonosításhoz
mapping = {
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
            # 0-k cseréje NaN-ra, hogy az interpolate felismerje őket
            df_res[col] = df_res[col].replace(0, np.nan)
            # Átlagolás az előtte és utána lévő értékből
            df_res[col] = df_res[col].interpolate(method='linear', limit_direction='both')
            # Maradék üres helyek feltöltése és típuskonverzió
            df_res[col] = df_res[col].fillna(0).astype(int)
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
    # Véletlen nullák elhelyezése a teszthez
    for c in df.columns[1:]:
        df.loc[np.random.choice(df.index, 10), c] = 0
    st.sidebar.success("Szimulációs üzemmód aktív")

else:
    try:
        # Adatok beolvasása közvetlenül a Google Sheets-ből
        raw_df = pd.read_csv(SHEET_URL)
        
        # Releváns oszlopok keresése
        found_cols = {}
        if 'Dátum' in raw_df.columns:
            found_cols['Dátum'] = 'Dátum'
        
        for col in raw_df.columns:
            col_str = str(col).lower()
            for key, friendly_name in mapping.items():
                if key in col_str:
                    found_cols[col] = friendly_name
        
        if len(found_cols) > 1:
            df = raw_df[list(found_cols.keys())].rename(columns=found_cols)
            df['Dátum'] = pd.to_datetime(df['Dátum'], errors='coerce')
            df = df.dropna(subset=['Dátum']).sort_values('Dátum')
            st.sidebar.success("Adatok sikeresen betöltve a Google Sheets-ből!")
        else:
            st.error("Nem találhatók a kért oszlopok a táblázatban.")
    except Exception as e:
        st.error(f"Hiba a Google Sheets elérésekor: {e}")

# --- MEGJELENÍTÉS ---
if df is not None:
    st.title(f"📊 COVID-19 Adatvizualizáció ({mode})")
    
    numeric_cols = [c for c in df.columns if c != 'Dátum']
    
    if numeric_cols:
        # Simítás elvégzése
        df_final = clean_and_interpolate(df, numeric_cols)
        
        # Interaktív választó
        selected_col = st.selectbox("Válassz egy kategóriát az ábrázoláshoz:", numeric_cols)
        
        # Grafikon készítése
        fig = px.line(df_final, x='Dátum', y=selected_col, 
                      title=f"{selected_col} időbeli alakulása (Simított görbe)",
                      markers=True, template="plotly_white")
        
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        if st.checkbox("Nyers adatok mutatása"):
            st.dataframe(df_final)
