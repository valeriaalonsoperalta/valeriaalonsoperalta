# scrum_simulator.py
import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Simulador de Equipo SCRUM",
    page_icon="🧑‍💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CARGA DE CLAVES Y CONFIGURACIÓN DEL MODELO DE IA ---
try:
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        st.error("🚨 Clave de API para Gemini no encontrada. Por favor, crea un archivo .env y añade tu GEMINI_API_KEY.")
        st.stop()

    genai.configure(api_key=GEMINI_API_KEY)

except Exception as e:
    st.error(f"Error al configurar la API. Asegúrate de que tu archivo .env está correcto. Detalle: {e}")
    st.stop()

# --- FUNCIÓN DE GENERACIÓN DE CONTENIDO UNIFICADA ---
def generar_contenido_ia(system_prompt, user_prompt, is_json=False):
    """
    Llama a la API de Gemini para generar contenido.
    Maneja la configuración de la respuesta para JSON si es necesario.
    """
    try:
        # Configura el tipo de respuesta esperada (MIME type)
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json" if is_json else "text/plain"
        )
        
        # Inicializa el modelo con la instrucción del sistema
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",  # Usamos un modelo capaz para asegurar la calidad de la simulación
            system_instruction=system_prompt,
            generation_config=generation_config
        )
        
        # Genera el contenido
        response = model.generate_content(user_prompt)
        return response.text
    except Exception as e:
        # Muestra un error detallado si la llamada a la API falla
        st.error(f"Ha ocurrido un error con la API de Gemini: {e}")
        return None

# --- INICIALIZACIÓN DEL ESTADO DE LA SIMULACIÓN ---
# Streamlit guarda el estado de la aplicación en este diccionario.
# Es crucial para mantener los datos de la simulación entre interacciones del usuario.
if 'sprint_iniciado' not in st.session_state:
    st.session_state.sprint_iniciado = False
    st.session_state.proyecto_definido = False
    st.session_state.product_backlog = []
    st.session_state.sprint_backlog = []
    st.session_state.dia_actual = 0
    st.session_state.eventos_sprint = []
    st.session_state.capacidad_equipo = 20
    st.session_state.sprint_goal = ""

# --- UI DE LA BARRA LATERAL (PANEL DE CONTROL) ---
with st.sidebar:
    st.title("🔧 Panel de Simulación")
    st.markdown("Controla el flujo de tu Sprint simulado.")
    
    # Botón para reiniciar la simulación borrando todo el estado
    if st.button("🔄 Reiniciar Simulación Completa", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("---")
    
    # Guía rápida para el estudiante
    st.title("📘 Guía del Laboratorio")
    st.markdown("""
    ¡Bienvenido al **Simulador de Equipo SCRUM**! Aquí, tomarás el rol de Scrum Master y Product Owner para guiar a un equipo de IA a través de un sprint.
    
    **Fases de la Simulación:**
    1.  **Define el Proyecto:** Dale a la IA un contexto.
    2.  **Crea el Product Backlog:** La IA generará las Historias de Usuario.
    3.  **Planifica el Sprint:** Selecciona historias y define el objetivo.
    4.  **Ejecuta el Sprint:** Avanza día a día, enfrentando eventos aleatorios.
    5.  **Revisa y Mejora:** Analiza los resultados en la Revisión y Retrospectiva.
    """)
    st.markdown("---")
    
    # Indicadores de estado clave
    st.info(f"""
    **Sprint:** {"En curso" if st.session_state.sprint_iniciado else "No iniciado"}
    
    **Día del Sprint:** {st.session_state.dia_actual} / 10
    """)

# --- CUERPO PRINCIPAL DE LA APLICACIÓN ---
st.title("🧑‍💻 Simulador de Equipo SCRUM")
st.markdown("Aprende a gestionar un equipo SCRUM tomando decisiones que impactarán el resultado de un sprint. ¡Tu equipo de IA te espera!")
st.markdown("---")

# La lógica de la aplicación se divide en fases controladas por el estado de la sesión
if not st.session_state.proyecto_definido:
    # ========== FASE 0: DEFINICIÓN DEL PROYECTO ==========
    st.header("🏁 Fase 0: Define tu Proyecto")
    st.info("Todo gran sprint comienza con una visión clara. Describe el producto que tu equipo de IA construirá.")
    
    idea_proyecto = st.text_area(
        "Describe la idea del producto:", 
        "Una aplicación móvil para intercambiar libros usados entre vecinos de un mismo barrio, con perfiles de usuario, catálogo de libros y un chat interno.", 
        height=100
    )
    
    if st.button("Definir Proyecto y Crear Backlog", type="primary"):
        if idea_proyecto:
            # Prompt para que la IA actúe como Product Owner y cree el backlog
            system_prompt = "Eres un Product Owner experto. Tu tarea es analizar una idea de producto y descomponerla en un Product Backlog inicial con Historias de Usuario (HU). Debes devolver el resultado únicamente en formato JSON."
            user_prompt = f"""
            Analiza la siguiente idea de producto y genera un Product Backlog con entre 8 y 12 Historias de Usuario.
            Cada HU debe tener los siguientes campos en el JSON: 'id' (ej: HU-01), 'titulo' (un nombre corto y descriptivo), 'descripcion' (en formato 'Como [rol], quiero [acción], para [beneficio]'), y 'puntos' (un valor de la secuencia Fibonacci: 1, 2, 3, 5, 8, 13).
            Asegúrate de que las historias cubran las funcionalidades clave descritas en la idea.

            Idea de Producto: "{idea_proyecto}"
            """
            with st.spinner("🧠 El Product Owner de IA está refinando la idea y creando el Product Backlog..."):
                backlog_json_str = generar_contenido_ia(system_prompt, user_prompt, is_json=True)
                if backlog_json_str:
                    try:
                        # Limpiar la respuesta JSON si viene con bloques de código Markdown
                        cleaned_json = backlog_json_str.strip().replace("```json", "").replace("```", "")
                        st.session_state.product_backlog = json.loads(cleaned_json)
                        st.session_state.proyecto_definido = True
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("La IA generó una respuesta JSON inválida. Por favor, inténtalo de nuevo.")
        else:
            st.warning("Por favor, describe la idea del proyecto para continuar.")

elif not st.session_state.sprint_iniciado:
    # ========== FASE 1: SPRINT PLANNING ==========
    st.header("🗓️ Fase 1: Sprint Planning")
    st.info("Es hora de planificar el sprint. Como Product Owner, selecciona las Historias de Usuario del Product Backlog. Como Scrum Master, ayuda al equipo a no sobrecomprometerse.")
    
    st.subheader("Product Backlog (Priorizado)")
    
    if not st.session_state.product_backlog:
        st.warning("No hay elementos en el Product Backlog. Por favor, reinicia la simulación.")
    else:
        selected_stories_indices = []
        total_puntos = 0
        
        st.write("Selecciona las HUs para incluir en el Sprint:")
        # Mostrar cada historia con una casilla para seleccionarla
        for i, story in enumerate(st.session_state.product_backlog):
            if st.checkbox(f"**{story['id']}: {story['titulo']}** ({story['puntos']} puntos) - *{story['descripcion']}*", key=f"cb_{i}"):
                selected_stories_indices.append(i)
                total_puntos += story['puntos']
        
        st.session_state.capacidad_equipo = st.slider("Define la capacidad del equipo para este sprint (en puntos)", 5, 50, 20)
        st.metric("Puntos Seleccionados para el Sprint", f"{total_puntos} / {st.session_state.capacidad_equipo}")
        
        if total_puntos > st.session_state.capacidad_equipo:
            st.warning("Has seleccionado más puntos de los que el equipo puede manejar. Esto aumenta el riesgo de no cumplir el Sprint Goal.")
            
        st.session_state.sprint_goal = st.text_input("Define el Objetivo del Sprint (Sprint Goal):", "Al final del sprint, los usuarios podrán registrarse, iniciar sesión y ver una lista de libros publicados por otros.")
        
        if st.button("🚀 Iniciar Sprint", type="primary", use_container_width=True):
            if not selected_stories_indices:
                st.warning("Debes seleccionar al menos una Historia de Usuario para el sprint.")
            elif not st.session_state.sprint_goal:
                st.warning("El Objetivo del Sprint es crucial y no puede estar vacío.")
            else:
                # Mover las historias seleccionadas al Sprint Backlog
                st.session_state.sprint_backlog = [st.session_state.product_backlog[i] for i in selected_stories_indices]
                for story in st.session_state.sprint_backlog:
                    story['estado'] = 'Pendiente' # Estado inicial
                
                # Actualizar estado de la simulación
                st.session_state.sprint_iniciado = True
                st.session_state.dia_actual = 1
                st.session_state.eventos_sprint.append("Día 1: ¡El Sprint ha comenzado! El equipo está motivado y empieza a trabajar en las primeras tareas.")
                st.rerun()

else:
    # ========== FASE 2: EJECUCIÓN DEL SPRINT ==========
    st.header(f"🏃‍♂️ Fase 2: Ejecución del Sprint - Día {st.session_state.dia_actual}")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📋 Sprint Backlog y Progreso")
        progreso_puntos = 0
        # Muestra el tablero de tareas del sprint
        for story in st.session_state.sprint_backlog:
            estado_actual = story.get('estado', 'Pendiente')
            # Permite al usuario simular el avance del equipo
            nuevo_estado = st.radio(
                f"**{story['id']}: {story['titulo']}** ({story['puntos']} puntos)",
                ['Pendiente', 'En Progreso', 'Hecho'],
                index=['Pendiente', 'En Progreso', 'Hecho'].index(estado_actual),
                key=f"radio_{story['id']}",
                horizontal=True
            )
            story['estado'] = nuevo_estado
            if nuevo_estado == 'Hecho':
                progreso_puntos += story['puntos']
        
        total_puntos_sprint = sum(s['puntos'] for s in st.session_state.sprint_backlog)
        st.progress(progreso_puntos / total_puntos_sprint if total_puntos_sprint > 0 else 0)
        st.metric("Progreso del Sprint", f"{progreso_puntos} / {total_puntos_sprint} Puntos Completados")

    with col2:
        st.subheader("📣 Eventos del Sprint (Daily Standup Log)")
        # Muestra el log de eventos
        for evento in reversed(st.session_state.eventos_sprint):
            st.info(evento)

    if st.session_state.dia_actual < 10: # Duración del sprint simulado: 10 días
        if st.button("Avanzar al Siguiente Día ➡️", type="primary", use_container_width=True):
            st.session_state.dia_actual += 1
            
            # Prompt para generar un evento aleatorio
            system_prompt = "Eres un Scrum Master simulando el día a día de un sprint. Tu tarea es generar un evento realista que podría ocurrir. Devuelve el evento únicamente en formato JSON."
            user_prompt = f"""
            Simula un evento para el día {st.session_state.dia_actual} de un sprint de 10 días.
            El equipo está trabajando en un proyecto de una app de intercambio de libros.
            El progreso actual es de {progreso_puntos} de {total_puntos_sprint} puntos completados.
            Genera un evento que pueda ser un bloqueo, una oportunidad, un problema técnico, una duda del Product Owner, una colaboración exitosa o un logro del equipo.
            Hay un 25% de probabilidad de que el evento sea un bloqueo o un impedimento.
            El evento debe ser conciso y realista.

            Devuelve un JSON con una sola clave: "evento".
            Ejemplo 1: {{"evento": "¡Gran avance! El equipo resolvió un bug complejo en la HU-02 gracias al pair programming."}}
            Ejemplo 2: {{"evento": "¡BLOQUEO! La API de mapas para la geolocalización no funciona como se esperaba y está deteniendo el avance en la HU-05."}}
            """
            with st.spinner("⏳ Simulando el día de trabajo del equipo..."):
                evento_json_str = generar_contenido_ia(system_prompt, user_prompt, is_json=True)
                if evento_json_str:
                    try:
                        cleaned_json = evento_json_str.strip().replace("```json", "").replace("```", "")
                        evento_obj = json.loads(cleaned_json)
                        st.session_state.eventos_sprint.append(f"Día {st.session_state.dia_actual}: {evento_obj['evento']}")
                    except (json.JSONDecodeError, KeyError):
                        st.session_state.eventos_sprint.append(f"Día {st.session_state.dia_actual}: El equipo sigue trabajando sin mayores incidentes.")
            st.rerun()
    else:
        # ========== FASE 3: SPRINT REVIEW Y RETROSPECTIVE ==========
        st.header("🏁 Fase 3: Fin del Sprint - Review y Retrospective")
        st.success("¡Has llegado al final del sprint! Es hora de inspeccionar el incremento y adaptar el proceso.")

        tab_review, tab_retro = st.tabs(["🔎 Sprint Review", "🌱 Sprint Retrospective"])

        # Preparar el contexto para los análisis de la IA
        puntos_completados = sum(s['puntos'] for s in st.session_state.sprint_backlog if s['estado'] == 'Hecho')
        puntos_totales = sum(s['puntos'] for s in st.session_state.sprint_backlog)
        historias_completadas = [f"{s['id']}: {s['titulo']}" for s in st.session_state.sprint_backlog if s['estado'] == 'Hecho']
        historias_no_completadas = [f"{s['id']}: {s['titulo']}" for s in st.session_state.sprint_backlog if s['estado'] != 'Hecho']
        eventos_str = "\n".join(f"- {e}" for e in st.session_state.eventos_sprint)
        
        with tab_review:
            st.subheader("Análisis de la Sprint Review")
            st.info("La IA actuará como Product Owner, analizando los resultados del sprint y generando un resumen para los stakeholders.")
            
            if st.button("Generar Resumen de Sprint Review", type="primary"):
                system_prompt = "Eres un Product Owner presentando los resultados de un sprint a los stakeholders. Tu tono es profesional, transparente y centrado en el valor de negocio entregado."
                user_prompt = f"""
                Analiza los siguientes datos del sprint y redacta un resumen conciso para la Sprint Review.
                - Objetivo del Sprint: "{st.session_state.sprint_goal}"
                - Puntos completados: {puntos_completados} de {puntos_totales}
                - Historias completadas: {', '.join(historias_completadas) if historias_completadas else "Ninguna"}
                - Historias no completadas: {', '.join(historias_no_completadas) if historias_no_completadas else "Ninguna"}
                - Resumen de eventos clave durante el sprint:
                {eventos_str}

                Elabora un texto que cubra los siguientes puntos:
                1. **Evaluación del Sprint Goal:** ¿Se cumplió el objetivo principal del sprint?
                2. **Valor Entregado:** Describe las nuevas capacidades que ahora tiene el producto gracias a las historias completadas. Traduce la jerga técnica a beneficios para el usuario.
                3. **Desafíos y Aprendizajes:** Menciona de forma constructiva los principales impedimentos y qué se aprendió de ellos.
                4. **Próximos Pasos:** Da una breve pincelada sobre la dirección del próximo sprint.
                """
                with st.spinner("🧠 La IA está preparando la presentación para los stakeholders..."):
                    review_summary = generar_contenido_ia(system_prompt, user_prompt)
                    if review_summary:
                        st.markdown(review_summary)

        with tab_retro:
            st.subheader("Análisis de la Sprint Retrospective")
            st.info("La IA actuará como un Agile Coach experimentado, analizando todo el sprint para sugerir puntos de mejora (Kaizen).")
            
            if st.button("Generar Insights de la Retrospectiva", type="primary"):
                system_prompt = "Eres un Agile Coach experto facilitando una Sprint Retrospective. Tu objetivo es identificar las causas raíz de los problemas y proponer acciones de mejora concretas y accionables."
                user_prompt = f"""
                Analiza el historial completo del siguiente sprint y genera insights para la retrospectiva del equipo.
                - Objetivo del Sprint: "{st.session_state.sprint_goal}"
                - Rendimiento: Se completaron {puntos_completados} de {puntos_totales} puntos comprometidos.
                - Historias no completadas: {len(historias_no_completadas)}
                - Historial de eventos del sprint:
                {eventos_str}

                Genera un análisis con tres secciones claras:
                1. **🎉 Qué fue bien:** Identifica los puntos fuertes, colaboraciones y éxitos del equipo que deberían celebrarse y mantenerse.
                2. **🤔 Qué se puede mejorar:** Señala los principales problemas, patrones negativos o impedimentos que afectaron el rendimiento o la moral del equipo. Busca la causa raíz.
                3. **💡 Acción de Mejora Sugerida (Kaizen):** Propón UNA acción de mejora específica, medible, alcanzable, relevante y con un plazo (SMART) que el equipo podría adoptar en el próximo sprint para abordar el principal problema identificado.
                """
                with st.spinner("🌱 La IA está buscando oportunidades de mejora continua..."):
                    retro_insights = generar_contenido_ia(system_prompt, user_prompt)
                    if retro_insights:
                        st.markdown(retro_insights)