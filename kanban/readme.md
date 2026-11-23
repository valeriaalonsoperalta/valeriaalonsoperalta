Aquí tienes el texto con el formato corregido para una mejor visualización en Markdown. Se han limpiado los espacios extraños, se ha normalizado el uso de negritas y se ha estructurado el texto para una lectura más fluida.

# Kanban Flow Optimizer 🌊

Bienvenido al **Kanban Flow Optimizer**, un laboratorio de simulación interactivo diseñado para el curso de "Gestión de Proyectos Ágiles con IA". Esta aplicación **no es una herramienta de gestión de proyectos**, sino un **simulador de procesos** que te permite experimentar con los principios de **Kanban** y visualizar su impacto en tiempo real.

Aprenderás de forma práctica por qué **limitar el Trabajo en Curso (WIP)** es una de las palancas más poderosas para mejorar la velocidad y predictibilidad de un equipo.

-----

## 📚 Índice

  * [Visión General](https://www.google.com/search?q=%23%F0%9F%8E%AF-visi%C3%B3n-general)
  * [Características Principales](https://www.google.com/search?q=%23%E2%9C%A8-caracter%C3%ADsticas-principales)
  * [Requisitos Previos](https://www.google.com/search?q=%23%F0%9F%93%8B-requisitos-previos)
  * [Guía de Instalación y Configuración](https://www.google.com/search?q=%23%F0%9F%9A%80-gu%C3%ADa-de-instalaci%C3%B3n-y-configuraci%C3%B3n)
  * [Cómo Usar el Simulador](https://www.google.com/search?q=%23%F0%9F%92%BB-c%C3%B3mo-usar-el-simulador)
  * [El Rol del Agile Coach de IA](https://www.google.com/search?q=%23%F0%9F%A4%96-el-rol-del-agile-coach-de-ia)
  * [Tecnologías Utilizadas](https://www.google.com/search?q=%23-tecnolog%C3%ADas-utilizadas)

-----

## 🎯 Visión General

Este simulador te pone en el rol de un **Agile Coach**. Tu objetivo no es hacer el trabajo, sino diseñar un sistema de trabajo eficiente. Configurarás un tablero Kanban virtual, establecerás políticas (como los límites de WIP) y observarás cómo un equipo virtual procesa un lote de tareas.

Los resultados se presentan a través de **métricas y gráficos estándar de Kanban**, permitiéndote:

  * Identificar cuellos de botella visualmente.
  * Medir el impacto de los cambios en el proceso.
  * Entender la relación entre **WIP**, **Cycle Time** y **Throughput**.
  * Utilizar una IA para analizar los resultados y obtener recomendaciones expertas.

-----

## ✨ Características Principales

  * **Configuración Flexible:** Define el número de tareas, el tamaño del equipo y los límites de WIP para cada etapa del flujo.
  * **Simulación de Flujo Realista:** Un motor de simulación día a día que respeta los límites de WIP y la capacidad del equipo, implementando un sistema "pull".
  * **Métricas Clave de Kanban:** Calcula automáticamente el **Throughput**, **Lead Time promedio** y **Cycle Time promedio**.
  * **Visualizaciones Profesionales:**
      * **Diagrama de Flujo Acumulativo (CFD):** Para analizar la salud del flujo de trabajo.
      * **Gráfico de Dispersión de Lead Time:** Para evaluar la predictibilidad del proceso.
  * **Análisis por IA:** Un "**Agile Coach**" de IA integrado que analiza los resultados de tu simulación y te ofrece un diagnóstico y recomendaciones para mejorar.
  * **Soporte Multi-IA:** Compatible con Gemini, Groq y OpenRouter.

-----

## 📋 Requisitos Previos

1.  **Python 3.8 o superior**.
2.  Una **Clave de API** de al menos uno de los siguientes proveedores:
      * [Google Gemini](https://aistudio.google.com/)
      * [Groq](https://console.groq.com/keys)
      * [OpenRouter](https://openrouter.ai/keys)

-----

## 🚀 Guía de Instalación y Configuración

1.  **Crea una Carpeta para el Proyecto** y guarda el archivo `kanban_optimizer.py` dentro.

2.  **Crea un Entorno Virtual** (recomendado):

    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instala las Dependencias:** Crea un archivo `requirements.txt` con el siguiente contenido:

    ```txt
    streamlit
    python-dotenv
    google-generativeai
    openai
    pandas
    numpy
    plotly
    ```

    Y luego instala todo con:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura las Claves de API:** Crea un archivo `.env` en la misma carpeta y añade tus claves. Solo necesitas rellenar la del proveedor que vayas a usar.

    ```env
    # .env
    GEMINI_API_KEY=Tu_Clave_de_Gemini
    GROQ_API_KEY=Tu_Clave_de_Groq
    OPENROUTER_API_KEY=Tu_Clave_de_OpenRouter
    ```

-----

## 💻 Cómo Usar el Simulador

1.  **Inicia la Aplicación:**

    ```bash
    streamlit run kanban_optimizer.py
    ```

2.  **Configura los Parámetros:** En la barra lateral, ajusta los controles deslizantes y los campos numéricos para definir tu escenario de simulación. Presta especial atención a los **Límites de WIP**.

3.  **Ejecuta la Simulación:** Haz clic en el botón **"🚀 Ejecutar Simulación"**.

4.  **Analiza los Resultados:**

      * Observa las **Métricas Clave** para un resumen rápido.
      * Estudia el **CFD** para identificar visualmente los cuellos de botella (donde las bandas se ensanchan).
      * Revisa el **Scatter Plot** para entender la predictibilidad de tus entregas.

-----

## 🤖 El Rol del Agile Coach de IA

Después de ejecutar una simulación, aparecerá una nueva pestaña llamada **"🤖 Análisis del Coach de IA"**.

1.  Haz clic en el botón **"Analizar Resultados con IA"**.
2.  La aplicación enviará los parámetros de tu simulación y los resultados obtenidos a la IA que hayas seleccionado.
3.  La IA te devolverá un **análisis experto**, explicando qué significan los resultados, cuál es el principal problema de tu flujo y qué cambios podrías hacer en los límites de WIP para mejorarlo.

¡Usa esta función para validar tus propias conclusiones y aprender de un experto virtual\!