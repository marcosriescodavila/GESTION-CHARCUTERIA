import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión Charcutería BI", layout="wide")

# Conexión optimizada
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60) # Esto hace que la app sea mucho más rápida
def load_data():
    # Cargamos solo lo necesario
    df = conn.read(worksheet="COSTES")
    # Limpieza rápida de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    # Buscamos la columna del nombre
    col_n = next((c for c in df.columns if 'NOMBRE' in c or 'ARTICULO' in c), None)
    if col_n:
        # Quitamos filas vacías de golpe
        df = df.dropna(subset=[col_n])
        df = df[df[col_n].str.strip() != ""]
    return df, col_n

try:
    df_c, col_nombre = load_data()

    st.title("🧀 Control de Márgenes")

    if col_nombre:
        opciones = sorted(df_c[col_nombre].unique())
        art = st.selectbox("Elegir Producto:", ["--- Toca aquí para buscar ---"] + opciones)

        if art != "--- Toca aquí para buscar ---":
            datos = df_c[df_c[col_nombre] == art].iloc[0]

            # Función ultra-rápida para números
            def n(key):
                c = next((col for col in df_c.columns if key in col), None)
                if c:
                    v = str(datos[c]).replace(',', '.').replace('€', '').strip()
                    try: return float(v)
                    except: return 0.0
                return 0.0

            c1, c2, c3 = st.columns(3)
            c1.metric("Coste Real", f"{n('REAL'):.2f} €")
            c2.metric("PVP Tienda", f"{n('TIENDA'):.2f} €")
            
            sup = n('SUPERAVIT')
            c3.metric("Superávit", f"{sup:.2f} €", delta=f"{sup:.2f}", delta_color="normal" if sup >=0 else "inverse")

            # Cálculo de margen
            p_tienda = n('TIENDA')
            c_real = n('REAL')
            if p_tienda > 0:
                margen = ((p_tienda - c_real) / p_tienda) * 100
                st.info(f"Margen actual: **{margen:.1f}%**")
    
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error("Conectando con el Excel...")
    st.stop()
    
