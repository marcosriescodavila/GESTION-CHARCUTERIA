import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión Charcutería BI", page_icon="🧀", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Cargamos con ttl=0 para refresco inmediato
    df_c = conn.read(worksheet="COSTES", ttl=0)
    df_p = conn.read(worksheet="PROVEEDORES", ttl=0)
    
    # Limpiamos nombres de columnas: quitamos espacios y pasamos a mayúsculas
    df_c.columns = [str(c).strip().upper() for c in df_c.columns]
    df_p.columns = [str(c).strip().upper() for c in df_p.columns]
    
    # IMPORTANTE: Eliminamos filas que tengan el nombre del producto vacío
    # Buscamos la columna del nombre
    col_n = next((c for c in df_c.columns if 'NOMBRE' in c or 'ARTICULO' in c), None)
    if col_n:
        df_c = df_c.dropna(subset=[col_n])
        df_c = df_c[df_c[col_n] != '']
        
    return df_c, df_p, col_n

try:
    df_c, df_p, col_nombre = load_data()

    st.sidebar.title("Charcutería Control")
    menu = st.sidebar.radio("Navegación:", ["Escandallos", "Proveedores"])

    if menu == "Escandallos":
        st.header("⚖️ Análisis de Margen y Costes")
        
        # Filtramos para que solo aparezcan artículos reales
        lista_articulos = [a for a in df_c[col_nombre].unique() if str(a) != 'nan']
        art = st.selectbox("Selecciona un artículo:", lista_articulos)
        
        # Filtramos la fila del producto elegido
        d = df_c[df_c[col_nombre] == art].iloc[0]

        # Función para sacar números limpios (evita el error de la imagen)
        def clean_num(key):
            col = next((c for c in df_c.columns if key in c), None)
            if col:
                val = str(d[col]).replace(',', '.').replace('€', '').strip()
                try:
                    return float(val)
                except:
                    return 0.0
            return 0.0

        c_base = clean_num('COSTE BASE') or clean_num('PRECIO COSTE')
        c_real = clean_num('COSTE REAL')
        p_tienda = clean_num('PRECIO TIENDA')
        sup = clean_num('SUPERAVIT')

        c1, c2, c3 = st.columns(3)
        c1.metric("Coste Base", f"{c_base:,.2f} €")
        c2.metric("Coste Real", f"{c_real:,.2f} €")
        c3.metric("Precio Tienda", f"{p_tienda:,.2f} €")

        st.divider()

        if p_tienda > 0:
            margen = ((p_tienda - c_real) / p_tienda) * 100
            st.info(f"El margen real actual es del **{margen:.1f}%**")
        
        if sup < 0:
            st.error(f"⚠️ Alerta: Pierdes {abs(sup):.2f}€ respecto al objetivo.")
        else:
            st.success(f"✅ Superávit de {sup:.2f}€ sobre objetivo.")

    elif menu == "Proveedores":
        st.header("📞 Directorio")
        # Limpiamos filas vacías en proveedores también
        df_p_clean = df_p.dropna(how='all')
        st.dataframe(df_p_clean, use_container_width=True)

except Exception as e:
    st.error(f"Configurando conexión... Si ves esto, espera 5 segundos.")
    st.write(f"Nota técnica: {e}")
