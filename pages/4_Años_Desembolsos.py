import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Dictionary mapping month numbers to names
MONTHS = {
    1: "Enero", 2: "Febrero", 3: "Marzo",
    4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre",
    10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# Convert DataFrame to Excel format in memory
def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    output.seek(0)
    return output.getvalue()

# Function to process the data
def process_data(uploaded_file):
    if uploaded_file is not None:
        # Read the data from the uploaded file
        data = pd.read_excel(uploaded_file)

        # Convert 'FechaEfectiva' to datetime
        data['FechaEfectiva'] = pd.to_datetime(data['FechaEfectiva'], errors='coerce')

        # Extract month and year from 'FechaEfectiva'
        data['Month'] = data['FechaEfectiva'].dt.month
        data['Year'] = data['FechaEfectiva'].dt.year

        # Allow the user to select a year and a month
        year = st.selectbox("Select Year", sorted(data['Year'].unique()))
        month = st.selectbox("Select Month", list(MONTHS.keys()), format_func=lambda x: MONTHS[x])

        # Filter the data based on the selected month and year
        filtered_data = data[(data['Month'] == month) & (data['Year'] == year)]

        # Calculate the sum of 'Monto' and count of distinct 'IDOperacion'
        total_amount = filtered_data['Monto'].sum()
        distinct_ids = filtered_data['IDOperacion'].nunique()

        # Display the results
        st.write("Total Amount: ", total_amount)
        st.write("Distinct Operation IDs: ", distinct_ids)

        # Provide an option to download the filtered data
        if st.button('Download Filtered Data as Excel'):
            excel_bytes = dataframe_to_excel_bytes(filtered_data)
            st.download_button(
                label="Download Excel",
                data=excel_bytes,
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Streamlit interface
def main():
    st.title('Monthly Data Analysis')

    # File uploader
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

    # Process the uploaded file
    if uploaded_file is not None:
        process_data(uploaded_file)

if __name__ == "__main__":
    main()




