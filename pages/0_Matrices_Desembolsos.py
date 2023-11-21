import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import threading
import io  # <-- Importa io

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def process_dataframe(xls_path):
    with _lock:
        xls = pd.ExcelFile(xls_path, engine='openpyxl')
        desembolsos = xls.parse('Desembolsos')
        operaciones = xls.parse('Operaciones')

    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia', 'AporteFonplata']], on='IDEtapa', how='left')
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 366).astype(int)
    merged_df['Meses'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 30).astype(int)

    result_df = merged_df.groupby(['IDEtapa', 'Ano', 'Meses', 'IDDesembolso', 'AporteFonplata'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['IDEtapa'])['Monto'].cumsum().reset_index(drop=True)
    result_df['Porcentaje del Monto'] = result_df['Monto'] / result_df['AporteFonplata'] * 100
    result_df['Porcentaje del Monto Acumulado'] = result_df['Monto Acumulado'] / result_df['AporteFonplata'] * 100

    country_map = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brasil', 'PY': 'Paraguay', 'UR': 'Uruguay'}
    result_df['Pais'] = result_df['IDEtapa'].str[:2].map(country_map).fillna('Desconocido')
    
    return result_df

def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
    output.seek(0)
    return output

def run():
    st.set_page_config(
        page_title="Desembolsos",
        page_icon="👋",
    )

    st.title("Análisis de Desembolsos 👋")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos.")
    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")
    
    if uploaded_file:
        result_df = process_dataframe(uploaded_file)
        st.write(result_df)
        
        # Convertir el DataFrame a bytes y agregar botón de descarga
        excel_bytes = dataframe_to_excel_bytes(result_df)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="resultados_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        filtered_df = result_df
        
        # Calcular Monto y Monto Acumulado para cada año
        df_monto_anual = filtered_df.groupby('Ano')["Monto"].sum().reset_index()
        df_monto_acumulado_anual = df_monto_anual['Monto'].cumsum()

        # Calcular Porcentaje del Monto de forma acumulativa
        aporte_total = filtered_df['AporteFonplata'].iloc[0]  # Asume que AporteFonplata es constante
        df_porcentaje_monto_anual = (df_monto_anual['Monto'] / aporte_total * 100).round(2)
        df_porcentaje_monto_acumulado_anual = (df_monto_acumulado_anual / aporte_total * 100).round(2)

        # Crear DataFrame combinado para el cuadro de resumen
        combined_df = pd.DataFrame({
            'Ano': df_monto_anual['Ano'],
            'Monto': df_monto_anual['Monto'],
            'Monto Acumulado': df_monto_acumulado_anual,
            'Porcentaje del Monto': df_porcentaje_monto_anual,
            'Porcentaje del Monto Acumulado': df_porcentaje_monto_acumulado_anual
        })

        st.write("Resumen de Datos:")

        combined_df = process_dataframe(uploaded_file)
        
        # Filtrar por países múltiples
        countries = combined_df['Pais'].unique()
        selected_countries = st.multiselect('Selecciona Países:', countries, default=countries)
        filtered_df = combined_df[combined_df['Pais'].isin(selected_countries)]

        # Configuración del formato de visualización de los DataFrame
        pd.options.display.float_format = '{:,.2f}'.format

        # Crear la tabla de Montos con años como columnas y IDEtapa como filas
        montos_pivot = filtered_df.pivot_table(
            index='IDEtapa', 
            columns='Ano', 
            values='Monto', 
            aggfunc='sum'
        ).fillna(0)
        
        # Agregar la columna de totales al final de la tabla de Montos
        montos_pivot['Total'] = montos_pivot.sum(axis=1)

        # Crear la tabla de Porcentajes con años como columnas y IDEtapa como filas
        porcentaje_pivot = filtered_df.pivot_table(
            index='IDEtapa', 
            columns='Ano', 
            values='Porcentaje del Monto', 
            aggfunc='sum'
        ).fillna(0)
        
        # Agregar la columna de totales al final de la tabla de Porcentajes
        porcentaje_pivot['Total'] = porcentaje_pivot.sum(axis=1)

        # Mostrar las tablas en Streamlit con un ancho fijo y la posibilidad de desplazamiento horizontal
        st.write('Tabla de Montos:')
        st.dataframe(montos_pivot, width=1500, height=600)  # Ajusta el ancho y alto según sea necesario

        # Convertir el DataFrame a bytes y agregar botón de descarga
        excel_bytes = dataframe_to_excel_bytes(montos_pivot)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="matriz_montos_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.write('Tabla de Porcentajes del Monto:')
        st.dataframe(porcentaje_pivot, width=1500, height=600)

        # Convertir el DataFrame a bytes y agregar botón de descarga
        excel_bytes = dataframe_to_excel_bytes(porcentaje_pivot)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="matriz_porcentaje_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    run()