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
        proyectos = xls.parse('Proyectos')
        operaciones = xls.parse('Operaciones')
        operaciones_desembolsos = xls.parse('OperacionesDesembolsos')

    # Fusionar los datos
    merged_op_desembolsos = pd.merge(operaciones, operaciones_desembolsos, on=['NoOperacion', 'NoEtapa'], how='left')
    merged_all = pd.merge(merged_op_desembolsos, proyectos, on='NoProyecto', how='left')

    # Convertir fechas a datetime y calcular la diferencia en años
    merged_all['FechaEfectiva'] = pd.to_datetime(merged_all['FechaEfectiva'], dayfirst=True)
    merged_all['FechaVigencia'] = pd.to_datetime(merged_all['FechaVigencia'], dayfirst=True)
    merged_all.dropna(subset=['FechaEfectiva', 'FechaVigencia'], inplace=True)
    merged_all['Ano'] = ((merged_all['FechaEfectiva'] - merged_all['FechaVigencia']).dt.days / 366).astype(int)

    # Realizar cálculos utilizando 'AporteFONPLATA'
    result_df = merged_all.groupby(['NoProyecto', 'Ano', 'IDEtapa'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['NoProyecto'])['Monto'].cumsum().reset_index(drop=True)

    # Verificar si 'AporteFONPLATA' está en 'operaciones'
    if 'AporteFONPLATAVigente' in operaciones.columns:
        result_df = pd.merge(result_df, operaciones[['NoProyecto', 'AporteFONPLATAVigente']], on='NoProyecto', how='left')
        result_df['Porcentaje del Monto'] = result_df['Monto'] / result_df['AporteFONPLATAVigente'] * 100
        result_df['Porcentaje del Monto Acumulado'] = result_df['Monto Acumulado'] / result_df['AporteFONPLATAVigente'] * 100
    else:
        st.error("La columna 'AporteFONPLATA' no se encontró en la hoja 'Operaciones'.")

    # Añadir 'IDAreaPrioritaria' (Sector) y 'IDAreaIntervencion' (Subsector) al DataFrame resultante
    result_df = pd.merge(result_df, proyectos[['NoProyecto', 'IDAreaPrioritaria', 'IDAreaIntervencion']], on='NoProyecto', how='left')

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

    st.title("Desembolsos de Proyectos📊")
    st.write("Carga tu archivo Excel y explora las métricas relacionadas con los desembolsos.")
    uploaded_file = st.file_uploader("Carga tu Excel aquí", type="xlsx")
    
    if uploaded_file:
        result_df = process_dataframe(uploaded_file)
        # Initialize combined_df to ensure it's always defined for later use
        combined_df = pd.DataFrame()

        st.write(result_df)
        
        # Convertir el DataFrame a bytes y agregar botón de descarga
        excel_bytes = dataframe_to_excel_bytes(result_df)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="resultados_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Definir colores para los gráficos
        color_monto = 'steelblue'
        color_porcentaje = 'firebrick'
        color_acumulado = 'goldenrod'
        
        # Asegurar que las columnas necesarias estén presentes
        if 'IDEtapa' in result_df.columns:
            # Crear una serie combinada con 'IDEtapa' y 'APODO' si está disponible
            if 'APODO' in result_df.columns:
                combined_series = result_df['IDEtapa'] + " (" + result_df['APODO'] + ")"
            else:
                combined_series = result_df['IDEtapa'].astype(str)
            
            # Ordenar las opciones alfabéticamente
            sorted_combined_series = combined_series.sort_values()

            # Usar la serie ordenada en el selectbox
            selected_combined = st.selectbox('Selecciona el Proyecto:', sorted_combined_series.unique())
            selected_etapa = selected_combined.split(" (")[0]
            filtered_df = result_df[result_df['IDEtapa'] == selected_etapa]

            if 'AporteFONPLATAVigente' in filtered_df.columns:
                # Perform calculations only if 'AporteFONPLATA' is available
                df_monto_anual = filtered_df.groupby('Ano')['Monto'].sum().reset_index()
                df_monto_acumulado_anual = df_monto_anual['Monto'].cumsum()

                aporte_total = filtered_df['AporteFONPLATAVigente'].iloc[0]
                df_porcentaje_monto_anual = (df_monto_anual['Monto'] / aporte_total * 100).round(2)
                df_porcentaje_monto_acumulado_anual = (df_monto_acumulado_anual / aporte_total * 100).round(2)

                combined_df = pd.DataFrame({
                    'Ano': df_monto_anual['Ano'],
                    'Monto': df_monto_anual['Monto'],
                    'Monto Acumulado': df_monto_acumulado_anual,
                    'Porcentaje del Monto': df_porcentaje_monto_anual,
                    'Porcentaje del Monto Acumulado': df_porcentaje_monto_acumulado_anual
                })

                st.write("Resumen de Datos:")
                st.write(combined_df)
                
                # Ensure 'Monto' is in the combined_df before attempting to modify it
                if 'Monto' in combined_df.columns:
                    combined_df['Monto'] = (combined_df['Monto'] / 1_000_000).round(3)
                # Additional code for chart generation goes here...
            else:
                st.error("La columna 'AporteFONPLATA' no está presente en los datos cargados.")
        else:
            st.error("La columna 'IDEtapa' no está presente en los datos cargados.")


        # Función para crear gráficos de líneas con puntos y etiquetas
        def line_chart_with_labels(data, x_col, y_col, title, color):
            # Gráfico de línea con puntos
            chart = alt.Chart(data).mark_line(point=alt.OverlayMarkDef(color=color, fill='black', strokeWidth=2), strokeWidth=3).encode(
                x=alt.X(f'{x_col}:N', axis=alt.Axis(title='Año', labelAngle=0)),
                y=alt.Y(f'{y_col}:Q', axis=alt.Axis(title=y_col)),
                color=alt.value(color),
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
                dx=20,  # Desplazamiento en el eje X para evitar solapamiento con los puntos
                dy=-20  # Desplazamiento en el eje Y para alejar el texto de la línea
            ).encode(
                text=alt.Text(f'{y_col}:Q'),
                color=alt.value('black')  # Establece el color del texto a negro
            )
            return chart + text  # Combinar gráfico de línea con etiquetas

        # Crear los tres gráficos con etiquetas
        chart_monto = line_chart_with_labels(combined_df, 'Ano', 'Monto', 'Monto por Año en Millones de USD', color_monto)
        chart_porcentaje_monto = line_chart_with_labels(combined_df, 'Ano', 'Porcentaje del Monto', 'Porcentaje del Monto Desembolsado por Año', color_porcentaje)
        chart_porcentaje_monto_acumulado = line_chart_with_labels(combined_df, 'Ano', 'Porcentaje del Monto Acumulado', 'Porcentaje del Monto Acumulado por Año', color_acumulado)

        # Mostrar los gráficos en Streamlit
        st.altair_chart(chart_monto, use_container_width=True)
        st.altair_chart(chart_porcentaje_monto, use_container_width=True)
        st.altair_chart(chart_porcentaje_monto_acumulado, use_container_width=True)

if __name__ == "__main__":
    run()
