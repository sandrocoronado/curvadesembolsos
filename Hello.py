import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Análisis de Desembolsos", layout="wide")

# Título de la página
st.markdown("<h1 style='text-align: center; color: black;'>📊 Análisis de Desembolsos</h1>", unsafe_allow_html=True)

# Introducción y descripción
st.markdown("""
Bienvenido a la aplicación de análisis de desembolsos! Esta herramienta interactiva te permitirá explorar y entender mejor los patrones y tendencias en los desembolsos de los Proyectos.
""")

# Instrucciones para navegar en la aplicación
st.header("Cómo Navegar 🧭")
st.markdown("""
Explora las distintas secciones de la aplicación para obtener una comprensión completa de los desembolsos:

- **Curva de Proyectos**: Análisis detallado de los Montos Desembolsados de los proyectos y su progreso en Años. 
- **Matrices de Desembolsos**: Explora las matrices detalladas de los Montos de los desembolsos y Porcentaje de los Desembolsos en los Años.

Selecciona la página que deseas visitar utilizando los enlaces a continuación:
- [Curva_Proyectos](#curva-proyectos)
- [Matrices_Desembolsos](#matrices-desembolsos)
""")

# Resumen ejecutivo o highlights
st.header("Highlights 🌟")
st.markdown("""
- **Tendencia Anual**: Observa cómo han evolucionado los desembolsos año tras año.
- **Comparación por Sector**: Analiza cómo se distribuyen los fondos entre diferentes sectores.
- **Desembolsos Recientes**: Mantente al día con los últimos desembolsos y su impacto.
""")

# Información sobre metodología y fuentes de datos
st.header("Metodología y Fuentes de Datos 📚")
st.markdown("""
Esta aplicación utiliza datos provenientes del Datawarehouse de las Tablas de Operaciones y Desembolsos, con una metodología detallada y rigurosa para asegurar la precisión y relevancia de los análisis presentados.
""")

# Sección de contacto y feedback
st.header("Contacto y Feedback 📬")
st.markdown("""
¿Tienes preguntas o comentarios? No dudes en contactarnos a través de [acoronado@fonplata.org] o deja tus comentarios usando el formulario de feedback en la sección de 'Contacto'.
""")

# Pie de página con información adicional
st.markdown("---")
st.markdown("""
Desarrollado por [Alessandro Coronado].
""")

