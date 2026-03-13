import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión Charcutería BI", page_icon="🧀", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Cargamos las pestañas con los nombres que tienes
    df_c = conn.read(worksheet="COSTES")
    df_p = conn.read(worksheet="PROVEEDORES")
    try:
        df_v = conn.read(worksheet="VENTAS")
    except:
        df_v = pd.DataFrame()
    return df_c, df_p, df_v

try:
    df_c, df_p, df_v = load_data()
    
    # Limpiamos filas vacías
    df_c = df_c.dropna(subset=['NOMBRE ARTICULO'])

    st.sidebar.title("Charcutería Control")
    menu = st.sidebar.radio("Navegación:", ["Escandallos y Márgenes", "Directorio Proveedores", "Análisis de Ventas"])

    if menu == "Escandallos y Márgenes":
        st.header("⚖️ Cálculo de Coste Real y Rentabilidad")
        
        # Selector de producto
        art = st.selectbox("Selecciona un artículo:", df_c['NOMBRE ARTICULO'].unique())
        d = df_c[df_c['NOMBRE ARTICULO'] == art].iloc[0]

        # Layout de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Coste Base", f"{d['PRECIO COSTE']:.2f} €")
        with col2:
            st.metric("Coste Real (Imp+Merma)", f"{d['COSTE REAL CON MERMA E IMPUESTOS']:.2f} €")
        with col3:
            st.metric("Precio Tienda", f"{d['PRECIO TIENDA']:.2f} €")
        with col4:
            # Calculamos el margen sobre el precio de tienda
            margen = ((d['PRECIO TIENDA'] - d['COSTE REAL CON MERMA E IMPUESTOS']) / d['PRECIO TIENDA']) * 100
            st.metric("Margen Real", f"{margen:.1f} %")

        st.divider()

        # Detalle técnico del producto
        c_a, c_b = st.columns(2)
        with c_a:
            st.write(f"**Proveedor:** {d['PROVEEDOR']}")
            st.write(f"**Categoría:** {d['CATEGORIA']}")
            st.write(f"**Unidad de venta:** {d['UNIDAD DE VENTA']}")
        with c_b:
            st.write(f"**IVA:** {d['IVA']} % | **R.E:** {d['R.E']} %")
            st.write(f"**Merma aplicada:** {d['MERMA']} %")
            st.write(f"**Gasto Envasado:** {d['ENVASADO']} €")

        if d['SUPERAVIT'] < 0:
            st.error(f"⚠️ ¡Ojo! Estás perdiendo {abs(d['SUPERAVIT'])}€ por unidad respecto al objetivo.")
        else:
            st.success(f"✅ Superávit de {d['SUPERAVIT']:.2f} € sobre el margen objetivo.")

    elif menu == "Directorio Proveedores":
        st.header("📞 Contacto Directo")
        st.dataframe(df_p[['PROVEEDOR', 'PERSONA CONTACTO', 'TELEFONO', 'CIF']], use_container_width=True)

    elif menu == "Análisis de Ventas":
        st.header("📈 Rendimiento de Caja")
        if not df_v.empty:
            st.line_chart(df_v.set_index('FECHA')['CAJA'])
        else:
            st.info("La pestaña VENTAS está vacía. Rellénala para ver estadísticas.")

except Exception as e:
    st.error("Error al leer las columnas. Revisa que los nombres en el Excel coincidan exactamente.")
    st.info("Columnas esperadas: PROVEEDOR, CATEGORIA, NOMBRE ARTICULO, PRECIO COSTE, IVA, R.E, MERMA, COSTE REAL CON MERMA E IMPUESTOS, PRECIO TIENDA, SUPERAVIT")
