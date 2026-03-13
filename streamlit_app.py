import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Gestión Charcutería BI", page_icon="🧀", layout="wide")

# Conexión con tu Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Usamos los nombres exactos de tus pestañas actuales
    df_costes = conn.read(worksheet="COSTES")
    df_prov = conn.read(worksheet="PROVEEDORES")
    # Intentamos leer ventas, si aún no existe la pestaña, creamos un dataframe vacío
    try:
        df_ventas = conn.read(worksheet="VENTAS")
    except:
        df_ventas = pd.DataFrame(columns=['FECHA', 'CAJA'])
    return df_costes, df_prov, df_ventas

try:
    df_c, df_p, df_v = load_data()

    # Limpieza de datos básica para evitar errores de lectura
    df_c = df_c.dropna(subset=['PRODUCTO'])

    st.sidebar.title("Menú Charcutería")
    opcion = st.sidebar.radio("Ir a:", ["📊 Dashboard Financiero", "⚖️ Calculadora de Margen", "📞 Directorio Proveedores"])

    if opcion == "📊 Dashboard Financiero":
        st.header("Resumen de Negocio")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            total_v = df_v['CAJA'].sum() if not df_v.empty else 0
            st.metric("Ventas Acumuladas", f"{total_v:,.2f} €")
        with c2:
            # Basado en tu deuda de 30.000€
            st.metric("Amortización Pendiente", "12.500 €", "-500 €")
        with c3:
            num_articulos = len(df_c)
            st.metric("Artículos en Catálogo", num_articulos)

        if not df_v.empty:
            st.subheader("Histórico de Ventas")
            st.line_chart(df_v.set_index('FECHA')['CAJA'])
        else:
            st.info("Aún no hay datos en la pestaña VENTAS.")

    elif opcion == "⚖️ Calculadora de Margen":
        st.header("Verificador de Rentabilidad")
        
        producto_sel = st.selectbox("Selecciona un producto:", df_c['PRODUCTO'].unique())
        datos = df_c[df_c['PRODUCTO'] == producto_sel].iloc[0]
        
        # Muestra de datos actuales del Excel
        col1, col2, col3 = st.columns(3)
        
        # Extraemos valores usando tus nombres de columna exactos
        base = float(datos['COSTE BASE (€)'])
        iva = float(datos['IVA (%)']) / 100
        re = float(datos['RE (%)']) / 100
        merma = float(datos['MERMA (%)']) / 100
        envasado = float(datos.get('ENVASADO (€)', 0))
        pvp_actual = float(datos['PVP ACTUAL (€)'])

        # CÁLCULO CIENTÍFICO DEL COSTE REAL
        # 1. Aplicamos impuestos a la base
        coste_con_impuestos = base * (1 + iva + re)
        # 2. Aplicamos la merma (cuánto perdemos al limpiar/cortar)
        coste_tras_merma = coste_con_impuestos / (1 - merma)
        # 3. Sumamos el coste del material de envasado
        coste_final_neto = coste_tras_merma + envasado

        with col1:
            st.metric("Coste Real Neto", f"{coste_final_neto:.2f} €/kg")
        with col2:
            margen_real = ((pvp_actual - coste_final_neto) / pvp_actual) * 100
            st.metric("Margen Real Actual", f"{margen_real:.1f} %")
        with col3:
            pvp_objetivo = coste_final_neto / 0.70 # Para un 30% de margen
            st.metric("PVP Sugerido (30%)", f"{pvp_objetivo:.2f} €")

        if margen_real < 30:
            st.error(f"⚠️ Alerta: El margen de {producto_sel} es inferior al 30% objetivo.")
        else:
            st.success(f"✅ El producto {producto_sel} cumple el objetivo de rentabilidad.")

    elif opcion == "📞 Directorio Proveedores":
        st.header("Contactos de Proveedores")
        busqueda = st.text_input("Buscar proveedor:")
        
        if busqueda:
            resultado = df_p[df_p['PROVEEDOR'].str.contains(busqueda, case=False, na=False)]
            st.dataframe(resultado)
        else:
            st.dataframe(df_p[['PROVEEDOR', 'CIF', 'PERSONA CONTACTO', 'TELEFONO']])

except Exception as e:
    st.error("Error de conexión o de lectura de columnas.")
    st.info("Asegúrate de que las columnas en el Excel se llamen exactamente: PRODUCTO, COSTE BASE (€), IVA (%), RE (%), MERMA (%), PVP ACTUAL (€)")
    st.write(f"Detalle técnico: {e}")
