import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Función para calcular los puntajes RFM
def calculate_rfm_scores(data):
    recency = data.groupby('IDEtapa')['FechaEfectiva'].max().reset_index()
    recency['Recency'] = (datetime.now() - recency['FechaEfectiva']).dt.days
    frequency = data.groupby('IDEtapa').size().reset_index(name='Frequency')
    monetary = data.groupby('IDEtapa')['Monto'].sum().reset_index()
    monetary.rename(columns={'Monto': 'Monetary'}, inplace=True)
    rfm = recency.merge(frequency, on='IDEtapa').merge(monetary, on='IDEtapa')
    return rfm

# Función para asignar puntajes R, F, M
def assign_rfm_scores(rfm):
    quantiles = rfm[['Recency', 'Frequency', 'Monetary']].quantile(q=[0.25, 0.5, 0.75]).to_dict()
    rfm['R_Score'] = rfm['Recency'].apply(lambda x: 1 if x <= quantiles['Recency'][0.25] else 2 if x <= quantiles['Recency'][0.5] else 3 if x <= quantiles['Recency'][0.75] else 4)
    rfm['F_Score'] = rfm['Frequency'].apply(lambda x: 4 if x <= quantiles['Frequency'][0.25] else 3 if x <= quantiles['Frequency'][0.5] else 2 if x <= quantiles['Frequency'][0.75] else 1)
    rfm['M_Score'] = rfm['Monetary'].apply(lambda x: 4 if x <= quantiles['Monetary'][0.25] else 3 if x <= quantiles['Monetary'][0.5] else 2 if x <= quantiles['Monetary'][0.75] else 1)
    return rfm

# Función para asignar segmentos
def assign_segment(row):
    if row['R_Score'] <= 2 and row['F_Score'] <= 2:
        return 'Champions'
    elif row['F_Score'] <= 2:
        return 'Loyal Customers'
    elif row['R_Score'] <= 2 and row['F_Score'] > 2 and row['M_Score'] > 2:
        return 'Potential Loyalist'
    elif row['R_Score'] <= 2:
        return 'New Customers'
    elif row['R_Score'] >= 3 and row['F_Score'] <= 2 and row['M_Score'] <= 2:
        return 'At Risk'
    elif row['R_Score'] == 4 and row['F_Score'] <= 2 and row['M_Score'] <= 2:
        return 'Can’t Lose Them'
    else:
        return 'Hibernating'
    
def calculate_segment_statistics(rfm):
    segment_stats = rfm.groupby('Segment').agg(
        Recency_mean=('Recency', 'mean').round(0),
        Frequency_mean=('Frequency', 'mean').round(0),
        Monetary_mean=('Monetary', 'mean').round(0),
        Count=('IDEtapa', 'count')
    ).reset_index()
    return segment_stats

# Función para crear el gráfico 3D
def plot_3d(rfm, sector_data):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    sectors = sector_data['SECTOR'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(sectors)))
    sector_to_color = dict(zip(sectors, colors))
    for sector in sectors:
        sector_rfm = rfm[rfm['SECTOR'] == sector]
        ax.scatter(sector_rfm['Recency'], sector_rfm['Frequency'], sector_rfm['Monetary'], color=sector_to_color[sector], label=sector)
    ax.set_xlabel('Recency')
    ax.set_ylabel('Frequency')
    ax.set_zlabel('Monetary')
    plt.title('RFM Analysis 3D Plot by Country')
    plt.title('RFM Analysis 3D Plot by Sector')
    ax.legend()
    return fig

# Función para crear el gráfico 3D por país
def plot_3d_by_country(rfm):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    countries = rfm['Country'].unique()
    colors = plt.cm.tab20(np.linspace(0, 1, len(countries)))
    country_to_color = dict(zip(countries, colors))
    for country in countries:
        country_rfm = rfm[rfm['Country'] == country]
        ax.scatter(country_rfm['Recency'], country_rfm['Frequency'], country_rfm['Monetary'], color=country_to_color[country], label=country)
    ax.set_xlabel('Recency')
    ax.set_ylabel('Frequency')
    ax.set_zlabel('Monetary')
    plt.title('RFM Analysis 3D Plot by Country')
    ax.legend()
    return fig

# App principal
# App principal
def main():
    st.title("Análisis RFM con Streamlit")
    uploaded_file = st.file_uploader("Sube tu archivo Excel", type="xlsx")

    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file, sheet_name='Desembolsos')
        operaciones = pd.read_excel(uploaded_file, sheet_name='Operaciones')[['IDEtapa', 'SECTOR', 'AporteFonplata']]

        rfm = calculate_rfm_scores(data)
        rfm = assign_rfm_scores(rfm)
        rfm['Segment'] = rfm.apply(assign_segment, axis=1)
        rfm = rfm.merge(operaciones, on='IDEtapa', how='left')
        rfm['Desembolsado'] = (rfm['Monetary'] / rfm['AporteFonplata']) * 100
        rfm['Estado'] = np.where(rfm['Desembolsado'] == 100, 'Terminado', 'Vigente')
        rfm['Country'] = rfm['IDEtapa'].str[:2]

        # Selectbox para filtrar por Estado
        estado_filter = st.selectbox('Filtrar por Estado', ['Todos', 'Terminado', 'Vigente'])
        if estado_filter != 'Todos':
            filtered_rfm = rfm[rfm['Estado'] == estado_filter]
        else:
            filtered_rfm = rfm

        # Selector de sector para el gráfico 3D
        sectors = ['Todos'] + list(operaciones['SECTOR'].unique())
        selected_sector = st.selectbox('Selecciona un sector para el gráfico 3D', sectors)
        if selected_sector != 'Todos':
            sector_filtered_rfm = filtered_rfm[filtered_rfm['SECTOR'] == selected_sector]
        else:
            sector_filtered_rfm = filtered_rfm

        if st.checkbox("Mostrar gráfico 3D por Sector"):
            fig = plot_3d(sector_filtered_rfm, operaciones)
            st.pyplot(fig)

        # Selector de país para el gráfico 3D
        countries = ['Todos'] + list(rfm['Country'].unique())
        selected_country = st.selectbox('Selecciona un país para el gráfico 3D', countries)
        if selected_country != 'Todos':
            country_filtered_rfm = filtered_rfm[filtered_rfm['Country'] == selected_country]
        else:
            country_filtered_rfm = filtered_rfm

        if st.checkbox("Mostrar gráfico 3D por País"):
            fig = plot_3d_by_country(country_filtered_rfm)
            st.pyplot(fig)

        if st.checkbox("Mostrar análisis RFM"):
            st.write(filtered_rfm)

        # Cálculo de estadísticas de segmentos
        if st.checkbox("Mostrar estadísticas de segmentos"):
            segment_stats = calculate_segment_statistics(rfm)
            st.write(segment_stats)


if __name__ == "__main__":
    main()

