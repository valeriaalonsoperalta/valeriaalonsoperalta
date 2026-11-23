# Suite de Gestión de Proyectos con IA

## 1. Introducción

Bienvenido a la Suite de Gestión de Proyectos con IA. Esta es una aplicación completa construida con Streamlit que te permite planificar, analizar y gestionar proyectos de manera integral. La herramienta utiliza el poder de los Grandes Modelos de Lenguaje (LLMs) para automatizar tareas complejas como la creación de la Estructura de Desglose de Trabajo (WBS), la redacción de documentos de proyecto y el análisis de riesgos.

Esta guía te llevará paso a paso a través del proceso de configuración e implementación de la aplicación en tu entorno local, partiendo de un archivo `.zip` con el código fuente.

## 2. Características Principales

*   **Generación de Proyectos por IA:** Describe tu proyecto en lenguaje natural y la IA generará un plan de tareas completo (WBS) en segundos.
*   **Múltiples Proveedores de IA:** Soporte para Gemini, Groq y OpenRouter, permitiéndote elegir el modelo que mejor se adapte a tus necesidades.
*   **Gestión de Tareas y WBS:** Edita, añade o elimina tareas en una tabla interactiva. Recalcula automáticamente las fechas y costes del proyecto.
*   **Análisis de Ruta Crítica:** Identifica las tareas críticas que impactan la duración total de tu proyecto.
*   **Diagrama de Gantt Interactivo:** Visualiza el cronograma del proyecto, las dependencias y la ruta crítica.
*   **Simulación Monte Carlo:** Estima la duración y el coste final del proyecto con análisis de probabilidad (P50, P80) para una toma de decisiones más informada.
*   **Tablero Kanban:** Gestiona el estado de las tareas de forma visual y arrastra tarjetas para actualizar su progreso (funcionalidad de mover mediante selector).
*   **Gestión de Riesgos e Incidencias:** Un módulo dedicado para registrar, seguir y mitigar los riesgos e incidencias del proyecto, con sugerencias de riesgos generadas por IA.
*   **Cálculo de Costes:** Define perfiles de recursos con costes por hora para obtener una estimación precisa del presupuesto.
*   **Nivelación de Recursos:** Ajusta el cronograma del proyecto basándose en la capacidad real de los recursos y calendarios laborales (festivos, fines de semana).
*   **Generación Automática de Documentos:** Crea documentos profesionales con un solo clic:
    *   Acta de Constitución del Proyecto
    *   Definición del Alcance
    *   Documento Funcional
    *   Historias de Usuario
    *   Informe de Simulación Monte Carlo
    *   Informe Completo del Proyecto (incluye EVA - Análisis de Valor Ganado)
*   **Autenticación de Usuarios:** Sistema de registro e inicio de sesión para gestionar proyectos de forma segura y separada por usuario.
*   **Persistencia de Datos:** Todos tus proyectos se guardan en una base de datos local SQLite para que puedas retomarlos en cualquier momento.
*   **Exportación Múltiple:** Exporta tus planes de proyecto a formatos estándar como Excel, JSON e iCalendar (.ics).

## 3. Prerrequisitos

Antes de comenzar, asegúrate de tener instalado **Python 3.8 o superior** en tu sistema. Puedes verificarlo abriendo una terminal o símbolo del sistema y ejecutando:

```bash
python --version
# o si tienes múltiples versiones de python:
python3 --version
```

## 4. Guía de Instalación y Configuración (Paso a Paso)

Sigue estos pasos para poner en marcha la aplicación.

### Paso 1: Descomprimir el Archivo del Proyecto

Comienza por descomprimir el archivo `.zip` que contiene el código fuente en una carpeta de tu elección. Al finalizar, tendrás una estructura de archivos similar a esta:

```
tu-carpeta-de-proyecto/
├── app.py
├── eva.py
├── risk_management.py
├── requirements.txt
├── .env
├── assets/
│   └── dragula.css
```

### Paso 2: Crear y Activar un Entorno Virtual

Es una buena práctica aislar las dependencias del proyecto en un entorno virtual.

1.  Abre una terminal o símbolo del sistema y navega hasta la carpeta donde descomprimiste los archivos.

    ```bash
    cd ruta/a/tu-carpeta-de-proyecto
    ```

2.  Crea el entorno virtual.

    ```bash
    python -m venv venv
    ```

3.  Activa el entorno virtual.
    *   **En Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **En macOS y Linux:**
        ```bash
        source venv/bin/activate
        ```

    Una vez activado, verás `(venv)` al principio de la línea de comandos.

### Paso 3: Instalar las Dependencias

Con el entorno virtual activado, instala todas las librerías necesarias utilizando el archivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

Este comando instalará Streamlit, Pandas, Plotly, las librerías de IA, y todo lo demás que la aplicación necesita para funcionar.

### Paso 4: Configurar las Claves API

La funcionalidad de IA de la aplicación depende de claves API de servicios externos.

1.  Abre el archivo `.env` con un editor de texto. Verás el siguiente contenido:

    ```env
        # Claves API para proveedores de IA
    # Pega tus claves de API aquí. Solo necesitas una para empezar, las otras son opcionales.

    # Obligatoria para los modelos de Google (incluyendo análisis de imagen)
    GEMINI_API_KEY=Tu_Clave_Aqui

    # Opcional: Para probar los modelos ultrarrápidos de Groq
    GROQ_API_KEY=Tu_Clave_Aqui

    # Opcional: Para probar una variedad de modelos de código abierto
    OPENROUTER_API_KEY=Tu_Clave_Aqui
    ```

2.  **Reemplaza las claves de ejemplo** con tus propias claves API. Debes obtenerlas de los siguientes sitios:
    *   **GEMINI\_API\_KEY:** Obtén tu clave desde [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   **GROQ\_API\_KEY:** Genera tu clave en la [consola de GroqCloud](https://console.groq.com/keys).
    *   **OPENROUTER\_API\_KEY:** Consigue tu clave en el [sitio de OpenRouter](https://openrouter.ai/keys).

3.  Guarda y cierra el archivo `.env`. La aplicación cargará estas claves automáticamente al iniciarse. **Nunca compartas este archivo con tus claves reales.**

## 5. Ejecutar la Aplicación

¡Ya está todo listo! Para iniciar la aplicación, ejecuta el siguiente comando en tu terminal (asegúrate de que el entorno virtual siga activado y estés en la carpeta del proyecto).

```bash
streamlit run app.py
```

Streamlit iniciará un servidor local y abrirá la aplicación automáticamente en tu navegador web. La primera pantalla que verás será la de inicio de sesión o registro.
**NOTA:** Si NO usa entorno virtual usa el siguiente comando para iniciar la aplicación en tu navegador web:

```bash
python -m streamlit run app.py
```
## 6. Cómo Usar la Aplicación

1.  **Registro y Acceso:** En la barra lateral, selecciona "Registrarse". Crea un nuevo usuario y una contraseña. Luego, inicia sesión con tus credenciales.
2.  **Configuración Inicial:**
    *   En la barra lateral, selecciona el **Proveedor de IA** y el **Modelo** que deseas utilizar.
    *   En la pestaña principal, despliega la sección "👤 Configuración de Perfiles y Costes" para definir los roles del proyecto y su coste por hora.
3.  **Generar un Nuevo Proyecto:**
    *   Ve a la pestaña **"📝 Definición y Generación"**.
    *   Asigna un **"Nombre del Proyecto Actual"** en la barra lateral. Este paso es **obligatorio**.
    *   Escribe una descripción detallada de tu proyecto en el área de texto o sube un documento (`.pdf`, `.txt`).
    *   Haz clic en el botón **"🚀 Generar Plan de Proyecto Completo"**. La IA creará el WBS y las subtareas.
4.  **Trabajar con el Proyecto:**
    *   Una vez generado, el proyecto se guarda automáticamente. Ve a la barra lateral y cárgalo desde el menú desplegable **"Cargar Proyecto Existente"**.
    *   **Pestaña "📋 Plan de Tareas (WBS)":** Revisa, edita y ajusta las tareas, duraciones, dependencias y recursos. Usa el botón "Recalcular" para actualizar el plan.
    *   **Pestaña "📌 Tablero Kanban":** Visualiza el flujo de trabajo y actualiza el estado de las tareas usando el selector en cada tarjeta.
    *   **Pestaña "⚠️ Riesgos e Incidencias":** Registra manualmente riesgos e incidencias, o usa la IA para que te sugiera riesgos potenciales basados en la descripción del proyecto.
    *   **Pestaña "📊 Análisis y Documentos":**
        *   Visualiza el **Diagrama de Gantt** con la ruta crítica.
        *   Ejecuta una **Simulación Monte Carlo** para analizar la viabilidad del cronograma y presupuesto.
        *   Genera todos los **documentos del proyecto** (Acta, Alcance, etc.) y **exporta** el plan a Excel, JSON o iCal.

## 7. Despliegue (Opcional)

Si deseas desplegar esta aplicación para que sea accesible online, la forma más sencilla es usar **Streamlit Community Cloud**.

1.  **Sube tu proyecto a GitHub:** Crea un repositorio en GitHub y sube todos los archivos del proyecto, **excepto el archivo `.env`**. Es una mala práctica de seguridad subir claves API a repositorios públicos.
2.  **Crea una cuenta en Streamlit:** Regístrate en [Streamlit Community Cloud](https://share.streamlit.io/).
3.  **Despliega la App:**
    *   Haz clic en "New app" y conecta tu cuenta de GitHub.
    *   Selecciona el repositorio y la rama donde se encuentra tu proyecto.
    *   El archivo principal es `app.py`.
4.  **Configura los "Secrets":** En lugar de usar un archivo `.env`, debes usar la gestión de secretos de Streamlit.
    *   En la configuración avanzada de tu app, ve a "Settings" > "Secrets".
    *   Añade tus claves API con el mismo formato que el archivo `.env`:

    ```toml
    # .streamlit/secrets.toml
    GEMINI_API_KEY="TU_CLAVE_DE_GEMINI"
    GROQ_API_KEY="TU_CLAVE_DE_GROQ"
    OPENROUTER_API_KEY="TU_CLAVE_DE_OPENROUTER"
    ```
5.  Guarda los secretos y despliega la aplicación. ¡Tu suite de gestión de proyectos estará ahora online

Por supuesto. Aquí tienes la sección adicional redactada en Markdown con un estilo formal y profesional, extendiendo las cláusulas de licencia y responsabilidad como solicitaste. Puedes añadir este bloque al final del archivo `Readme.md` que generé anteriormente.

---

## 8. Licencia y Limitación de Responsabilidad

Lea atentamente los siguientes términos y condiciones antes de descargar, instalar o utilizar este software.

### Aceptación de los Términos

Al descargar, instalar, copiar o utilizar la "Suite de Gestión de Proyectos con IA" (en adelante, "el Software"), usted (en adelante, "el Usuario") reconoce que ha leído, entendido y aceptado estar sujeto a los términos de esta licencia. Si no está de acuerdo con estos términos, no debe utilizar el Software de ninguna manera.

### Concesión de Licencia

El autor, **Ángel Arias**, le concede una licencia no exclusiva, intransferible y revocable para utilizar el Software únicamente para fines **personales**, **profesionales** (si puedes comercializar los proyectos generados con este Software), **educativos** o **de evaluación interna**.

### Sin Garantías (Software "TAL CUAL")

El Software se proporciona **"tal cual" (as is)**, sin garantía de ningún tipo, ya sea expresa, implícita o legal. El autor renuncia explícitamente a todas las garantías, incluyendo, entre otras, las garantías implícitas de **comerciabilidad**, **idoneidad para un propósito particular** y **no infracción** de derechos de terceros.

El autor no garantiza que las funciones contenidas en el Software cumplirán con los requisitos del Usuario, que el funcionamiento del Software será ininterrumpido o libre de errores, que los resultados obtenidos serán precisos o fiables, ni que los defectos en el Software serán corregidos.

### Limitación de Responsabilidad

Bajo ninguna circunstancia y bajo ninguna teoría legal, ya sea por agravio, contrato o de otra manera, el autor, **Ángel Arias**, será responsable ante el Usuario o cualquier otra persona por cualquier tipo de daño, ya sea directo, indirecto, especial, incidental, consecuente o punitivo, que surja del uso o la incapacidad de usar este Software.

Esto incluye, sin limitación, daños por:
*   Pérdida de beneficios o ingresos.
*   Interrupción del negocio.
*   Pérdida de datos, información, fondo de comercio o ahorros.
*   Costes de adquisición de bienes o servicios sustitutivos.
*   Cualquier otro perjuicio comercial, económico o personal.

Esta limitación de responsabilidad se aplicará incluso si se ha advertido al autor de la posibilidad de tales daños. El Usuario asume toda la responsabilidad y el riesgo por la selección y el uso de este Software, así como por los resultados obtenidos del mismo.

### Restricción de Uso Comercial

Queda estrictamente prohibido el uso de este Software, o de cualquiera de sus componentes, con fines comerciales. Se considera "uso comercial" cualquier utilización que genere directa o indirectamente ingresos, beneficios o cualquier tipo de remuneración. Esto incluye, sin limitación:

*   La reventa, alquiler o arrendamiento del Software.
*   Su integración total o parcial en un producto o servicio de pago.

Cualquier uso comercial requiere la obtención de un permiso explícito, previo y por escrito del autor, **Ángel Arias**. Para solicitar dicho permiso, se deberá contactar directamente con el autor. El autor se reserva el derecho de denegar dicho permiso a su entera discreción.

### Derechos de Propiedad Intelectual

Todos los derechos, títulos e intereses sobre el Software, incluyendo los derechos de autor y otros derechos de propiedad intelectual, son y seguirán siendo propiedad exclusiva del autor. Esta licencia no le otorga al Usuario ningún derecho de propiedad sobre el Software, sino únicamente un derecho limitado de uso de acuerdo con los términos aquí establecidos.