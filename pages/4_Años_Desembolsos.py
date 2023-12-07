import streamlit as st
import pandas as pd
import io
from datetime import datetime
from streamlit.logger import get_logger
import threading

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()

def merge_data(xls):
    proyectos = xls.parse('Proyectos')
    operaciones = xls.parse('Operaciones')
    operaciones_desembolsos = xls.parse('OperacionesDesembolsos')

    # Fusionar 'OperacionesDesembolsos' con 'Operaciones' usando 'NoEtapa'
    merged_op_desembolsos = pd.merge(operaciones_desembolsos, operaciones, on='NoOperacion', how='left')

    # Fusionar el resultado con 'Proyectos' usando 'NoOperacion'
    merged_data = pd.merge(merged_op_desembolsos, proyectos, on='NoProyecto', how='left')

    return merged_data

def process_data(merge_data, selected_year, selected_month):
    filtered_data = merge_data[(merge_data['FechaEfectiva'].dt.year == selected_year) & 
                         (merge_data['FechaEfectiva'].dt.month == selected_month)]
    total_monto = filtered_data['Monto'].sum()
    st.write(f"Monto Total: {total_monto:,.2f}")
    columns_to_display = ['IDOperacion', 'Pais', 'FechaEfectiva', 'Monto', 'IDAreaPrioritaria', 'IDAreaIntervencion']
    if all(col in filtered_data.columns for col in columns_to_display):
        st.dataframe(filtered_data[columns_to_display])
    else:
        st.write("One or more columns are missing in the DataFrame.")

def main():
    st.set_page_config(page_title="Análisis de Datos Mensual", page_icon="📊")
    st.title('Análisis de Datos Mensual')

    uploaded_file = st.file_uploader("Elige un archivo Excel", type=["xlsx"])
    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        data = merge_data(xls)
        data['FechaEfectiva'] = pd.to_datetime(data['FechaEfectiva'])

        min_year = int(data['FechaEfectiva'].dt.year.min())
        max_year = int(data['FechaEfectiva'].dt.year.max())

        selected_year = st.slider("Selecciona el Año", min_year, max_year, max_year)
        selected_month = st.slider("Selecciona el Mes", 1, 12, 1)

        preview_data = data[(data['FechaEfectiva'].dt.year == selected_year) & 
                            (data['FechaEfectiva'].dt.month == selected_month)]
        columns_to_display = ['IDOperacion', 'Pais', 'FechaEfectiva', 'Monto', 'IDAreaPrioritaria', 'IDAreaIntervencion']
        if all(col in preview_data.columns for col in columns_to_display):
            st.dataframe(preview_data[columns_to_display])
        else:
            st.write("One or more columns are missing in the DataFrame.")

        if st.button('Calcular'):
            process_data(data, selected_year, selected_month)

if __name__ == "__main__":
    main()















