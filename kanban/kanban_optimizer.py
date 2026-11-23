import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Kanban Flow Optimizer", page_icon="🌊")

# --- CARGA DE CLAVES Y CONFIGURACIÓN DE MODELOS ---
load_dotenv()
API_PROVIDERS = {
    "Gemini": {"api_key": os.getenv("GEMINI_API_KEY"), "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"]},
    "Groq": {"api_key": os.getenv("GROQ_API_KEY"), "models": ["openai/gpt-oss-120b", "meta-llama/llama-4-maverick-17b-128e-instruct", "deepseek-r1-distill-llama-70b"]},
    "OpenRouter": {"api_key": os.getenv("OPENROUTER_API_KEY"), "models": ["deepseek/deepseek-r1-0528:free", "deepseek/deepseek-chat-v3.1:free", "qwen/qwen3-coder:free", "moonshotai/kimi-k2:free"]}
}

# --- FUNCIÓN DE GENERACIÓN DE CONTENIDO UNIFICADA ---
def generar_contenido_ia(provider, model, system_prompt, user_prompt):
    config = API_PROVIDERS.get(provider)
    if not config or not config["api_key"]:
        st.error(f"🚨 Clave de API para {provider} no encontrada. Configúrala en tu archivo .env.")
        return None
    try:
        if provider == "Gemini":
            genai.configure(api_key=config["api_key"])
            gemini_model = genai.GenerativeModel(model_name=model, system_instruction=system_prompt)
            response = gemini_model.generate_content(user_prompt)
            return response.text
        else:
            client_config = {"base_url": "https://api.groq.com/openai/v1"} if provider == "Groq" else {"base_url": "https://openrouter.ai/api/v1"}
            client = OpenAI(api_key=config["api_key"], **client_config)
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                model=model, temperature=0.7)
            return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error con la API de {provider}: {e}")
        return None

# --- LÓGICA DE SIMULACIÓN KANBAN REDISEÑADA ---
def run_simulation(num_tasks, team_size, wip_limits, days_to_simulate):
    columns = ["Backlog", "Análisis", "Desarrollo", "Pruebas", "Hecho"]
    
    # Complejidad de cada fase (días de trabajo requeridos)
    phase_work = {
        'Análisis': 3,
        'Desarrollo': 5,
        'Pruebas': 2
    }
    
    # Inicializar tareas - TODAS comienzan entrando al sistema el día 0
    tasks = []
    for i in range(num_tasks):
        tasks.append({
            'id': i,
            'column': 'Ready',  # Estado especial: listas para entrar
            'work_done': 0,
            'entry_day': 0,  # Día en que llegaron al sistema
            'analysis_start': None,
            'done_day': None
        })
    
    board = {col: [] for col in columns}
    ready_queue = list(range(num_tasks))  # Cola de tareas listas para entrar
    
    cfd_data = []
    
    for day in range(1, days_to_simulate + 1):
        # FASE 1: PULL - Traer tareas nuevas al sistema
        # Con WIP ilimitado: entran todas inmediatamente
        # Con WIP limitado: solo las que quepan
        while len(board['Análisis']) < wip_limits.get('Análisis', 999) and ready_queue:
            task_id = ready_queue.pop(0)
            board['Análisis'].append(task_id)
            task = tasks[task_id]
            task['column'] = 'Análisis'
            task['analysis_start'] = day
            task['work_done'] = 0
        
        # FASE 2: TRABAJO - Asignar esfuerzo del equipo
        workers_available = team_size
        
        # Priorizar columnas de derecha a izquierda
        for col in ["Pruebas", "Desarrollo", "Análisis"]:
            if not board[col] or workers_available <= 0:
                continue
            
            # CLAVE: Dividir trabajadores entre tareas de esta columna
            # Con WIP alto (muchas tareas), cada tarea avanza lento
            # Con WIP bajo (pocas tareas), cada tarea avanza rápido
            tasks_in_col = len(board[col])
            effort_per_task = workers_available / tasks_in_col
            
            for task_id in board[col]:
                task = tasks[task_id]
                task['work_done'] += effort_per_task
        
        # FASE 3: FLUJO - Mover tareas que completaron su fase
        # Hacer esto de derecha a izquierda para evitar bloqueos
        
        # Pruebas → Hecho
        completed_in_pruebas = [tid for tid in board['Pruebas'] 
                                if tasks[tid]['work_done'] >= phase_work['Pruebas']]
        for task_id in completed_in_pruebas:
            board['Pruebas'].remove(task_id)
            board['Hecho'].append(task_id)
            tasks[task_id]['column'] = 'Hecho'
            tasks[task_id]['done_day'] = day
        
        # Desarrollo → Pruebas
        completed_in_desarrollo = [tid for tid in board['Desarrollo'] 
                                   if tasks[tid]['work_done'] >= phase_work['Desarrollo']]
        for task_id in completed_in_desarrollo:
            if len(board['Pruebas']) < wip_limits.get('Pruebas', 999):
                board['Desarrollo'].remove(task_id)
                board['Pruebas'].append(task_id)
                tasks[task_id]['column'] = 'Pruebas'
                tasks[task_id]['work_done'] = 0
        
        # Análisis → Desarrollo
        completed_in_analisis = [tid for tid in board['Análisis'] 
                                 if tasks[tid]['work_done'] >= phase_work['Análisis']]
        for task_id in completed_in_analisis:
            if len(board['Desarrollo']) < wip_limits.get('Desarrollo', 999):
                board['Análisis'].remove(task_id)
                board['Desarrollo'].append(task_id)
                tasks[task_id]['column'] = 'Desarrollo'
                tasks[task_id]['work_done'] = 0
        
        # Backlog se calcula como tareas que AÚN NO han entrado
        board['Backlog'] = ready_queue.copy()
        
        # FASE 4: Registrar CFD
        cfd_data.append({
            'Día': day,
            'Backlog': len(board['Backlog']),
            'Análisis': len(board['Análisis']),
            'Desarrollo': len(board['Desarrollo']),
            'Pruebas': len(board['Pruebas']),
            'Hecho': len(board['Hecho']),
        })
    
    cfd_df = pd.DataFrame(cfd_data)
    
    # CALCULAR MÉTRICAS
    completed_tasks = [t for t in tasks if t['done_day'] is not None]
    throughput = len(completed_tasks)
    
    lead_times = []
    cycle_times = []
    
    for t in completed_tasks:
        # Lead Time = desde entry (día 0) hasta done
        lead_time = t['done_day'] - t['entry_day']
        lead_times.append(lead_time)
        
        # Cycle Time = desde que empezó análisis hasta done
        if t['analysis_start'] is not None:
            cycle_time = t['done_day'] - t['analysis_start']
            cycle_times.append(cycle_time)
    
    # WIP promedio (excluyendo Backlog y Hecho)
    wip_avg = {
        'Análisis': cfd_df['Análisis'].mean(),
        'Desarrollo': cfd_df['Desarrollo'].mean(),
        'Pruebas': cfd_df['Pruebas'].mean(),
        'Total WIP': (cfd_df['Análisis'] + cfd_df['Desarrollo'] + cfd_df['Pruebas']).mean()
    }
    
    metrics = {
        "throughput": throughput,
        "avg_lead_time": np.mean(lead_times) if lead_times else 0,
        "avg_cycle_time": np.mean(cycle_times) if cycle_times else 0,
        "wip_avg": wip_avg,
        "throughput_per_day": throughput / days_to_simulate if days_to_simulate > 0 else 0
    }
    
    lead_time_df = pd.DataFrame({
        'Lead Time (días)': lead_times, 
        'Cycle Time (días)': cycle_times,
        'Tarea': range(len(lead_times))
    })
    
    return metrics, cfd_df, lead_time_df

# --- INTERFAZ DE USUARIO ---
st.title("🌊 Kanban Flow Optimizer")
st.markdown("**Experimenta cómo los límites de WIP impactan el rendimiento de tu equipo.**")
st.markdown("_Demuestra la Ley de Little: Lead Time = WIP / Throughput_")

if 'results' not in st.session_state:
    st.session_state.results = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Parámetros de Simulación")
    
    num_tasks = st.slider("Número de Tareas a Simular", 20, 200, 100)
    team_size = st.slider("Miembros del Equipo", 1, 20, 8)
    days_to_simulate = st.slider("Días a Simular", 20, 200, 150)
    
    st.markdown("---")
    st.subheader("Límites de Work In Progress (WIP)")
    
    use_wip = st.checkbox("Activar Límites de WIP", value=True)
    
    if use_wip:
        wip_limits = {
            'Análisis': st.number_input("WIP - Análisis", min_value=1, max_value=50, value=4),
            'Desarrollo': st.number_input("WIP - Desarrollo", min_value=1, max_value=50, value=5),
            'Pruebas': st.number_input("WIP - Pruebas", min_value=1, max_value=50, value=3)
        }
        final_wip_limits = wip_limits
        st.success(f"✅ WIP Total: {sum(wip_limits.values())} tareas")
    else:
        st.warning("⚠️ **SIN límites WIP** = Sistema PUSH")
        st.error("Esto causará dispersión de esfuerzo")
        final_wip_limits = {'Análisis': 999, 'Desarrollo': 999, 'Pruebas': 999}
    
    if st.button("🚀 Ejecutar Simulación", type="primary", use_container_width=True):
        with st.spinner("⏳ Simulando el flujo de trabajo..."):
            st.session_state.results = run_simulation(num_tasks, team_size, final_wip_limits, days_to_simulate)
            st.session_state.last_params = {
                "WIP Activado": use_wip, 
                "Límites WIP": final_wip_limits if use_wip else "Sin límites (999/999/999)", 
                "Tareas": num_tasks, 
                "Equipo": team_size,
                "Días": days_to_simulate
            }
    
    st.markdown("---")
    st.header("🤖 Coach de IA")
    providers_con_key = [p for p, c in API_PROVIDERS.items() if c["api_key"]]
    if providers_con_key:
        selected_provider = st.selectbox("Proveedor de IA:", providers_con_key)
        selected_model = st.selectbox("Modelo:", API_PROVIDERS[selected_provider]["models"])
    else:
        st.warning("⚠️ Configura una API Key para usar el Coach")

# --- ÁREA PRINCIPAL ---
if st.session_state.results:
    metrics, cfd_df, lead_time_df = st.session_state.results
    
    st.header("📊 Resultados de la Simulación")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Throughput", f"{metrics['throughput']} tareas", 
                f"{metrics['throughput_per_day']:.2f} por día")
    col2.metric("⏳ Lead Time", f"{metrics['avg_lead_time']:.1f} días",
                help="Tiempo total desde que la tarea entra al sistema")
    col3.metric("⚙️ Cycle Time", f"{metrics['avg_cycle_time']:.1f} días",
                help="Tiempo desde que empieza a trabajarse hasta terminar")
    col4.metric("📦 WIP Promedio", f"{metrics['wip_avg']['Total WIP']:.1f} tareas",
                help="Work In Progress promedio (excluyendo Backlog)")
    
    # Verificación Ley de Little
    if metrics['throughput_per_day'] > 0:
        little_law_ct = metrics['wip_avg']['Total WIP'] / metrics['throughput_per_day']
        error = abs(little_law_ct - metrics['avg_cycle_time']) / metrics['avg_cycle_time'] * 100 if metrics['avg_cycle_time'] > 0 else 0
        st.info(f"🔬 **Verificación Ley de Little:** Cycle Time teórico = {little_law_ct:.1f} días | Cycle Time real = {metrics['avg_cycle_time']:.1f} días | Error: {error:.1f}%")
    
    st.markdown("---")
    
    tab_cfd, tab_scatter, tab_ai, tab_data = st.tabs(["📈 CFD", "⏱️ Scatter Plot", "🤖 Análisis IA", "📋 Datos"])
    
    with tab_cfd:
        st.subheader("Diagrama de Flujo Acumulativo (CFD)")
        fig_cfd = go.Figure()
        columns_to_plot = ['Hecho', 'Pruebas', 'Desarrollo', 'Análisis', 'Backlog']
        colors = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12', '#95a5a6']
        
        for col, color in zip(columns_to_plot, colors):
            fig_cfd.add_trace(go.Scatter(
                x=cfd_df['Día'], 
                y=cfd_df[col], 
                hoverinfo='x+y+name', 
                mode='lines', 
                stackgroup='one', 
                name=col,
                line=dict(width=0.5, color=color),
                fillcolor=color
            ))
        
        fig_cfd.update_layout(
            title="Flujo de Trabajo a lo largo del Tiempo",
            xaxis_title="Día",
            yaxis_title="Número de Tareas Acumuladas",
            hovermode='x unified',
            height=500
        )
        st.plotly_chart(fig_cfd, use_container_width=True)
        
        st.info("📊 **Cómo interpretar:** Bandas anchas = Acumulación. Bandas delgadas paralelas = Flujo saludable.")
    
    with tab_scatter:
        st.subheader("Gráfico de Dispersión: Lead Time vs Cycle Time")
        
        fig_scatter = go.Figure()
        
        fig_scatter.add_trace(go.Scatter(
            x=lead_time_df.index, 
            y=lead_time_df['Lead Time (días)'], 
            mode='markers',
            name='Lead Time',
            marker=dict(size=8, color='#e74c3c', opacity=0.6)
        ))
        
        fig_scatter.add_trace(go.Scatter(
            x=lead_time_df.index, 
            y=lead_time_df['Cycle Time (días)'], 
            mode='markers',
            name='Cycle Time',
            marker=dict(size=8, color='#3498db', opacity=0.6)
        ))
        
        if len(lead_time_df) > 0:
            fig_scatter.add_hline(
                y=metrics['avg_lead_time'], 
                line_dash="dash", 
                line_color="#e74c3c",
                annotation_text=f"Lead Time: {metrics['avg_lead_time']:.1f}d"
            )
            fig_scatter.add_hline(
                y=metrics['avg_cycle_time'], 
                line_dash="dash", 
                line_color="#3498db",
                annotation_text=f"Cycle Time: {metrics['avg_cycle_time']:.1f}d"
            )
        
        fig_scatter.update_layout(
            title="Distribución de Tiempos por Tarea",
            xaxis_title="Tarea Completada",
            yaxis_title="Tiempo (días)",
            height=500
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.info("📊 **Interpretar:** Puntos bajos = Rápido. Puntos agrupados = Predecible.")
    
    with tab_ai:
        st.subheader("Análisis del Coach de IA")
        if st.button("🤖 Analizar con IA", use_container_width=True):
            if not providers_con_key:
                st.error("❌ No hay proveedor de IA configurado.")
            else:
                system_prompt = """Eres un Agile Coach experto en Lean, Kanban y Teoría de las Restricciones. 
                Analiza resultados y conecta siempre con la Ley de Little. Sé constructivo."""
                
                user_prompt = f"""
Analiza esta simulación:

PARÁMETROS: {json.dumps(st.session_state.last_params, indent=2)}

MÉTRICAS:
- Throughput: {metrics['throughput']} ({metrics['throughput_per_day']:.2f}/día)
- Lead Time: {metrics['avg_lead_time']:.1f} días
- Cycle Time: {metrics['avg_cycle_time']:.1f} días
- WIP: {metrics['wip_avg']['Total WIP']:.1f} tareas

CFD Inicio:
{cfd_df.head().to_string()}

CFD Fin:
{cfd_df.tail().to_string()}

Responde en 3 secciones:
1. DIAGNÓSTICO: ¿Salud del sistema? ¿Cuellos de botella?
2. LEY DE LITTLE: ¿Cómo impactó el WIP al Cycle Time?
3. RECOMENDACIÓN: Un cambio específico en WIP.
"""
                
                with st.spinner(f"🤖 Analizando..."):
                    analysis = generar_contenido_ia(selected_provider, selected_model, system_prompt, user_prompt)
                    if analysis:
                        st.markdown(analysis)
    
    with tab_data:
        st.subheader("Datos Crudos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**CFD:**")
            st.dataframe(cfd_df, height=300)
        
        with col2:
            st.write("**Tiempos:**")
            st.dataframe(lead_time_df, height=300)
        
        st.markdown("---")
        st.subheader("🧮 Calculadora para Estudiante")
        
        calc_col1, calc_col2 = st.columns(2)
        
        with calc_col1:
            st.code(f"""
Lead Time: {metrics['avg_lead_time']:.2f} días
Cycle Time: {metrics['avg_cycle_time']:.2f} días
Throughput: {metrics['throughput']} tareas
Throughput/día: {metrics['throughput_per_day']:.3f}
WIP Promedio: {metrics['wip_avg']['Total WIP']:.2f}
            """, language="text")
        
        with calc_col2:
            if metrics['throughput_per_day'] > 0:
                ct_teorico = metrics['wip_avg']['Total WIP'] / metrics['throughput_per_day']
                error = abs(ct_teorico - metrics['avg_cycle_time']) / metrics['avg_cycle_time'] * 100 if metrics['avg_cycle_time'] > 0 else 0
                st.code(f"""
Ley de Little:
CT teórico = WIP / Throughput
= {metrics['wip_avg']['Total WIP']:.2f} / {metrics['throughput_per_day']:.3f}
= {ct_teorico:.2f} días

CT real: {metrics['avg_cycle_time']:.2f} días
Error: {error:.1f}%
            """, language="text")

else:
    st.info("👈 **Configura y ejecuta** la simulación en la barra lateral")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔴 Experimento A: Sin WIP")
        st.markdown("""
        **Pasos:**
        1. ❌ Desmarca "Activar Límites de WIP"
        2. ⚙️ 100 tareas, 8 miembros, 150 días
        3. 🚀 Ejecutar Simulación
        4. 📝 Anota el **Lead Time**
        
        **Esperado:**
        - Lead Time: ~80-100 días
        - WIP alto: ~40-60 tareas
        - CFD: Bandas muy anchas
        - Dispersión alta
        """)
    
    with col2:
        st.subheader("🟢 Experimento B: Con WIP")
        st.markdown("""
        **Pasos:**
        1. ✅ Marca "Activar Límites de WIP"
        2. ⚙️ WIP: 4/5/3 (Análisis/Desarrollo/Pruebas)
        3. 🚀 Ejecutar Simulación
        4. 📝 Anota el **Lead Time**
        
        **Esperado:**
        - Lead Time: ~25-35 días
        - WIP bajo: ~10-12 tareas
        - CFD: Bandas delgadas
        - Dispersión baja
        """)
    
    st.markdown("---")
    st.success("🎯 **Meta:** Reducir Lead Time un 60-70% con límites WIP")
    
    st.markdown("---")
    st.subheader("📐 Fórmula para tu Tarea")
    st.latex(r"\text{Mejora (\%)} = \frac{\text{Lead Time}_A - \text{Lead Time}_B}{\text{Lead Time}_A} \times 100")
    
    st.markdown("""
    **Ejemplo:**
    - Lead Time A (sin WIP) = 90 días
    - Lead Time B (con WIP) = 28 días
    - Mejora = (90 - 28) / 90 × 100 = **68.9%**
    """)