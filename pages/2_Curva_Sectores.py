import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import threading
import io  # <-- Importa io

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def process_dataframe_for_sector(xls_path):
    with _lock:
        xls = pd.ExcelFile(xls_path, engine='openpyxl')
        proyectos = xls.parse('Proyectos')
        operaciones = xls.parse('Operaciones')
        operaciones_desembolsos = xls.parse('OperacionesDesembolsos')

    # Fusionar los datos
    merged_op_desembolsos = pd.merge(operaciones, operaciones_desembolsos, on=['NoOperacion', 'NoEtapa'], how='left')
    merged_all = pd.merge(merged_op_desembolsos, proyectos, on='NoProyecto', how='left')

    # Convertir fechas a datetime y calcular la diferencia en años y meses
    merged_all['FechaEfectiva'] = pd.to_datetime(merged_all['FechaEfectiva'], dayfirst=True)
    merged_all['FechaVigencia'] = pd.to_datetime(merged_all['FechaVigencia'], dayfirst=True)
    merged_all.dropna(subset=['FechaEfectiva', 'FechaVigencia'], inplace=True)
    merged_all['Ano'] = ((merged_all['FechaEfectiva'] - merged_all['FechaVigencia']).dt.days / 366).astype(int)
    merged_all['Meses'] = ((merged_all['FechaEfectiva'] - merged_all['FechaVigencia']).dt.days / 30).astype(int)

    # Filtrar para excluir años y meses negativos
    merged_all = merged_all[(merged_all['Ano'] >= 0) & (merged_all['Meses'] >= 0)]
    
    # Realizar cálculos utilizando 'AporteFONPLATAVigente' y 'IDAreaPrioritaria'
    result_df = merged_all.groupby(['IDAreaPrioritaria', 'Ano', 'Meses', 'IDEtapa'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['IDAreaPrioritaria'])['Monto'].cumsum().reset_index(drop=True)
    result_df['Porcentaje del Monto'] = result_df.groupby(['IDAreaPrioritaria'])['Monto'].apply(lambda x: x / x.sum() * 100).reset_index(drop=True)
    result_df['Porcentaje del Monto Acumulado'] = result_df.groupby(['IDAreaPrioritaria'])['Monto Acumulado'].apply(lambda x: x / x.max() * 100).reset_index(drop=True)

    return result_df
    

def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
    output.seek(0)
    return output

def run_for_sector():
    st.set_page_config(
        page_title="Desembolsos por Sector",
        page_icon="🌍",
    )

    st.title("Análisis de Desembolsos por Sector 🌍")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos por sector.")

    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")

    if uploaded_file:
        result_df = process_dataframe_for_sector(uploaded_file)
        st.write(result_df)

        excel_bytes = dataframe_to_excel_bytes(result_df)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="resultados_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        sorted_sectors = result_df['IDAreaPrioritaria'].sort_values().unique()
        selected_sector = st.selectbox('Selecciona el Sector:', sorted_sectors)

        filtered_df = result_df[result_df['IDAreaPrioritaria'] == selected_sector]

        df_monto = filtered_df.groupby('Ano')['Monto'].sum().reset_index()
        df_monto['Monto'] /= 1e6
        df_monto['Monto Acumulado'] = df_monto['Monto'].cumsum()
        df_monto['Porcentaje del Monto'] = ((df_monto['Monto'] / df_monto['Monto'].sum()) * 100).round(2)
        df_monto['Porcentaje Acumulado del Monto'] = (df_monto['Monto Acumulado'] / df_monto['Monto'].sum() * 100).round(2)

        st.write("Resumen de Datos:")
        st.write(df_monto)

        excel_bytes = dataframe_to_excel_bytes(df_monto)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="sectores_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        color_monto = 'steelblue'
        color_acumulado = 'goldenrod'
        color_porcentaje = 'salmon'

        def line_chart_with_labels(data, x_col, y_col, title, color):
            chart = alt.Chart(data).mark_line(point=True, color=color).encode(
                x=alt.X(f'{x_col}:O', axis=alt.Axis(title='Año', labelAngle=0)),
                y=alt.Y(f'{y_col}:Q', axis=alt.Axis(title=y_col)),
                tooltip=[x_col, y_col]
            ).properties(
                title=title,
                width=600,
                height=400
            )

            text = chart.mark_text(
                align='left',
                baseline='middle',
                dx=18,
                dy=-18
            ).encode(
                text=alt.Text(f'{y_col}:Q', format='.2f')
            )
            return chart + text

        chart_monto = line_chart_with_labels(df_monto, 'Ano', 'Monto', 'Monto por Año en Millones', color_monto)
        chart_monto_acumulado = line_chart_with_labels(df_monto, 'Ano', 'Monto Acumulado', 'Monto Acumulado por Año en Millones', color_acumulado)
        chart_porcentaje_acumulado = line_chart_with_labels(df_monto, 'Ano', 'Porcentaje Acumulado del Monto', 'Porcentaje Acumulado del Monto por Año', color_porcentaje)

        st.altair_chart(chart_monto, use_container_width=True)
        st.altair_chart(chart_monto_acumulado, use_container_width=True)
        st.altair_chart(chart_porcentaje_acumulado, use_container_width=True)

if __name__ == "__main__":
    run_for_sector()
