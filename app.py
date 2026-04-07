import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="COVID-19 Vizualizáció", layout="wide")

# --- OLDALSÁV ---
st.sidebar.title("Beállítások")
mode = st.sidebar.radio("Adatforrás:", ["Szimulált adatok", "Excel/CSV feltöltése"])

# Keresett kulcsszavak az oszlopnevekben
mapping = {
    "elhunyt": "Új elhunytak száma",
    "gyógyult": "Új gyógyultak száma",
    "kórház": "Kórházi ápoltak száma",
    "lélegeztető": "Lélegeztetőgépen lévők"
}

def load_data():
    if mode == "Szimulált adatok":
        # 100 napos tesztadat generálása
        dates = pd.date_range(start="2022-01-01", periods=100)
        data = pd.DataFrame({
            'Dátum': dates,
            'Új elhunytak száma': np.random.randint(0, 40, 100),
            'Új gyógyultak száma': np.random.randint(100, 500, 100),
            'Kórházi ápoltak száma': np.random.randint(500, 2500, 100),
            'Lélegeztetőgépen lévők': np.random.randint(20, 150, 100)
        })
        # Néhány véletlenszerű nulla a simítás teszteléséhez
        for col in data.columns[1:]:
            data.loc[np.random.choice(data.index, 5), col] = 0
        return data
    
    else:
        file = st.sidebar.file_uploader("Töltsd fel a fájlt", type=["xlsx", "csv"])
        if file is not None:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            
            # Dátum oszlop keresése és rendbetétele
            if 'Dátum' in df.columns:
                df['Dátum'] = pd.to_datetime(df['Dátum'])
            
            # Oszlopok intelligens párosítása
            new_columns = {'Dátum': 'Dátum'}
            for original_col in df.columns:
                lower_col = original_col.lower()
                for key, friendly_name in mapping.items():
                    if key in lower_col:
                        new_columns[original_col] = friendly_name
            
            df = df[list(new_columns.keys())].rename(columns=new_columns)
            return df
        return None

df = load_data()

if df is not None:
    st.title(f"📊 Vizualizáció: {mode}")
    
    # Csak a numerikus oszlopok (kivéve Dátum)
    numeric_cols = [c for c in df.columns if c != 'Dátum']
    
    # --- ADATSIMÍTÁS LOGIKA ---
    # 0 értékek cseréje NaN-ra, majd interpoláció (átlagolás)
    df_clean = df.copy()
    for col in numeric_cols:
        df_clean[col] = df_clean[col].replace(0, np.nan)
        df_clean[col] = df_clean[col].interpolate(method='linear', limit_direction='both')
        df_clean[col] = df_clean[col].fillna(0).astype(int)

    # Megjelenítés
    selected_col = st.selectbox("Válassz szempontot a grafikonhoz:", numeric_cols)
    
    fig = px.line(df_clean, x='Dátum', y=selected_col, 
                  title=f"{selected_col} alakulása (simított görbe)",
                  markers=True, template="plotly_white")
    
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    if st.checkbox("Nyers adatok táblázata"):
        st.write(df_clean)
else:
    st.warning("Várjuk az adatokat... Válaszd a 'Szimulált adatok' módot vagy tölts fel egy fájlt!")
