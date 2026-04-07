import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="COVID-19 Vizualizáció", layout="wide")

# --- OLDALSÁV: ADATFORRÁS ÉS BEÁLLÍTÁSOK ---
st.sidebar.title("⚙️ Beállítások")
mode = st.sidebar.radio("Válassz adatforrást:", ["Szimulált adatok", "Saját fájl feltöltése"])

# Keresett kulcsszavak az oszlopok beazonosításához
mapping = {
    "elhunyt": "Új elhunytak száma",
    "gyógyult": "Új gyógyultak száma",
    "kórház": "Kórházi ápoltak száma",
    "lélegeztető": "Lélegeztetőgépen lévők"
}

def clean_and_interpolate(df, columns):
    """Végrehajtja a kért simítást: 0-k helyett átlagolás"""
    df_res = df.copy()
    for col in columns:
        # Csak ha az oszlop numerikus
        if pd.api.types.is_numeric_dtype(df_res[col]):
            df_res[col] = df_res[col].replace(0, np.nan)
            df_res[col] = df_res[col].interpolate(method='linear', limit_direction='both')
            df_res[col] = df_res[col].fillna(0).astype(int)
    return df_res

# --- ADATBETÖLTÉS ---
df = None

if mode == "Szimulált adatok":
    # Teljesen különálló szimulációs blokk
    dates = pd.date_range(start="2022-01-01", periods=150)
    df = pd.DataFrame({
        'Dátum': dates,
        'Új elhunytak száma': np.random.randint(0, 30, 150),
        'Új gyógyultak száma': np.random.randint(50, 400, 150),
        'Kórházi ápoltak száma': np.random.randint(400, 2000, 150),
        'Lélegeztetőgépen lévők': np.random.randint(10, 100, 150)
    })
    # Szándékos nullák a teszthez
    for c in df.columns[1:]:
        df.loc[np.random.choice(df.index, 8), c] = 0
    st.sidebar.success("Szimulációs üzemmód aktív")

else:
    uploaded_file = st.sidebar.file_uploader("Töltsd fel az Excel vagy CSV fájlt", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                temp_df = pd.read_csv(uploaded_file)
            else:
                temp_df = pd.read_excel(uploaded_file)
            
            # --- OSZLOPKERESÉS (Hibajavítással) ---
            found_cols = {}
            if 'Dátum' in temp_df.columns:
                found_cols['Dátum'] = 'Dátum'
            
            for col in temp_df.columns:
                # KIKÜSZÖBÖLJÜK AZ ATTRIBUTERROR-T: stringgé alakítjuk az oszlopnevet
                col_str = str(col).lower()
                for key, friendly_name in mapping.items():
                    if key in col_str:
                        found_cols[col] = friendly_name
            
            if len(found_cols) > 1:
                df = temp_df[list(found_cols.keys())].rename(columns=found_cols)
                df['Dátum'] = pd.to_datetime(df['Dátum'], errors='coerce')
                df = df.dropna(subset=['Dátum'])
            else:
                st.error("Nem találtam megfelelő oszlopokat a fájlban (Dátum, Elhunyt, stb.)")
        except Exception as e:
            st.error(f"Hiba történt a fájl feldolgozásakor: {e}")

# --- MEGJELENÍTÉS ---
if df is not None:
    st.title(f"📊 Adatvizualizáció ({mode})")
    
    numeric_cols = [c for c in df.columns if c != 'Dátum']
    
    if not numeric_cols:
        st.warning("Nincsenek megjeleníthető számszerű adatok.")
    else:
        # Adatsimítás alkalmazása
        df_final = clean_and_interpolate(df, numeric_cols)
        
        selected_col = st.selectbox("Válassz egy kategóriát:", numeric_cols)
        
        # Grafikon rajzolása
        fig = px.line(df_final, x='Dátum', y=selected_col, 
                      title=f"{selected_col} időbeli alakulása (0-érték simítással)",
                      markers=True, template="plotly_white",
                      color_discrete_sequence=['#E63946'])
        
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        if st.checkbox("Táblázat megtekintése"):
            st.dataframe(df_final)
else:
    if mode == "Saját fájl feltöltése":
        st.info("ℹ️ Kérlek, töltsd fel a fájlt a bal oldali menüben!")
