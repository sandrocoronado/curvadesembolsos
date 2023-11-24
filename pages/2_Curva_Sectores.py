import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import threading

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def process_dataframe_for_sector(xls_path):
    with _lock:
        xls = pd.ExcelFile(xls_path, engine='openpyxl')
        desembolsos = xls.parse('Desembolsos')
        operaciones = xls.parse('Operaciones')

    merged_df = pd.merge(desembolsos, operaciones[['IDEtapa', 'FechaVigencia', 'SECTOR']], on='IDEtapa', how='left')
    merged_df['FechaEfectiva'] = pd.to_datetime(merged_df['FechaEfectiva'], dayfirst=True)
    merged_df['FechaVigencia'] = pd.to_datetime(merged_df['FechaVigencia'], dayfirst=True)
    merged_df['Ano'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 366).astype(int)
    merged_df['Meses'] = ((merged_df['FechaEfectiva'] - merged_df['FechaVigencia']).dt.days / 30).astype(int)
    
    result_df = merged_df.groupby(['SECTOR', 'Ano', 'Meses', 'IDDesembolso'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['SECTOR'])['Monto'].cumsum().reset_index(drop=True)
    result_df['Porcentaje del Monto'] = result_df.groupby(['SECTOR'])['Monto'].apply(lambda x: x / x.sum() * 100).reset_index(drop=True)
    result_df['Porcentaje del Monto Acumulado'] = result_df.groupby(['SECTOR'])['Monto Acumulado'].apply(lambda x: x / x.max() * 100).reset_index(drop=True)

    return result_df

def run_for_sector():
    st.set_page_config(
        page_title="Desembolsos por Sector",
        page_icon="🌍",
    )

    st.title("Análisis de Desembolsos por Sector")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos por sector.")

    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")

    if uploaded_file:
        result_df = process_dataframe_for_sector(uploaded_file)
        st.write(result_df)

        selected_sector = st.selectbox('Selecciona el Sector:', result_df['SECTOR'].unique())

        filtered_df = result_df[result_df['SECTOR'] == selected_sector]

        df_monto = filtered_df.groupby('Ano')["Monto"].mean().reset_index()
        df_monto_acumulado = filtered_df.groupby('Ano')["Monto Acumulado"].mean().reset_index()
        df_porcentaje_monto_acumulado = filtered_df.groupby('Ano')["Porcentaje del Monto Acumulado"].mean().reset_index()
        df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"] = df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"].round(2)

        combined_df = pd.concat([df_monto, df_monto_acumulado["Monto Acumulado"], df_porcentaje_monto_acumulado["Porcentaje del Monto Acumulado"]], axis=1)
        st.write("Resumen de Datos:")
        st.write(combined_df)

        chart_monto = alt.Chart(df_monto).mark_line(point=True, color='blue').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Monto:Q',
            tooltip=['Ano', 'Monto']
        ).properties(
            title=f'Promedio de Monto por año para {selected_sector}',
            width=600,
            height=400
        )
        st.altair_chart(chart_monto, use_container_width=True)

        chart_monto_acumulado = alt.Chart(df_monto_acumulado).mark_line(point=True, color='purple').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Monto Acumulado:Q',
            tooltip=['Ano', 'Monto Acumulado']
        ).properties(
            title=f'Promedio de Monto Acumulado por año para {selected_sector}',
            width=600,
            height=400
        )
        st.altair_chart(chart_monto_acumulado, use_container_width=True)

        chart_porcentaje = alt.Chart(df_porcentaje_monto_acumulado).mark_line(point=True, color='green').encode(
            x=alt.X('Ano:O', axis=alt.Axis(title='Año', labelAngle=0)),
            y='Porcentaje del Monto Acumulado:Q',
            tooltip=['Ano', 'Porcentaje del Monto Acumulado']
        ).properties(
            title=f'Promedio del Porcentaje del Monto Acumulado por año para {selected_sector}',
            width=600,
            height=400
        )
        st.altair_chart(chart_porcentaje, use_container_width=True)


if __name__ == "__main__":
    run_for_sector()
