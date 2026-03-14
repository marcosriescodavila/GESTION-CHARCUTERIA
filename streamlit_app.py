import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión Charcutería", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# Función de carga ultra-ligera
@st.cache_data(ttl=300)
def load_data():
    # Leemos la hoja COSTES
    df = conn.read(worksheet="COSTES")
    
    # Forzamos limpieza de nombres de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Buscamos la columna del nombre del producto
    col_n = next((c for c in df.columns if 'NOMBRE' in c or 'ARTICULO' in c), None)
    
    if col_n:
        # Quitamos todas las filas donde el nombre esté vacío
        df = df.dropna(subset=[col_n])
        df = df[df[col_n].astype(str).str.strip() != ""]
        # Nos quedamos solo con las columnas que realmente tienen datos para no saturar
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
    
    return df, col_n

try:
    df_c, col_nombre = load_data()

    st.title("🧀 BI Charcutería")

    if col_nombre:
        # Creamos la lista de productos
        opciones = sorted([str(x) for x in df_c[col_nombre].unique()])
        
        art = st.selectbox("🔍 Selecciona un producto:", ["--- Toca para desplegar ---"] + opciones)

        if art != "--- Toca para desplegar ---":
            # Extraemos la fila del producto
            datos = df_c[df_c[col_nombre] == art].iloc[0]

            # Función para limpiar números de cualquier formato (moneda, comas, etc)
            def clean_val(key_word):
                col = next((c for c in df_c.columns if key_word in c), None)
                if col:
                    v = str(datos[col]).replace('€', '').replace('%', '').replace(',', '.').strip()
                    try: return float(v)
                    except: return 0.0
                return 0.0

            # Panel de métricas principales
            m1, m2, m3 = st.columns(3)
            
            c_real = clean_val('REAL')
            p_tienda = clean_val('TIENDA')
            sup = clean_val('SUPERAVIT')
            
            m1.metric("COSTE REAL", f"{c_real:.2f} €")
            m2.metric("PVP TIENDA", f"{p_tienda:.2f} €")
            
            # Color del superávit: verde si es positivo, rojo si es negativo
            m3.metric("SUPERÁVIT", f"{sup:.2f} €", delta=f"{sup:.2f} €", 
                      delta_color="normal" if sup >= 0 else "inverse")

            st.markdown("---")
            
            # Cálculo de Margen Porcentual
            if p_tienda > 0:
                margen = ((p_tienda - c_real) / p_tienda) * 100
                if margen < 30:
                    st.warning(f"⚠️ Margen actual: **{margen:.1f}%** (Por debajo del 30% objetivo)")
                else:
                    st.success(f"✅ Margen actual: **{margen:.1f}%** (Objetivo cumplido)")
    
    # Botón pequeño de refresco al final
    if st.button("🔄 Refrescar datos del Excel"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.warning("Conectando con la base de datos de Google... Por favor, espera.")
    st.stop()
    
