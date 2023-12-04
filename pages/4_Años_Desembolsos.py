import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Función para convertir un DataFrame a formato Excel en memoria
def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()

# Función para fusionar datos de múltiples hojas
def merge_data(xls):
    proyectos = xls.parse('Proyectos')
    operaciones = xls.parse('Operaciones')
    operaciones_desembolsos = xls.parse('OperacionesDesembolsos')

    # Fusionar 'operaciones_desembolsos' con 'operaciones'
    merged_op_desembolsos = pd.merge(operaciones_desembolsos, operaciones, on='NoEtapa', how='left')

    # Fusionar el resultado con 'proyectos'
    merged_data = pd.merge(merged_op_desembolsos, proyectos, on='NoProyecto', how='left')

    return merged_data

# Función para procesar y mostrar los datos
def process_data(data, selected_year, selected_month):
    # Filtrar datos por año y mes seleccionados
    filtered_data = data[(data['FechaEfectiva'].dt.year == selected_year) & 
                         (data['FechaEfectiva'].dt.month == selected_month)]

    # Calcular el monto total
    total_monto = filtered_data['Monto'].sum()

    # Mostrar los resultados
    st.write(f"Monto Total: {total_monto:,.2f}")
    st.dataframe(filtered_data[['IDOperacion', 'Pais', 'FechaEfectiva', 'Monto', 'IDAreaPrioritaria', 'IDAreaIntervencion']])

# Interfaz de Streamlit
def main():
    st.set_page_config(page_title="Análisis de Datos Mensual", page_icon="📊")
    st.title('Análisis de Datos Mensual')

    # Cargador de archivos
    uploaded_file = st.file_uploader("Elige un archivo Excel", type=["xlsx"])
    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        data = merge_data(xls)

        # Asegurarse de que 'FechaEfectiva' es un tipo datetime
        data['FechaEfectiva'] = pd.to_datetime(data['FechaEfectiva'])

        # Determinar el rango de años disponibles
        min_year = int(data['FechaEfectiva'].dt.year.min())
        max_year = int(data['FechaEfectiva'].dt.year.max())

        # Slider para seleccionar el año
        selected_year = st.slider("Selecciona el Año", min_year, max_year, max_year)

        # Slider para seleccionar el mes
        selected_month = st.slider("Selecciona el Mes", 1, 12, 1)

        # Mostrar DataFrame preliminar
        preview_data = data[(data['FechaEfectiva'].dt.year == selected_year) & 
                            (data['FechaEfectiva'].dt.month == selected_month)]
        st.dataframe(preview_data[['IDOperacion', 'Pais', 'FechaEfectiva', 'Monto', 'IDAreaPrioritaria', 'IDAreaIntervencion']])

        # Botón para realizar el cálculo
        if st.button('Calcular'):
            process_data(data, selected_year, selected_month)

if __name__ == "__main__":
    main()












