import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Charcutería BI", layout="wide")

st.title("🧀 BI Charcutería")

try:
    # Conexión directa
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Intentamos leer solo la pestaña COSTES
    df = conn.read(worksheet="COSTES", ttl=300)
    
    if df is not None:
        # Limpieza de nombres
        df.columns = [str(c).strip().upper() for c in df.columns]
        col_n = next((c for c in df.columns if 'NOMBRE' in c or 'ARTICULO' in c), None)
        
        if col_n:
            df = df.dropna(subset=[col_n])
            opciones = sorted([str(x) for x in df[col_n].unique() if str(x) != 'nan'])
            
            art = st.selectbox("🔍 Selecciona un producto:", ["--- Toca para buscar ---"] + opciones)
            
            if art != "--- Toca para buscar ---":
                datos = df[df[col_n] == art].iloc[0]
                
                # Función de extracción limpia
                def get_v(key):
                    c = next((col for col in df.columns if key in col), None)
                    if c:
                        try:
                            v = str(datos[c]).replace('€','').replace(',','.').strip()
                            return float(v)
                        except: return 0.0
                    return 0.0

                c1, c2, c3 = st.columns(3)
                real = get_v('REAL')
                tienda = get_v('TIENDA')
                sup = get_v('SUPERAVIT')
                
                c1.metric("COSTE REAL", f"{real:.2f} €")
                c2.metric("PVP TIENDA", f"{tienda:.2f} €")
                c3.metric("SUPERÁVIT", f"{sup:.2f} €", delta=f"{sup:.2f}", delta_color="normal" if sup>=0 else "inverse")
        else:
            st.error("No encuentro la columna 'NOMBRE ARTICULO'. Revisa el Excel.")
            st.write("Columnas leídas:", list(df.columns))

except Exception as e:
    st.error("⚠️ Error de Conexión")
    st.info("Asegúrate de haber pegado el enlace del Excel en los 'Secrets' de Streamlit.")
    st.write("Detalle para soporte:", str(e))
