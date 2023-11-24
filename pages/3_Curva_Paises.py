import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import threading
import io

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def process_dataframe(xls_path):
    with _lock:
        xls = pd.ExcelFile(xls_path, engine='openpyxl')
        desembolsos = xls.parse('Desembolsos')
        operaciones = xls.parse('Operaciones')

    # Verificar que las columnas 'SECTOR' y 'SUBSECTOR' estén en 'operaciones'
    if 'SECTOR' not in operaciones.columns or 'SUBSECTOR' not in operaciones.columns:
        raise ValueError("Las columnas SECTOR y SUBSECTOR son necesarias en la hoja 'Operaciones'")

    # Mezclar los DataFrames
    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia', 'AporteFonplata', 'SECTOR', 'SUBSECTOR']], on='IDEtapa', how='left')

    # Convertir fechas a datetime
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)

    # Calcular año y meses
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 365).astype(int)
    merged_df['Meses'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 30).astype(int)

    # Crear columnas formateadas para las fechas
    merged_df['FechaEfectiva'] = merged_df['FechaEfectiva'].dt.strftime('%d-%m-%Y')
    merged_df['FechaVigencia'] = merged_df['FechaVigencia'].dt.strftime('%d-%m-%Y')

    # Agrupar y calcular montos acumulados y porcentajes
    result_df = merged_df.groupby(['IDEtapa', 'FechaEfectiva', 'Ano', 'Meses', 'IDDesembolso', 'AporteFonplata'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['IDEtapa'])['Monto'].cumsum()
    result_df['Porcentaje del Monto'] = result_df['Monto'] / result_df['AporteFonplata'] * 100
    result_df['Porcentaje del Monto Acumulado'] = result_df['Monto Acumulado'] / result_df['AporteFonplata'] * 100

    # Mapear códigos de país a nombres
    country_map = {'AR': 'Argentina', 'BO': 'Bolivia', 'BR': 'Brasil', 'PY': 'Paraguay', 'UR': 'Uruguay'}
    result_df['Pais'] = result_df['IDEtapa'].str[:2].map(country_map).fillna('Desconocido')

    # Añadir 'SECTOR', 'SUBSECTOR', 'FechaVigencia' y 'APODO' al DataFrame resultante
    result_df = pd.merge(result_df, operaciones[['IDEtapa', 'SECTOR', 'SUBSECTOR', 'APODO']], on='IDEtapa', how='left')

    return result_df

def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
    output.seek(0)
    return output

def run():
    st.set_page_config(
        page_title="Desembolsos por País",
        page_icon="🌍",
    )

    st.title("Análisis de Desembolsos por País 🌍")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos por país.")

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

        selected_country = st.selectbox('Selecciona el País:', result_df['Pais'].unique())

        filtered_df = result_df[result_df['Pais'] == selected_country]

        # Sumando y convirtiendo el 'Monto' a millones
        df_monto = filtered_df.groupby('Ano')['Monto'].sum().reset_index()
        df_monto['Monto'] /= 1e6

        # Calculando el 'Monto Acumulado' y convirtiéndolo a millones
        df_monto['Monto Acumulado'] = df_monto['Monto'].cumsum()

        # Calculando el 'Porcentaje del Monto'
        df_monto['Porcentaje del Monto'] = ((df_monto['Monto'] / df_monto['Monto'].sum()) * 100).round(2)

        # Calculando el 'Porcentaje Acumulado del Monto'
        df_monto['Porcentaje Acumulado del Monto'] = (df_monto['Monto Acumulado'] / df_monto['Monto'].sum() * 100).round(2)

        st.write("Resumen de Datos:")
        st.write(df_monto)

        # Convertir el DataFrame a bytes y agregar botón de descarga
        excel_bytes = dataframe_to_excel_bytes(df_monto)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="Paises_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Definir colores para los gráficos
        color_monto = 'steelblue'
        color_acumulado = 'goldenrod'
        color_porcentaje = 'salmon'

        # Función para crear gráficos de líneas con puntos y etiquetas
        def line_chart_with_labels(data, x_col, y_col, title, color):
            # Gráfico de línea con puntos
            chart = alt.Chart(data).mark_line(point=True, color=color).encode(
                x=alt.X(f'{x_col}:O', axis=alt.Axis(title='Año', labelAngle=0)),
                y=alt.Y(f'{y_col}:Q', axis=alt.Axis(title=y_col)),
                tooltip=[x_col, y_col]
            ).properties(
                title=title,
                width=600,
                height=400
            )

            # Etiquetas de texto para cada punto
            text = chart.mark_text(
                align='left',
                baseline='middle',
                dx=18,  # Desplazamiento horizontal para evitar superposición con los puntos
                dy=-18
            ).encode(
                text=alt.Text(f'{y_col}:Q', format='.2f')
            )
            return chart + text  # Combinar gráfico de línea con etiquetas

        # Crear los tres gráficos con etiquetas
        chart_monto = line_chart_with_labels(df_monto, 'Ano', 'Monto', 'Monto por Año en Millones', color_monto)
        chart_monto_acumulado = line_chart_with_labels(df_monto, 'Ano', 'Monto Acumulado', 'Monto Acumulado por Año en Millones', color_acumulado)
        chart_porcentaje_acumulado = line_chart_with_labels(df_monto, 'Ano', 'Porcentaje Acumulado del Monto', 'Porcentaje Acumulado del Monto por Año', color_porcentaje)

        # Mostrar los gráficos en Streamlit
        st.altair_chart(chart_monto, use_container_width=True)
        st.altair_chart(chart_monto_acumulado, use_container_width=True)
        st.altair_chart(chart_porcentaje_acumulado, use_container_width=True)



if __name__ == "__main__":
    run()