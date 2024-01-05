import streamlit as st
import pandas as pd
from streamlit.logger import get_logger
import altair as alt
import re
from datetime import datetime
import threading
import io

LOGGER = get_logger(__name__)
_lock = threading.Lock()

# URLs de las hojas de Google Sheets
sheet_url_proyectos = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHedheaRLyqnjwtsRvlBFFOnzhfarkFMoJ04chQbKZCBRZXh_2REE3cmsRC69GwsUK0PoOVv95xptX/pub?gid=2084477941&single=true&output=csv"
sheet_url_operaciones = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHedheaRLyqnjwtsRvlBFFOnzhfarkFMoJ04chQbKZCBRZXh_2REE3cmsRC69GwsUK0PoOVv95xptX/pub?gid=1468153763&single=true&output=csv"
sheet_url_desembolsos = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHedheaRLyqnjwtsRvlBFFOnzhfarkFMoJ04chQbKZCBRZXh_2REE3cmsRC69GwsUK0PoOVv95xptX/pub?gid=1657640798&single=true&output=csv"

def convert_monto_to_numeric(monto_str):
    if pd.isnull(monto_str):
        return None
    try:
        return float(monto_str.replace('.', '').replace(',', '.'))
    except ValueError:
        LOGGER.error(f"Error al convertir el monto: {monto_str}")
        return None

# Función para convertir las fechas del formato español al formato estándar
def convert_spanish_date(date_str):
    months = {
        'ENE': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'ABR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
        'JUL': 'Jul', 'AGO': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DIC': 'Dec'
    }
    match = re.match(r"(\d{2}) (\w{3}) (\d{2})", date_str)
    if match:
        day, spanish_month, year = match.groups()
        english_month = months.get(spanish_month.upper())
        if english_month:
            return datetime.strptime(f"{day} {english_month} 20{year}", "%d %b %Y").strftime("%d/%m/%Y")
    return date_str

# Función para manejar diferentes formatos de fechas y valores nulos
def convert_dates(date_str):
    if pd.isnull(date_str):
        return None

    if not isinstance(date_str, str):
        return date_str

    months = {
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
    }

    try:
        # Formato '15-ago-14' o '1-dic-17'
        day, month, year = date_str.split('-')
        if len(year) == 2: year = f"20{year}"
        month = months.get(month[:3].lower(), '00')
        return f"{day.zfill(2)}/{month}/{year}"
    except ValueError:
        pass

    try:
        # Formato 'martes, 17 de noviembre de 2015'
        parts = date_str.split(' ')
        day = parts[1]
        month = parts[3].lower()[:3]
        year = parts[5]
        return f"{day.zfill(2)}/{months[month]}/{year}"
    except (ValueError, IndexError):
        pass

    try:
        # Formato '13-abr-20'
        return datetime.strptime(date_str, '%d-%b-%y').strftime('%d/%m/%Y')
    except ValueError:
        pass

    return date_str

# Función para cargar los datos desde la URL
def load_data_from_url(url):
    with _lock:
        try:
            return pd.read_csv(url)
        except Exception as e:
            LOGGER.error("Error al cargar los datos: " + str(e))
            return None

# Adaptación de la función process_dataframe para cargar desde Google Sheets
def process_data():
    proyectos = load_data_from_url(sheet_url_proyectos)
    operaciones = load_data_from_url(sheet_url_operaciones)
    operaciones_desembolsos = load_data_from_url(sheet_url_desembolsos)

    # Verificar la carga correcta de datos
    if proyectos is None or operaciones is None or operaciones_desembolsos is None:
        st.error("Error en la carga de datos desde Google Sheets.")
        return pd.DataFrame()

    # Aplicar la conversión de fechas
    for df in [proyectos, operaciones, operaciones_desembolsos]:
        if 'FechaEfectiva' in df.columns:
            df['FechaEfectiva'] = df['FechaEfectiva'].apply(convert_dates)
        if 'FechaVigencia' in df.columns:
            df['FechaVigencia'] = df['FechaVigencia'].apply(convert_dates)

    # Limpiar y convertir la columna 'Monto' en operaciones_desembolsos
    operaciones_desembolsos['Monto'] = operaciones_desembolsos['Monto'].apply(convert_monto_to_numeric)
    operaciones['AporteFONPLATAVigente'] = operaciones['AporteFONPLATAVigente'].apply(convert_monto_to_numeric)

    # Fusionar los datos
    merged_op_desembolsos = pd.merge(operaciones, operaciones_desembolsos, on=['NoOperacion', 'NoEtapa'], how='left')
    merged_all = pd.merge(merged_op_desembolsos, proyectos, on='NoProyecto', how='left')

    # Convertir fechas a datetime y calcular la diferencia en años
    merged_all['Monto'] = pd.to_numeric(merged_all['Monto'], errors='coerce')
    merged_all['AporteFONPLATAVigente'] = pd.to_numeric(merged_all['AporteFONPLATAVigente'], errors='coerce')
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
    result_df = pd.merge(result_df, proyectos[['NoProyecto', 'IDAreaPrioritaria', 'IDAreaIntervencion','Alias','Pais']], on='NoProyecto', how='left')

    return result_df


# Función para convertir DataFrame a bytes para descargar en Excel
def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
    output.seek(0)
    return output

# Función para convertir DataFrame a bytes para descargar en Excel
def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
    output.seek(0)
    return output

def run():
    st.set_page_config(page_title="Desembolsos", page_icon="👋")
    st.title("Matrices de Desembolsos 📊")
    st.write("Explora las métricas relacionadas con los desembolsos cargando los datos desde Google Sheets.")

    result_df = process_data()
    if not result_df.empty:
        st.write(result_df)

        # Sección para calcular montos y porcentajes
        filtered_df = result_df
        
        # Calcular Monto y Monto Acumulado para cada año
        df_monto_anual = filtered_df.groupby('Ano')["Monto"].sum().reset_index()
        df_monto_acumulado_anual = df_monto_anual['Monto'].cumsum()

        # Calcular Porcentaje del Monto de forma acumulativa
        aporte_total = filtered_df['AporteFONPLATAVigente'].iloc[0]  # Asume que AporteFonplata es constante
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

        st.write("Resumen de Datos:", combined_df)
        
        # Filtrar por países múltiples
        countries = result_df['Pais'].unique()
        selected_countries = st.multiselect('Selecciona Países:', countries, default=countries)
        filtered_df = result_df[result_df['Pais'].isin(selected_countries)]

        # Configuración del formato de visualización de los DataFrame
        pd.options.display.float_format = '{:,.2f}'.format

        # Crear la tabla de Montos con años como columnas y IDEtapa como filas
        montos_pivot = filtered_df.pivot_table(
            index='IDEtapa', 
            columns='Ano', 
            values='Monto', 
            aggfunc='sum'
        ).fillna(0)

        # Convertir los montos a millones
        montos_pivot = (montos_pivot / 1_000_000).round(3)

        # Agregar la columna de totales al final de la tabla de Montos
        montos_pivot['Total'] = montos_pivot.sum(axis=1)

        st.write('Tabla de Montos En Millones de USD:', montos_pivot)

        # Descarga de la tabla de Montos
        excel_bytes_montos = dataframe_to_excel_bytes(montos_pivot)
        st.download_button(
            label="Descargar tabla de Montos en Excel",
            data=excel_bytes_montos,
            file_name="montos_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Crear la tabla de Porcentajes con años como columnas y IDEtapa como filas
        porcentaje_pivot = filtered_df.pivot_table(
            index='IDEtapa', 
            columns='Ano', 
            values='Porcentaje del Monto', 
            aggfunc='sum'
        ).fillna(0)

        # Redondear a dos decimales en el DataFrame de porcentajes
        porcentaje_pivot = porcentaje_pivot.round(2)

        # Agregar la columna de totales al final de la tabla de Porcentajes
        porcentaje_pivot['Total'] = porcentaje_pivot.sum(axis=1).round(0)

        st.write('Tabla de Porcentajes del Monto:', porcentaje_pivot)

        # Descarga de la tabla de Porcentajes
        excel_bytes_porcentajes = dataframe_to_excel_bytes(porcentaje_pivot)
        st.download_button(
            label="Descargar tabla de Porcentajes en Excel",
            data=excel_bytes_porcentajes,
            file_name="porcentajes_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Aplicando la misma lógica para calcular los años hasta ahora y la categorización
        porcentaje_pivot['Años hasta Ahora'] = porcentaje_pivot.iloc[:, :-1].apply(
            lambda row: row.last_valid_index(), axis=1
        )

        # Creando la función de categorización
        def categorize_project(row):
            if row['Total'] == 100:
                return 'Completado'
            elif row['Total'] >= 50:
                return 'Últimos Desembolsos'
            else:
                return 'Empezando sus Desembolsos'

        # Aplicar la categorización a la tabla pivot
        porcentaje_pivot['Categoría'] = porcentaje_pivot.apply(categorize_project, axis=1)

        # Mostrar la tabla con categorías
        st.write('Tabla de Proyectos con Categorías:', porcentaje_pivot)

        # Contando el número de proyectos en cada categoría
        category_counts_pivot = porcentaje_pivot['Categoría'].value_counts()
        st.write('Número de Proyectos por Categoría:', category_counts_pivot)

        # Restableciendo el índice para convertir 'IDEtapa' de nuevo en una columna
        porcentaje_pivot_reset = porcentaje_pivot.reset_index()

        # Seleccionando las columnas para la tabla final
        final_table_pivot = porcentaje_pivot_reset[['IDEtapa', 'Total', 'Años hasta Ahora', 'Categoría']]

        st.write('Tabla Final con Categorías:', final_table_pivot)

        # Descarga de la tabla final con categorías
        excel_bytes_final = dataframe_to_excel_bytes(final_table_pivot)
        st.download_button(
            label="Descargar tabla final con categorías en Excel",
            data=excel_bytes_final,
            file_name="tabla_final_categorías_desembolsos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Contando el número de proyectos en cada categoría
        category_counts_pivot = porcentaje_pivot['Categoría'].value_counts()
        st.write('Número de Proyectos por Categoría:', category_counts_pivot)

        # Utilizar st.columns para colocar gráficos lado a lado
        col1, col2 = st.columns(2)
        with col1:
            st.write('Detalle de Categorías de Proyectos:')
            st.dataframe(final_table_pivot)

        with col2:
            st.write('Distribución de Proyectos por Categoría:')
            st.bar_chart(category_counts_pivot)


if __name__ == "__main__":
    run()