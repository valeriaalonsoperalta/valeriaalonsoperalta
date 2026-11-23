# 🧑‍💻 Simulador de Equipo SCRUM con IA

Bienvenido al Simulador de Equipo SCRUM, una aplicación interactiva construida con Streamlit y la potencia de la IA generativa de Google (Gemini). Esta herramienta está diseñada para estudiantes, profesionales y entusiastas de la agilidad que deseen aprender y practicar la gestión de un proyecto SCRUM en un entorno controlado y dinámico.

A través de esta simulación, tomarás el doble rol de Product Owner y Scrum Master, guiando a un equipo de desarrollo simulado por una IA a lo largo de un sprint completo, desde la planificación hasta la retrospectiva.

---

## 🚀 Tabla de Contenidos
- [Visión General](#-visión-general)
- [✨ Características Principales](#-características-principales)
- [🔧 Cómo Funciona: Fases de la Simulación](#-cómo-funciona-fases-de-la-simulación)
- [🛠️ Primeros Pasos](#️-primeros-pasos)
  - [Prerrequisitos](#prerrequisitos)
  - [Instalación](#instalación)
  - [Configuración](#configuración)
- [▶️ Cómo Ejecutar la Aplicación](#️-cómo-ejecutar-la-aplicación)
- [📂 Estructura del Código](#-estructura-del-código)
- [🤝 Contribuciones](#-contribuciones)

---

## 📖 Visión General

El objetivo principal de este proyecto es ofrecer una experiencia de aprendizaje práctica sobre el marco de trabajo SCRUM. El simulador abstrae la complejidad del desarrollo de software y se enfoca en los eventos, artefactos y roles de SCRUM. La interacción con una IA generativa añade un elemento de imprevisibilidad y realismo, simulando los desafíos y éxitos que un equipo puede encontrar en un sprint real.

---

## ✨ Características Principales

*   **Generación Dinámica de Proyectos:** Simplemente describe una idea de producto y la IA, actuando como un Product Owner, generará un Product Backlog completo con Historias de Usuario, descripciones y estimaciones en puntos.
*   **Planificación de Sprint Interactiva:** Selecciona qué Historias de Usuario incluir en el sprint, define la capacidad de tu equipo y establece un Sprint Goal claro y conciso.
*   **Ejecución de Sprint Simulada:** Avanza día a día a través de un sprint de 10 días. Gestiona el estado de las tareas (Pendiente, En Progreso, Hecho) y observa el progreso.
*   **Eventos Aleatorios Impulsados por IA:** Cada día, la IA genera un evento de sprint (un bloqueo, un descubrimiento, un éxito del equipo, etc.), simulando las dinámicas de un Daily Standup y forzándote a adaptarte.
*   **Sprint Review y Retrospective con Análisis de IA:** Al final del sprint, la IA analiza el rendimiento y genera:
    *   Un **resumen de Sprint Review** profesional para los stakeholders.
    *   **Insights accionables para la Sprint Retrospective**, identificando qué fue bien, qué se puede mejorar y sugiriendo acciones concretas (Kaizen).
*   **Interfaz Gráfica Intuitiva:** Construido con Streamlit para una experiencia de usuario limpia y fácil de usar, con un panel de control para guiarte a través del proceso.

---

## 🔧 Cómo Funciona: Fases de la Simulación

La aplicación te guiará paso a paso a través de las siguientes fases:

### **Fase 0: Definición del Proyecto**
1.  **Describe tu Idea:** Comienzas proporcionando una descripción en lenguaje natural de un producto o proyecto.
2.  **Generación del Product Backlog:** La IA de Google Gemini analiza tu idea y crea una lista de Historias de Usuario con formato estándar (`Como [rol], quiero [acción], para [beneficio]`), `id`, `título` y `puntos` de estimación (usando la secuencia Fibonacci).

### **Fase 1: Sprint Planning**
1.  **Selecciona Historias:** Revisa el Product Backlog y selecciona las historias que el equipo abordará en el sprint.
2.  **Define la Capacidad:** Ajusta un control deslizante para establecer la capacidad total del equipo en puntos para el sprint. La aplicación te advertirá si te sobrecomprometes.
3.  **Establece el Sprint Goal:** Escribe un objetivo claro y unificador para el sprint.
4.  **Inicia el Sprint:** Con todo listo, un clic lanza oficialmente el sprint.

### **Fase 2: Ejecución del Sprint**
1.  **Tablero de Progreso:** Visualiza el Sprint Backlog y actualiza el estado de cada historia a medida que el equipo "trabaja" en ellas.
2.  **Avanza Día a Día:** Cada vez que avanzas un día, la IA genera un nuevo evento que se añade al registro del "Daily Standup". Estos eventos pueden ser positivos o negativos, afectando el flujo de trabajo.
3.  **Monitorización:** Observa el progreso en tiempo real a través de una barra de progreso y métricas de puntos completados.

### **Fase 3: Sprint Review y Retrospectiva**
1.  **Sprint Review:** Al finalizar los 10 días, la IA genera un informe detallado que evalúa el cumplimiento del Sprint Goal, el valor entregado y los desafíos encontrados, perfecto para presentar a los stakeholders.
2.  **Sprint Retrospective:** La IA actúa como un Agile Coach, analizando todo el sprint para identificar éxitos, áreas de mejora y proponer una acción de mejora (Kaizen) específica y accionable para el próximo ciclo.

---

## 🛠️ Primeros Pasos

Sigue estos pasos para poner en marcha el simulador en tu máquina local.

### Prerrequisitos
Asegúrate de tener Python 3.8 o superior instalado en tu sistema.

### Instalación
1.  **Descomprime el Archivo:** Descomprime el archivo `.zip` que descargaste de Udemy en una carpeta de tu elección. Esto creará una carpeta con el código fuente del proyecto.

2.  **Abre una Terminal:** Abre tu terminal o línea de comandos (como PowerShell en Windows o Terminal en macOS/Linux).

3.  **Navega a la Carpeta del Proyecto:** Usa el comando `cd` para moverte al directorio que acabas de descomprimir.
    ```bash
    # Ejemplo:
    cd ruta/a/la/carpeta/scrum-simulator-main
    ```

4.  **Crea un Entorno Virtual (Recomendado):** Esto aísla las dependencias del proyecto.
    ```bash
    python -m venv venv
    ```

5.  **Activa el Entorno Virtual:**
    *   **En Windows:**
        ```bash
        venv\Scripts\activate
        ```
    *   **En macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

6.  **Instala las Dependencias:**
    El código requiere varias librerías de Python. Instálalas usando pip:
    ```bash
    pip install -r requirements.txt
    ```

### Configuración
1.  **Obtén tu clave de API de Gemini:**
    *   Ve a [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Haz clic en "Create API key" para generar una nueva clave.

2.  **Crea el archivo `.env`:**
    *   Dentro de la carpeta del proyecto, crea un nuevo archivo llamado `.env`.
    *   Abre el archivo `.env` con un editor de texto y añade la siguiente línea, reemplazando `TU_CLAVE_DE_API_AQUI` con la clave que acabas de obtener:
    ```
    GEMINI_API_KEY="TU_CLAVE_DE_API_AQUI"
    ```

---

## ▶️ Cómo Ejecutar la Aplicación

Una vez que hayas completado la instalación y configuración, y con el entorno virtual todavía activado, ejecuta el siguiente comando en tu terminal:

```bash
streamlit run scrum_simulator.py
```

**Tu navegador web se abrirá automáticamente en una nueva pestaña con la aplicación lista para usar. ¡A disfrutar de la simulación!**