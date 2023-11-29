import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Function to convert DataFrame to Excel format in memory
def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()

# Function to display results in a formatted table
def display_results(df, total_amount, distinct_ids):
    # Display the DataFrame as a table
    st.dataframe(df.style.format({"Monto": "{:,.2f}"}))

    # Display summary below the table
    st.write(f"(Suma del Monto): {total_amount:,.2f}")
    st.write(f"(Cantidad de IDOperacion Distintos): {distinct_ids}")

# Function to process the data
def process_data(data, year, month):
    # Filter the data based on the selected month and year
    filtered_data = data[(data['FechaEfectiva'].dt.year == year) & (data['FechaEfectiva'].dt.month == month)]

    # Calculate the sum of 'Monto' and count of distinct 'IDOperacion'
    total_amount = filtered_data['Monto'].sum()
    distinct_ids = filtered_data['IDOperacion'].nunique()

    # Display the results
    display_results(filtered_data, total_amount, distinct_ids)

# Streamlit interface
def main():
    st.set_page_config(page_title="Monthly Data Analysis", page_icon="📊")

    st.title('Monthly Data Analysis')

    # File uploader
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file)

        # Ensure 'FechaEfectiva' is a datetime type
        data['FechaEfectiva'] = pd.to_datetime(data['FechaEfectiva'])

        # Selectbox for selecting the year
        years = sorted(data['FechaEfectiva'].dt.year.unique())
        # Slider for selecting the year
        selected_year = st.slider("Select Year", min_value=2013, max_value=2023, value=2023)

        # Slider for selecting the month
        selected_month = st.slider("Select Month", 1, 12)

        # Button to perform calculation
        if st.button('Calculate'):
            process_data(data, selected_year, selected_month)

        # Display filtered DataFrame to Excel for download
        if st.button('Download Excel'):
            # Filter data for selected month and year
            filtered_data = data[(data['FechaEfectiva'].dt.year == selected_year) & (data['FechaEfectiva'].dt.month == selected_month)]
            excel_bytes = dataframe_to_excel_bytes(filtered_data)
            st.download_button(
                label="Download Excel",
                data=excel_bytes,
                file_name=f"{selected_year}_{selected_month}_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()








