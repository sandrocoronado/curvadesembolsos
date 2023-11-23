import streamlit as st
from streamlit.logger import get_logger
import threading

LOGGER = get_logger(__name__)
_lock = threading.Lock()

def pagina_inicial():
    # Configuración de la página
    st.set_page_config(page_title="Análisis de Desembolsos", layout="wide")

    # Título de la página
    st.markdown("<h1 style='text-align: center; color: black;'> Análisis de Desembolsos Fonplata 📊</h1>", unsafe_allow_html=True)

    # Introducción y descripción con margen
    st.markdown("""
    <div style="margin-left: 3em;">
        Bienvenido a la aplicación de análisis de desembolsos! Esta herramienta interactiva te permitirá explorar y entender mejor los patrones y tendencias en los desembolsos de los Proyectos para mejorar la toma de decisiones.
    </div>
    """, unsafe_allow_html=True)

    # Instrucciones para navegar en la aplicación con margen
    st.markdown("""
    <div style="margin-left: 3em;">
        <h2 style='margin-bottom: 0;'>Cómo Navegar 🧭</h2>
        <p>Explora las distintas secciones de la aplicación para obtener una comprensión completa de los desembolsos:</p>
    </div>
    """, unsafe_allow_html=True)

    # Usa el nombre del archivo sin el número inicial, guiones bajos y sin la extensión .py
    st.markdown("[Matrices de Desembolsos](/MatricesDesembolsos)")
    st.markdown("[Curvas de Proyectos](/CurvasProyectos)")


    # Resumen ejecutivo o highlights con margen
    st.markdown("""
    <div style="margin-left: 3em;">
        <h2 style='margin-bottom: 0;'>Resumen Ejecutivo 🌟</h2>
        <ul>
            <li><strong>Tendencia Anual</strong>: Observa cómo han evolucionado los desembolsos año tras año.</li>
            <li><strong>Comparación por Paises</strong>: Analiza cómo se distribuyen los fondos entre diferentes paises.</li>
            <li><strong>Desembolsos y sus Porcentajes</strong>: Mantente al día con los últimos desembolsos.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Metodología y fuentes de datos con margen
    st.markdown("""
    <div style="margin-left: 3em;">
        <h2 style='margin-bottom: 0;'>Metodología y Fuentes de Datos 📚</h2>
        <p>Esta aplicación utiliza datos provenientes del Datawarehouse de las Tablas de Operaciones y Desembolsos, con una metodología detallada y rigurosa para asegurar la precisión y relevancia de los análisis presentados.</p>
    </div>
    """, unsafe_allow_html=True)

    # Sección de contacto y feedback con margen
    st.markdown("""
    <div style="margin-left: 3em;">
        <h2 style='margin-bottom: 0;'>Contacto y Feedback 📬</h2>
        <p>¿Tienes preguntas o comentarios? No dudes en contactarnos a través de <a href='mailto:acoronado@fonplata.org'>acoronado@fonplata.org</a> o deja tus comentarios usando el formulario de feedback en la sección de 'Contacto'.</p>
    </div>
    """, unsafe_allow_html=True)

    # Pie de página con información adicional
    st.markdown("""
    <div style="margin-left: 3em;">
        <hr>
        <p>Desarrollado por <strong>Alessandro Coronado</strong>.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    pagina_inicial()


