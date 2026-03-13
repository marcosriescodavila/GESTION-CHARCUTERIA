import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión Charcutería BI", page_icon="🧀", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Cargamos las pestañas
    df_c = conn.read(worksheet="COSTES")
    df_p = conn.read(worksheet="PROVEEDORES")
    try:
        df_v = conn.read(worksheet="VENTAS")
    except:
        df_v = pd.DataFrame()
    
    # TRUCO MÁGICO: Limpiamos espacios raros en los nombres de las columnas
    df_c.columns = df_c.columns.str.strip()
    df_p.columns = df_p.columns.str.strip()
    if not df_v.empty:
        df_v.columns = df_v.columns.str.strip()
        
    return df_c, df_p, df_v

try:
    df_c, df_p, df_v = load_data()
    
    # Nombre de columna flexible para el buscador
    col_nombre = "NOMBRE ARTICULO"
    df_c = df_c.dropna(subset=[col_nombre])

    st.sidebar.title("Charcutería Control")
    menu = st.sidebar.radio("Navegación:", ["Escandallos", "Proveedores", "Ventas"])

    if menu == "Escandallos":
        st.header("⚖️ Análisis de Margen")
        
        art = st.selectbox("Selecciona un artículo:", df_c[col_nombre].unique())
        d = df_c[df_c[col_nombre] == art].iloc[0]

        # Usamos .get() para que si falta una columna no rompa la app
        coste_base = d.get('PRECIO COSTE', 0)
        coste_real = d.get('COSTE REAL CON MERMA E IMPUESTOS', 0)
        precio_tienda = d.get('PRECIO TIENDA', 0)
        superavit = d.get('SUPERAVIT', 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("Coste Base", f"{coste_base:.2f} €")
        c2.metric("Coste Real", f"{coste_real:.2f} €")
        c3.metric("Precio Tienda", f"{precio_tienda:.2f} €")

        # Cálculo de margen dinámico
        if precio_tienda > 0:
            margen = ((precio_tienda - coste_real) / precio_tienda) * 100
            st.info(f"El margen real de este producto es del **{margen:.1f}%**")
        
        if superavit < 0:
            st.error(f"⚠️ Estás perdiendo {abs(superavit):.2f}€ respecto al objetivo.")
        else:
            st.success(f"✅ Tienes un superávit de {superavit:.2f}€.")

    elif menu == "Proveedores":
        st.header("📞 Directorio")
        st.dataframe(df_p, use_container_width=True)

    elif menu == "Ventas":
        st.header("📈 Rendimiento")
        if not df_v.empty:
            st.line_chart(df_v.set_index(df_v.columns[0])[df_v.columns[1]])
        else:
            st.warning("No hay datos de ventas.")

except Exception as e:
    st.error(f"Error detectado: {e}")
    st.write("Asegúrate de que en el Excel la pestaña se llama COSTES y la columna NOMBRE ARTICULO.")
