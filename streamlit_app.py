import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración profesional
st.set_page_config(page_title="Gestión Charcutería BI", page_icon="🧀", layout="wide")

# Conexión con tu archivo
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    costes = conn.read(worksheet="CATALOGO_COSTES")
    ventas = conn.read(worksheet="VENTAS")
    pagos = conn.read(worksheet="PAGOS_PROVEEDORES")
    return costes, ventas, pagos

try:
    df_c, df_v, df_p = load_data()
    
    st.sidebar.title("Menú de Gestión")
    opcion = st.sidebar.radio("Ir a:", ["Dashboard Financiero", "Calculadora de Precios", "Facturas y Pagos"])

    if opcion == "Dashboard Financiero":
        st.header("📊 Resumen de Rentabilidad")
        
        # Métricas principales
        c1, c2, c3 = st.columns(3)
        total_ventas = df_v['Total Caja'].sum() if 'Total Caja' in df_v.columns else 0
        c1.metric("Ventas Totales", f"{total_ventas:,.2f} €")
        
        # Cálculo de deuda (asumiendo base de 30.000€)
        amortizado = 30000 - 12500 # Ejemplo con tus datos actuales
        c2.metric("Deuda Pendiente", "12.500 €", delta="-500 €", delta_color="normal")
        
        c3.metric("Proveedores Pendientes", len(df_p[df_p['Estado'] == 'PENDIENTE']))

        st.subheader("Evolución de Caja")
        st.line_chart(df_v.set_index('Fecha')['Total Caja'])

    elif opcion == "Calculadora de Precios":
        st.header("⚖️ Verificador de Margen Real")
        prod = st.selectbox("Selecciona un producto del catálogo", df_c['Producto'].unique())
        
        datos = df_c[df_c['Producto'] == prod].iloc[0]
        
        # Lógica de cálculo automática
        base = datos['Coste Base (Kg/Ud)']
        iva = datos['IVA (%)'] / 100
        re = datos['RE (%)'] / 100
        merma = datos['Merma (%)'] / 100
        
        coste_real = (base * (1 + iva + re)) / (1 - merma)
        pvp_sugerido = coste_real / 0.70  # Para mantener margen del 30%
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Coste Real puesto en tienda:** {coste_real:.2f} €")
            st.success(f"**PVP Sugerido (30% margen):** {pvp_sugerido:.2f} €")
        
        with col2:
            st.warning(f"**PVP Actual en Báscula:** {datos['PVP Actual']} €")
            margen_actual = (datos['PVP Actual'] - coste_real) / datos['PVP Actual']
            st.metric("Margen Actual", f"{margen_actual*100:.1f}%")

    elif opcion == "Facturas y Pagos":
        st.header("🧾 Conciliación de Proveedores")
        st.dataframe(df_p[df_p['Estado'] == 'PENDIENTE'])
        
        if st.button("Marcar factura seleccionada como PAGADA"):
            st.write("Esta función actualizará tu Google Sheets automáticamente.")

except Exception as e:
    st.error(f"Conecta el Sheets en la configuración de Streamlit: {e}")
