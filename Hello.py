import streamlit as st
from streamlit.logger import get_logger
import threading

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def pagina_inicial():
    # Configuración de la página
    st.set_page_config(page_title="Análisis de Desembolsos", layout="wide")

    # Título de la página
    st.markdown("<h1 style='text-align: center; color: black;'>Análisis de Desembolsos Fonplata</h1>", unsafe_allow_html=True)

    # Introducción y descripción con margen
    st.markdown("""
    <div style="margin-left: 4em;">
        Bienvenido a la aplicación de análisis de desembolsos! Esta herramienta interactiva te permitirá explorar y entender mejor los patrones y tendencias en los desembolsos de los Proyectos.
    </div>
    """, unsafe_allow_html=True)

    # Instrucciones para navegar en la aplicación con margen
    st.markdown("""
    <div style="margin-left: 4em;">
        <h2 style='margin-bottom: 0;'>Cómo Navegar 🧭</h2>
        <p>Explora las distintas secciones de la aplicación para obtener una comprensión completa de los desembolsos:</p>
        <ul>
            <li><strong>Curva de Proyectos</strong>: Análisis detallado de los Montos Desembolsados de los proyectos y su progreso en Años.</li>
            <li><strong>Matrices de Desembolsos</strong>: Explora las matrices detalladas de los Montos de los desembolsos y Porcentaje de los Desembolsos en los Años.</li>
            <li><strong>Curva de Sectores</strong>: Análisis de los Montos Desembolsados de los proyectos y su progreso en Años y por Sectores.</li>
            <li><strong>Curva de Paises</strong>: Análisis de los Montos Desembolsados de los proyectos y su progreso en Años y por Paises.</li>      
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Resumen ejecutivo o highlights con margen
    st.markdown("""
    <div style="margin-left: 4em;">
        <h2 style='margin-bottom: 0;'>Resumen Ejecutivo 🌟</h2>
        <ul>
            <li><strong>Tendencia Anual</strong>: Observa cómo han evolucionado los desembolsos año tras año.</li>
            <li><strong>Comparación por Paises</strong>: Analiza cómo se distribuyen los fondos entre diferentes paises.</li>
            <li><strong>Desembolsos y sus Porcentajes</strong>: Mantente al día con los últimos desembolsos.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align: center;'>
            <img src='https://www.fonplata.org/sites/default/files/glazed-cms-media/SELECCION-BANDERAS.jpg?fid=5544' width='800'>
        </div>
        """, unsafe_allow_html=True)

    # Metodología y fuentes de datos con margen
    st.markdown("""
    <div style="margin-left: 4em;">
        <h2 style='margin-bottom: 0;'>Metodología y Fuentes de Datos 📚</h2>
        <p>Esta aplicación utiliza datos provenientes del Datawarehouse de las Tablas de Operaciones y Desembolsos, con una metodología detallada y rigurosa para asegurar la precisión y relevancia de los análisis presentados.</p>
    </div>
    """, unsafe_allow_html=True)

    # Sección de contacto y feedback con margen
    st.markdown("""
    <div style="margin-left: 4em;">
        <h2 style='margin-bottom: 0;'>Contacto y Feedback 📬</h2>
        <p>¿Tienes preguntas o comentarios? No dudes en contactarnos a través de <a href='mailto:acoronado@fonplata.org'>acoronado@fonplata.org</a> </p>
    </div>
    """, unsafe_allow_html=True)

    # Pie de página con información adicional
    st.markdown("""
    <div style="margin-left: 4em;">
        <hr>
        <p>Desarrollado por <strong>Alessandro Coronado</strong>.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    pagina_inicial()


