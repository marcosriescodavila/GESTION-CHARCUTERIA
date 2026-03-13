import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestión Charcutería BI", page_icon="🧀", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Cargamos las pestañas. 
    # Añadimos ttl=0 para que refresque los datos del Excel al instante
    df_c = conn.read(worksheet="COSTES", ttl=0)
    df_p = conn.read(worksheet="PROVEEDORES", ttl=0)
    try:
        df_v = conn.read(worksheet="VENTAS", ttl=0)
    except:
        df_v = pd.DataFrame()
    
    # Limpieza total: quitamos espacios, puntos y pasamos a mayúsculas
    df_c.columns = [str(c).strip().upper().replace('.', '') for c in df_c.columns]
    df_p.columns = [str(c).strip().upper().replace('.', '') for c in df_p.columns]
    
    return df_c, df_p, df_v

try:
    df_c, df_p, df_v = load_data()
    
    # Buscador ultra-flexible de columnas
    def find_col(possible_names, dataframe):
        for col in dataframe.columns:
            for name in possible_names:
                if name in col:
                    return col
        return None

    col_nombre = find_col(['NOMBRE', 'ARTICULO', 'PRODUCTO'], df_c)

    if not col_nombre:
        st.error("❌ No encuentro la columna del nombre del artículo.")
        st.write("Columnas detectadas en tu Excel:", list(df_c.columns))
    else:
        df_c = df_c.dropna(subset=[col_nombre])

        st.sidebar.title("Charcutería Control")
        menu = st.sidebar.radio("Navegación:", ["Escandallos", "Proveedores", "Ventas"])

        if menu == "Escandallos":
            st.header("⚖️ Análisis de Margen y Costes")
            
            art = st.selectbox("Selecciona un artículo:", df_c[col_nombre].unique())
            d = df_c[df_c[col_nombre] == art].iloc[0]

            # Función para extraer valores numéricos de forma segura
            def safe_num(key_list):
                col = find_col(key_list, df_c)
                if col:
                    val = d[col]
                    return pd.to_numeric(val, errors='coerce') or 0
                return 0

            coste_base = safe_num(['BASE', 'COSTE', 'PRECIO COSTE'])
            coste_real = safe_num(['REAL', 'MERMA E IMPUESTOS'])
            precio_tienda = safe_num(['TIENDA', 'VENTA'])
            superavit = safe_num(['SUPERAVIT'])

            c1, c2, c3 = st.columns(3)
            c1.metric("Coste Base", f"{coste_base:,.2f} €")
            c2.metric("Coste Real", f"{coste_real:,.2f} €")
            c3.metric("Precio Tienda", f"{precio_tienda:,.2f} €")

            st.divider()

            if precio_tienda > 0:
                margen = ((precio_tienda - coste_real) / precio_tienda) * 100
                st.info(f"El margen real actual es del **{margen:.1f}%**")
            
            if superavit < 0:
                st.error(f"⚠️ Alerta: Margen insuficiente. Pierdes {abs(superavit):.2f}€")
            else:
                st.success(f"✅ Superávit de {superavit:.2f}€ sobre objetivo.")

        elif menu == "Proveedores":
            st.header("📞 Directorio de Proveedores")
            st.dataframe(df_p, use_container_width=True)

        elif menu == "Ventas":
            st.header("📈 Rendimiento")
            if not df_v.empty:
                st.line_chart(df_v)
            else:
                st.warning("No hay datos en VENTAS.")

except Exception as e:
    st.error(f"Error crítico: {e}")
