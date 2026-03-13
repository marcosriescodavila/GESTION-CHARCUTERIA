import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión Charcutería BI", page_icon="🧀", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # 1. Cargamos las pestañas
    df_c = conn.read(worksheet="COSTES")
    df_p = conn.read(worksheet="PROVEEDORES")
    try:
        df_v = conn.read(worksheet="VENTAS")
    except:
        df_v = pd.DataFrame()
    
    # 2. Limpieza radical de nombres de columnas
    df_c.columns = [str(c).strip().upper() for c in df_c.columns]
    df_p.columns = [str(c).strip().upper() for c in df_p.columns]
    
    return df_c, df_p, df_v

try:
    df_c, df_p, df_v = load_data()
    
    # Buscamos la columna del nombre (por si acaso no es exactamente 'NOMBRE ARTICULO')
    col_nombre = [c for c in df_c.columns if 'NOMBRE' in c or 'ARTICULO' in c][0]
    
    # Limpiamos filas que no tengan nombre de producto
    df_c = df_c.dropna(subset=[col_nombre])

    st.sidebar.title("Charcutería Control")
    menu = st.sidebar.radio("Navegación:", ["Escandallos", "Proveedores", "Ventas"])

    if menu == "Escandallos":
        st.header("⚖️ Análisis de Margen y Costes")
        
        art = st.selectbox("Selecciona un artículo:", df_c[col_nombre].unique())
        d = df_c[df_c[col_nombre] == art].iloc[0]

        # Extraemos datos usando nombres flexibles
        def get_val(key):
            # Busca una columna que contenga la palabra clave
            cols = [c for c in df_c.columns if key in c]
            return d[cols[0]] if cols else 0

        coste_base = get_val('COSTE BASE') or get_val('PRECIO COSTE')
        coste_real = get_val('COSTE REAL')
        precio_tienda = get_val('PRECIO TIENDA')
        superavit = get_val('SUPERAVIT')

        c1, c2, c3 = st.columns(3)
        c1.metric("Coste Base", f"{float(coste_base):,.2f} €")
        c2.metric("Coste Real", f"{float(coste_real):,.2f} €")
        c3.metric("Precio Tienda", f"{float(precio_tienda):,.2f} €")

        st.divider()

        if float(precio_tienda) > 0:
            margen = ((float(precio_tienda) - float(coste_real)) / float(precio_tienda)) * 100
            st.info(f"El margen real actual es del **{margen:.1f}%**")
        
        if float(superavit) < 0:
            st.error(f"⚠️ Estás perdiendo {abs(float(superavit)):.2f}€ respecto al margen objetivo.")
        else:
            st.success(f"✅ Tienes un superávit de {float(superavit):.2f}€ sobre el objetivo.")

    elif menu == "Proveedores":
        st.header("📞 Directorio de Proveedores")
        st.dataframe(df_p, use_container_width=True)

    elif menu == "Ventas":
        st.header("📈 Rendimiento")
        if not df_v.empty:
            st.line_chart(df_v)
        else:
            st.warning("No hay datos en la pestaña VENTAS.")

except Exception as e:
    st.error(f"Error de lectura: {e}")
    st.write("Revisa que en el Excel la columna se llame NOMBRE ARTICULO.")
