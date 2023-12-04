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

    # Realizar cálculos y transformaciones necesarias
    merged_all['FechaEfectiva'] = pd.to_datetime(merged_all['FechaEfectiva'], dayfirst=True)
    merged_all['FechaVigencia'] = pd.to_datetime(merged_all['FechaVigencia'], dayfirst=True)
    merged_all['Ano'] = ((merged_all['FechaEfectiva'] - merged_all['FechaVigencia']).dt.days / 366).astype(int)

    result_df = merged_all.groupby(['NoProyecto', 'Ano', 'IDEtapa'])['Monto'].sum().reset_index()
    result_df['Monto Acumulado'] = result_df.groupby(['NoProyecto'])['Monto'].cumsum().reset_index(drop=True)

    # Asumir una columna 'AporteFonplata' en alguna de las hojas para cálculos de porcentaje
    # Si no existe, se debería ajustar este cálculo
    result_df['Porcentaje del Monto'] = result_df['Monto'] / result_df['AporteFonplata'] * 100
    result_df['Porcentaje del Monto Acumulado'] = result_df['Monto Acumulado'] / result_df['AporteFonplata'] * 100

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
        st.write(result_df)
        
        # Convertir el DataFrame a bytes y agregar botón de descarga
        excel_bytes = dataframe_to_excel_bytes(result_df)
        st.download_button(
            label="Descargar DataFrame en Excel",
            data=excel_bytes,
            file_name="resultados_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Suponiendo que 'result_df' es tu DataFrame y tiene las columnas 'IDEtapa' y 'APODO'
        combined_series = result_df['IDEtapa'] + " (" + result_df['APODO'] + ")"

        # Usando esta serie combinada en el selectbox
        selected_combined = st.selectbox('Selecciona el Proyecto:', combined_series.unique())

        # Extraemos el valor de 'IDEtapa' del texto seleccionado para filtrar el DataFrame
        selected_country = selected_combined.split(" (")[0]
        filtered_df = result_df[result_df['IDEtapa'] == selected_country]

        
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
        st.write(combined_df)

        # Convertir Monto a millones y redondear a tres decimales
        combined_df['Monto'] = (combined_df['Monto'] / 1_000_000).round(3)

        # Definir colores para los gráficos
        color_monto = 'steelblue'
        color_porcentaje = 'firebrick'
        color_acumulado = 'goldenrod'

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
