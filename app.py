# app.py
import os
import re
import io
import json
import sqlite3
import time 
from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import PyPDF2
import requests
import streamlit as st
import xlsxwriter
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from ics import Calendar, Event 
import eva
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

# =========================
# Cargar variables de entorno y configuración de IA
# =========================
load_dotenv()
GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY = os.getenv("GEMINI_API_KEY", ""), os.getenv("GROQ_API_KEY", ""), os.getenv("OPENROUTER_API_KEY", "")

API_PROVIDERS = {
    "Gemini": {"api_key": GEMINI_API_KEY, "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"], "url_template": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"},
    "Groq": {"api_key": GROQ_API_KEY, "models": ["openai/gpt-oss-120b", "meta-llama/llama-4-maverick-17b-128e-instruct", "deepseek-r1-distill-llama-70b"], "url_template": "https://api.groq.com/openai/v1/chat/completions"},
    "OpenRouter": {"api_key": OPENROUTER_API_KEY, "models": ["deepseek/deepseek-r1-0528:free", "deepseek/deepseek-chat-v3.1:free", "qwen/qwen3-coder:free", "moonshotai/kimi-k2:free"], "url_template": "https://openrouter.ai/api/v1/chat/completions"},
}

# =========================
# Prompts para la IA
# =========================
PROMPT_WBS_JSON = """Eres un Senior Project Manager experto. Genera una Estructura de Desglose de Trabajo (WBS) a partir del texto proporcionado y devuélvela en formato JSON.
REGLAS ESTRICTAS:
- Tu respuesta DEBE ser únicamente el bloque de código JSON. Sin texto introductorio, explicaciones ni comentarios.
- Cada tarea debe tener: "id", "nombre", "duracion_horas", "dependencias", y "perfil".
- El perfil debe ser elegido ÚNICAMENTE de la siguiente lista de perfiles válidos: {valid_profiles}. No inventes perfiles nuevos.
- Todo en castellano.
EJEMPLO: [{{"id": "1", "nombre": "Fase 1", "duracion_horas": 40, "dependencias": [], "perfil": "Project Manager"}}]
Texto de entrada:
{input_text}
"""
PROMPT_EXECUTIVE_SUMMARY = "Eres un Senior PM. Redacta un resumen ejecutivo profesional y conciso (150-200 palabras) en castellano para el siguiente plan de proyecto. Céntrate en objetivos, resultados, cronograma y presupuesto. Menciona la importancia de la ruta crítica. Datos:\n- Título: {project_title}\n- Duración: {duration} días\n- Costo: €{cost:,.2f}\n- Tareas Totales: {task_count}\n- Tareas Críticas: {critical_task_count}\n- Fases Clave:\n{task_list}"
PROMPT_SCOPE_STATEMENT = "Como Senior PM, genera una 'Declaración del Alcance del Proyecto' completa en castellano usando formato Markdown. **IMPORTANTE: No uses tablas de Markdown**, en su lugar, utiliza listas con viñetas y texto. Sé detallado. Basado en:\n- Descripción: {project_description}\n- Duración: {duration} días\n- Costo: €{cost:,.2f}\n- Hitos Clave:\n{milestones}"
PROMPT_PROJECT_CHARTER = "Como Senior PM, genera un 'Acta de Constitución del Proyecto' formal y completa en castellano usando formato Markdown. **IMPORTANTE: No uses tablas de Markdown**, en su lugar, utiliza listas con viñetas y texto. Sé detallado. Basado en:\n- Descripción: {project_description}\n- Duración: {duration} días\n- Costo: €{cost:,.2f}\n- Roles Clave: {roles}\n- Hitos Clave:\n{milestones}"
PROMPT_DETAILED_SUBTASKS = """Eres un experto en gestión de proyectos. Para CADA una de las siguientes tareas, desglósala en 3-5 subtareas concretas y accionables en castellano.
Sigue el formato EXACTO que se muestra a continuación, sin añadir texto introductorio, resúmenes ni ninguna otra cosa. Tu respuesta debe empezar directamente con la primera tarea.

Formato a seguir:
[ID_TAREA] Nombre de Tarea
- Subtarea 1
- Subtarea 2

Lista de Tareas:
{task_list_str}"""

PROMPT_FUNCTIONAL_DOC = """Como experto Analista Funcional, genera un **'Documento Funcional' (DF) completo y detallado** en castellano, con un **enfoque tradicional (basado en Requisitos Funcionales)**, usando formato Markdown.
**IMPORTANTE: No uses tablas de Markdown.** Para el listado de requisitos, usa listas con viñetas en lugar de una tabla.
Sé detallado y profesional. Basa el contenido en la siguiente descripción del proyecto y lista de tareas principales.

**Estructura Obligatoria (Documento Funcional Tradicional):**

## 1. Visión del Producto
- Describe brevemente el sistema, su objetivo principal y el valor que aporta al negocio.

---

## 2. Requisitos Funcionales
- Genera al menos **5 Requisitos Funcionales (RF)** clave derivados del proyecto, asegurando que sean claros, unívocos y verificables.
- Usa el formato: **ID: RF-XXX**
- **Descripción:** [Detalla la funcionalidad o comportamiento que el sistema debe realizar.]
- **Reglas de Negocio Asociadas:**
- - [Menciona cualquier regla o restricción específica que afecte este requisito.]
- **Criterios de Verificación/Prueba:**
- - El sistema debe... [Resultado esperado para confirmar la funcionalidad.]

---

## 3. Flujos y Prototipos
- (Esta sección es un marcador de posición)
- Escribe un párrafo indicando que en esta sección se incluirían los diagramas de flujo (ej. BPMN, Diagramas de Caso de Uso), wireframes o mockups de alta fidelidad que detallan el comportamiento del sistema y el diseño de la interfaz para complementar los requisitos.
- Incluye diagramas cuando sea posible usando el estilo/formato de Mermaid

---

## 4. Requisitos No Funcionales
- Detalla los requisitos clave en las siguientes categorías:
- **Seguridad:** (ej. Autenticación, roles de usuario, protección de datos, cifrado)
- **Rendimiento:** (ej. Tiempos de respuesta máximos, carga concurrente de usuarios, escalabilidad)
- **Compatibilidad:** (ej. Navegadores soportados, sistemas operativos, integración con otros sistemas)
- **Usabilidad:** (ej. Diseño intuitivo, accesibilidad, estándares de interfaz)

---

## 5. Listado de Requisitos Funcionales y Trazabilidad
- Presenta un listado inicial y con trazabilidad de los requisitos funcionales generados en la Sección 2.
- **NO USES TABLAS.** Usa una lista con viñetas para cada item, así:
- - **ID:** RF-001 | **Requisito:** [Nombre corto de la funcionalidad] | **Prioridad:** Obligatorio/Deseable/Opcional | **Origen:** [Sección del documento/Tarea principal que lo origina]
- - **ID:** RF-002 | **Requisito:** [Nombre corto de la funcionalidad] | **Prioridad:** Obligatorio/Deseable/Opcional | **Origen:** [Sección del documento/Tarea principal que lo origina]

**Datos del Proyecto:**
- **Descripción:** {project_description}
- **Tareas Principales:**
{task_list}
"""

# Prompt para documento SOLO de Historias de Usuario
PROMPT_USER_STORIES = """Eres un Product Owner Senior. Genera un documento en castellano con SOLO Historias de Usuario claras y accionables, derivadas del proyecto y su WBS.

Reglas:
- Entrega en formato Markdown, sin tablas.
- Al menos 10 Historias de Usuario.
- Para cada historia incluye: ID (US-XXX), Nombre corto, Descripción (Como..., quiero..., para...), Criterios de Aceptación (3-5), Prioridad (Alta/Media/Baja), Estimación (puntos), Dependencias (si aplica).
- Usa lenguaje orientado a negocio y resultados.

Contexto:
- Descripción: {project_description}
- Resumen de tareas:
{task_list}
"""

# Prompts para revisión de requisitos y generación de casos de prueba
PROMPT_REQUIREMENTS_REVIEW = """Eres un analista senior de requisitos. Revisa el siguiente texto (requisitos/propuesta) en castellano evaluando: claridad, coherencia, completitud, ambigüedades, testabilidad y riesgos. Devuelve recomendaciones concretas y priorizadas. Texto a revisar:\n\n{project_description}"""

PROMPT_TEST_CASES_FROM_HUS = """Eres un QA senior. Genera casos de prueba detallados (en castellano) a partir de estas Historias de Usuario. Usa formato Markdown con secciones por HU, incluye: título del caso, objetivo, precondiciones, pasos numerados, datos, resultado esperado y criterios de aceptación verificados. Historias:\n\n{stories_markdown}"""

# Prompt para propuesta de riesgos por IA (JSON)
PROMPT_RISK_SUGGESTION = """Eres un Risk Manager senior. Propón riesgos relevantes para el proyecto en FORMATO JSON.
Reglas:
- Responde SOLO con JSON (lista de objetos), sin texto extra.
- Cada riesgo: description (string), probability (0-1), impact (Bajo/Medio/Alto), mitigation_plan (string opcional).
- Incluye entre 6 y 12 riesgos variados (técnicos, operativos, compliance, stakeholders, cronograma, costes).
Contexto:
- Descripción: {project_description}
- Tareas principales:\n{task_list}
"""

PROMPT_MONTE_CARLO_REPORT = """Eres un experto en gestión de proyectos. Genera un informe conciso (200-300 palabras) en castellano con la explicación y conclusiones de una simulación Monte Carlo para un proyecto.
Incluye:
- Una breve introducción a la simulación Monte Carlo en gestión de proyectos.
- Interpretación de los percentiles P50 y P80 para duración y coste.
- Conclusiones sobre la probabilidad de completar el proyecto dentro de ciertos rangos.
- Recomendaciones basadas en los resultados.

Datos de la simulación:
- Duración P50: {p50_dur} días
- Duración P80: {p80_dur} días
- Coste P50: €{p50_cost:,.2f}
- Coste P80: €{p80_cost:,.2f}
- Número de simulaciones: {sims}
- Variabilidad (sigma): {sigma_pct}%
- Descripción del proyecto: {project_description}
"""


# =========================
# FUNCIONES DE BASE DE DATOS
# =========================
DB_FILE = "projects.db"
@st.cache_resource
def get_db_connection():
    """Establece y devuelve una conexión thread-safe a la base de datos."""
    conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, user_id INTEGER, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)")
        cursor.execute("PRAGMA table_info(projects)")
        columns_projects = [col[1] for col in cursor.fetchall()]
        if 'user_id' not in columns_projects:
            cursor.execute("ALTER TABLE projects ADD COLUMN user_id INTEGER")
        cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, project_id INTEGER, TaskID TEXT NOT NULL, Task TEXT NOT NULL, Duration_days INTEGER, Duration_hours INTEGER, Dependencies TEXT, Resource TEXT, Priority TEXT DEFAULT 'Media', Status TEXT DEFAULT 'No Iniciada', Progress REAL DEFAULT 0.0, Actual_Start TIMESTAMP, Actual_Finish TIMESTAMP, Sprint TEXT, Story_Points REAL, Actual_Cost REAL, Epic TEXT, Tags TEXT, Business_Value REAL, Time_Criticality REAL, Risk_Reduction REAL, Job_Size REAL, RACI_R TEXT, RACI_A TEXT, RACI_C TEXT, RACI_I TEXT, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE)")
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'Duration_hours' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Duration_hours INTEGER DEFAULT 0")
        if 'Priority' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Priority TEXT DEFAULT 'Media'")
        if 'Status' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Status TEXT DEFAULT 'No Iniciada'")
        if 'Progress' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Progress REAL DEFAULT 0.0")
        if 'Actual_Start' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Actual_Start TIMESTAMP")
        if 'Actual_Finish' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Actual_Finish TIMESTAMP")
        if 'Sprint' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Sprint TEXT")
        if 'Story_Points' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Story_Points REAL")
        if 'Actual_Cost' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Actual_Cost REAL")
        if 'Epic' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Epic TEXT")
        if 'Tags' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN Tags TEXT")
        for col_name in ['Business_Value','Time_Criticality','Risk_Reduction','Job_Size']:
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} REAL")
        for col_name in ['RACI_R','RACI_A','RACI_C','RACI_I']:
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} TEXT")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks (project_id)")
        cursor.execute("CREATE TABLE IF NOT EXISTS detailed_tasks (id INTEGER PRIMARY KEY, project_id INTEGER, TaskID TEXT, Task TEXT, Detailed_Step TEXT, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detailed_tasks_project_id ON detailed_tasks (project_id)")
        cursor.execute("CREATE TABLE IF NOT EXISTS additional_costs (id INTEGER PRIMARY KEY, project_id INTEGER, Description TEXT, Cost REAL, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_additional_costs_project_id ON additional_costs (project_id)")
        cursor.execute("CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, role_id INTEGER, FOREIGN KEY(role_id) REFERENCES roles(id))")
        cursor.execute("INSERT OR IGNORE INTO roles (id, name) VALUES (1, 'Project Manager')")
        cursor.execute("INSERT OR IGNORE INTO roles (id, name) VALUES (2, 'Team Member')")
        cursor.execute("INSERT OR IGNORE INTO roles (id, name) VALUES (3, 'Stakeholder')")
        cursor.execute("CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, user_id INTEGER, project_id INTEGER, message TEXT NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_read BOOLEAN DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id)")
        
        # Tablas para gestión de riesgos e incidencias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS risks (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            probability REAL CHECK(probability >= 0 AND probability <= 1),
            impact TEXT CHECK(impact IN ('Bajo', 'Medio', 'Alto')),
            status TEXT DEFAULT 'Abierto' CHECK(status IN ('Abierto', 'Mitigado', 'Cerrado')),
            mitigation_plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            severity TEXT CHECK(severity IN ('Bajo', 'Medio', 'Alto', 'Crítico')),
            status TEXT DEFAULT 'Abierto' CHECK(status IN ('Abierto', 'En Progreso', 'Resuelto', 'Cerrado')),
            resolution_plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)
        
        # Tablas para Sprints, Capacidades y Líneas Base
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sprints (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            goal TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

        # Tablas para Change Requests, Attachments y OKRs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS change_requests (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            impact TEXT,
            status TEXT DEFAULT 'Propuesto' CHECK(status IN ('Propuesto','Aprobado','Rechazado','Implementado')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_by TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            task_id TEXT,
            name TEXT NOT NULL,
            content BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS okrs (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            objective TEXT NOT NULL,
            key_result TEXT NOT NULL,
            target_value REAL,
            current_value REAL DEFAULT 0,
            owner TEXT,
            due_date DATE,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_capacity (
            id INTEGER PRIMARY KEY,
            sprint_id INTEGER NOT NULL,
            resource TEXT NOT NULL,
            capacity_hours REAL NOT NULL,
            FOREIGN KEY(sprint_id) REFERENCES sprints(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS baselines (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS baseline_tasks (
            id INTEGER PRIMARY KEY,
            baseline_id INTEGER NOT NULL,
            TaskID TEXT,
            Task TEXT,
            Start TIMESTAMP,
            Finish TIMESTAMP,
            Cost REAL,
            Sprint TEXT,
            Story_Points REAL,
            FOREIGN KEY(baseline_id) REFERENCES baselines(id) ON DELETE CASCADE
        )
        """)

        # Preferencias por proyecto (calendario y capacidades)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_prefs (
            project_id INTEGER PRIMARY KEY,
            weekends_off INTEGER DEFAULT 1,
            holidays TEXT,
            capacities_json TEXT,
            mc_sims INTEGER,
            mc_variability_pct INTEGER,
            spi_threshold REAL,
            cpi_threshold REAL,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)
        conn.commit()

def get_project_list(user_id: int) -> List[Tuple[int, str]]:
    conn = get_db_connection()
    return conn.cursor().execute("SELECT id, name FROM projects WHERE user_id = ? ORDER BY name ASC", (user_id,)).fetchall()

def save_complete_project_to_db(project_name: str, description: str, project_data: Dict, max_retries: int = 10, backoff_factor: float = 1.0):
    """Guarda TODOS los datos relacionados con un proyecto"""
    if not project_name.strip():
        raise ValueError("El nombre del proyecto no puede estar vacío.")

    project_id = None
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            with conn:
                cursor = conn.cursor()
                
                # Crear o actualizar proyecto principal
                project = cursor.execute("SELECT id FROM projects WHERE name = ? AND user_id = ?", (project_name, st.session_state.user_id)).fetchone()
                if project:
                    project_id = project[0]
                    cursor.execute("UPDATE projects SET description = ? WHERE id = ?", (description, project_id))
                    if st.session_state.user_id:
                        add_notification(st.session_state.user_id, project_id, f"El proyecto '{project_name}' ha sido actualizado.")
                else:
                    cursor.execute("INSERT INTO projects (name, description, user_id) VALUES (?, ?, ?)", (project_name, description, st.session_state.user_id))
                    project_id = cursor.lastrowid
                    if st.session_state.user_id:
                        add_notification(st.session_state.user_id, project_id, f"El proyecto '{project_name}' ha sido creado.")
                
                # Limpiar datos existentes
                cursor.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM detailed_tasks WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM additional_costs WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM risks WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM issues WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM change_requests WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM attachments WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM okrs WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM project_prefs WHERE project_id = ?", (project_id,))
                
                # Eliminar sprints (con sus datos relacionados)
                sprints_to_delete = cursor.execute("SELECT id FROM sprints WHERE project_id = ?", (project_id,)).fetchall()
                for sprint in sprints_to_delete:
                    cursor.execute("DELETE FROM resource_capacity WHERE sprint_id = ?", (sprint[0],))
                cursor.execute("DELETE FROM sprints WHERE project_id = ?", (project_id,))
                
                baselines_to_delete = cursor.execute("SELECT id FROM baselines WHERE project_id = ?", (project_id,)).fetchall()
                for baseline in baselines_to_delete:
                    cursor.execute("DELETE FROM baseline_tasks WHERE baseline_id = ?", (baseline[0],))
                cursor.execute("DELETE FROM baselines WHERE project_id = ?", (project_id,))

                # Guardar datos básicos del proyecto
                tasks_df = project_data.get('tasks_df', pd.DataFrame())
                detailed_df = project_data.get('detailed_df', pd.DataFrame())
                additional_costs_df = project_data.get('additional_costs_df', pd.DataFrame())
                
                if not tasks_df.empty:
                    tasks_to_save = tasks_df.copy()
                    # Asegurar columnas opcionales con valores por defecto
                    default_task_cols = {
                        'Sprint': '', 'Story_Points': 0, 'Actual_Cost': 0.0, 'Actual_Start': pd.NaT, 'Actual_Finish': pd.NaT,
                        'Priority': 'Media', 'Status': 'No Iniciada', 'Progress': 0.0, 'Epic': '', 'Tags': '',
                        'Business_Value': 0.0, 'Time_Criticality': 0.0, 'Risk_Reduction': 0.0, 'Job_Size': 0.0,
                        'RACI_R': '', 'RACI_A': '', 'RACI_C': '', 'RACI_I': '',
                    }
                    for col, default_val in default_task_cols.items():
                        if col not in tasks_to_save.columns:
                            tasks_to_save[col] = default_val
                    tasks_to_save['project_id'] = project_id
                    tasks_to_save['Dependencies'] = tasks_to_save['Dependencies'].apply(lambda x: json.dumps([str(d) for d in x]) if isinstance(x, list) else json.dumps([]))
                    tasks_to_save['Actual_Start'] = tasks_to_save['Actual_Start'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)
                    tasks_to_save['Actual_Finish'] = tasks_to_save['Actual_Finish'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)
                    
                    cols_to_save = ['project_id', 'TaskID', 'Task', 'Duration_days', 'Duration_hours', 'Dependencies', 'Resource', 'Priority', 'Status', 'Progress', 'Actual_Start', 'Actual_Finish', 'Sprint', 'Story_Points', 'Actual_Cost', 'Epic', 'Tags', 'Business_Value', 'Time_Criticality', 'Risk_Reduction', 'Job_Size', 'RACI_R', 'RACI_A', 'RACI_C', 'RACI_I']
                    for col in cols_to_save:
                        if col not in tasks_to_save.columns:
                            if col in ['Actual_Start', 'Actual_Finish']:
                                tasks_to_save[col] = pd.NaT
                            elif col in ['Duration_days', 'Duration_hours', 'Story_Points', 'Progress']:
                                tasks_to_save[col] = 0
                            elif col in ['Actual_Cost', 'Business_Value', 'Time_Criticality', 'Risk_Reduction', 'Job_Size']:
                                tasks_to_save[col] = 0.0
                            elif col == 'Dependencies':
                                tasks_to_save[col] = [[]] * len(tasks_to_save)
                            else:
                                tasks_to_save[col] = ''
                    
                    tasks_to_save[cols_to_save].to_sql('tasks', conn, if_exists='append', index=False)

                # Guardar tareas detalladas
                if not detailed_df.empty:
                    detailed_to_save = detailed_df.copy()
                    detailed_to_save['project_id'] = project_id
                    detailed_to_save.rename(columns={"Detailed Step": "Detailed_Step"}, inplace=True)
                    detailed_to_save[['project_id', 'TaskID', 'Task', 'Detailed_Step']].to_sql('detailed_tasks', conn, if_exists='append', index=False)

                # Guardar costos adicionales
                if not additional_costs_df.empty:
                    costs_to_save = additional_costs_df.dropna(subset=["Description", "Cost"]).copy()
                    if not costs_to_save.empty:
                        costs_to_save['project_id'] = project_id
                        costs_to_save[['project_id', 'Description', 'Cost']].to_sql('additional_costs', conn, if_exists='append', index=False)

                # Guardar riesgos
                risks_df = project_data.get('risks_df', pd.DataFrame())
                if not risks_df.empty:
                    risks_to_save = risks_df.copy()
                    risks_to_save['project_id'] = project_id
                    risks_to_save[['project_id', 'description', 'probability', 'impact', 'status', 'mitigation_plan', 'created_at', 'updated_at']].to_sql('risks', conn, if_exists='append', index=False)

                # Guardar incidencias
                issues_df = project_data.get('issues_df', pd.DataFrame())
                if not issues_df.empty:
                    issues_to_save = issues_df.copy()
                    issues_to_save['project_id'] = project_id
                    issues_to_save[['project_id', 'description', 'severity', 'status', 'resolution_plan', 'created_at', 'updated_at']].to_sql('issues', conn, if_exists='append', index=False)

                # Guardar sprints
                sprints_df = project_data.get('sprints_df', pd.DataFrame())
                if not sprints_df.empty:
                    sprints_to_save = sprints_df.copy()
                    sprints_to_save['project_id'] = project_id
                    sprints_to_save[['project_id', 'name', 'start_date', 'end_date']].to_sql('sprints', conn, if_exists='append', index=False)
                    
                    # Guardar resource_capacity para cada sprint
                    resource_capacity_dfs = project_data.get('resource_capacity_dfs', {})
                    for sprint_id, capacity_df in resource_capacity_dfs.items():
                        if not capacity_df.empty:
                            capacity_to_save = capacity_df.copy()
                            capacity_to_save['sprint_id'] = sprint_id
                            capacity_to_save[['sprint_id', 'resource', 'capacity_hours']].to_sql('resource_capacity', conn, if_exists='append', index=False)

                # Guardar change requests
                change_requests_df = project_data.get('change_requests_df', pd.DataFrame())
                if not change_requests_df.empty:
                    cr_to_save = change_requests_df.copy()
                    cr_to_save['project_id'] = project_id
                    cr_to_save[['project_id', 'title', 'description', 'impact', 'status', 'created_at']].to_sql('change_requests', conn, if_exists='append', index=False)

                # Guardar attachments
                attachments_df = project_data.get('attachments_df', pd.DataFrame())
                if not attachments_df.empty:
                    att_to_save = attachments_df.copy()
                    att_to_save['project_id'] = project_id
                    att_to_save[['project_id', 'task_id', 'name', 'content', 'created_at']].to_sql('attachments', conn, if_exists='append', index=False)

                # Guardar OKRs
                okrs_df = project_data.get('okrs_df', pd.DataFrame())
                if not okrs_df.empty:
                    okrs_to_save = okrs_df.copy()
                    okrs_to_save['project_id'] = project_id
                    okrs_to_save[['project_id', 'objective', 'key_result', 'target_value', 'current_value', 'created_at']].to_sql('okrs', conn, if_exists='append', index=False)

                # Guardar baselines
                baselines_df = project_data.get('baselines_df', pd.DataFrame())
                if not baselines_df.empty:
                    baselines_to_save = baselines_df.copy()
                    baselines_to_save['project_id'] = project_id
                    baselines_to_save[['project_id', 'name', 'created_at']].to_sql('baselines', conn, if_exists='append', index=False)
                    
                    # Guardar baseline_tasks para cada baseline
                    baseline_tasks_dfs = project_data.get('baseline_tasks_dfs', {})
                    for baseline_id, baseline_tasks_df in baseline_tasks_dfs.items():
                        if not baseline_tasks_df.empty:
                            bt_to_save = baseline_tasks_df.copy()
                            bt_to_save['baseline_id'] = baseline_id
                            bt_to_save[['baseline_id', 'TaskID', 'Task', 'Start', 'Finish', 'Duration', 'Resource', 'Cost', 'Sprint', 'Story_Points']].to_sql('baseline_tasks', conn, if_exists='append', index=False)

                # Guardar preferencias del proyecto
                project_prefs_df = project_data.get('project_prefs_df', pd.DataFrame())
                if not project_prefs_df.empty:
                    prefs_to_save = project_prefs_df.copy()
                    prefs_to_save['project_id'] = project_id
                    prefs_to_save[['project_id', 'weekends_off', 'holidays', 'capacities_json', 'mc_sims', 'cpi_threshold']].to_sql('project_prefs', conn, if_exists='append', index=False)

            return project_id
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                st.warning(f"Base de datos bloqueada. Reintentando en {backoff_factor * (2 ** attempt):.1f} segundos... (Intento {attempt + 1}/{max_retries})")
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                raise
    raise RuntimeError(f"Fallo al guardar el proyecto después de {max_retries} intentos debido a bloqueo de la base de datos.")

def save_project_to_db(project_name: str, description: str, tasks_df: pd.DataFrame, detailed_df: pd.DataFrame, additional_costs_df: pd.DataFrame, max_retries: int = 10, backoff_factor: float = 1.0):
    if not project_name.strip():
        raise ValueError("El nombre del proyecto no puede estar vacío.")

    project_id = None  # asegurar inicialización
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            with conn:
                cursor = conn.cursor()
                
                project = cursor.execute("SELECT id FROM projects WHERE name = ? AND user_id = ?", (project_name, st.session_state.user_id)).fetchone()
                if project:
                    project_id = project[0]
                    cursor.execute("UPDATE projects SET description = ? WHERE id = ?", (description, project_id))
                    if st.session_state.user_id:
                        add_notification(st.session_state.user_id, project_id, f"El proyecto '{project_name}' ha sido actualizado.")
                else:
                    cursor.execute("INSERT INTO projects (name, description, user_id) VALUES (?, ?, ?)", (project_name, description, st.session_state.user_id))
                    project_id = cursor.lastrowid
                    if st.session_state.user_id:
                        add_notification(st.session_state.user_id, project_id, f"El proyecto '{project_name}' ha sido creado.")
                
                # Limpiar tareas, detalladas y costes viejos para este proyecto
                cursor.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM detailed_tasks WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM additional_costs WHERE project_id = ?", (project_id,))

                # Insertar tareas nuevas
                tasks_to_save = tasks_df.copy()
                # Asegurar columnas opcionales con valores por defecto
                default_task_cols = {
                    'Sprint': '',
                    'Story_Points': 0,
                    'Actual_Cost': 0.0,
                    'Actual_Start': pd.NaT,
                    'Actual_Finish': pd.NaT,
                    'Priority': 'Media',
                    'Status': 'No Iniciada',
                    'Progress': 0.0,
                    'Epic': '',
                    'Tags': '',
                    'Business_Value': 0.0,
                    'Time_Criticality': 0.0,
                    'Risk_Reduction': 0.0,
                    'Job_Size': 0.0,
                    'RACI_R': '',
                    'RACI_A': '',
                    'RACI_C': '',
                    'RACI_I': '',
                }
                for col, default_val in default_task_cols.items():
                    if col not in tasks_to_save.columns:
                        tasks_to_save[col] = default_val
                tasks_to_save['project_id'] = project_id
                # Asegurar que 'Dependencies' es una lista de strings antes de serializar
                if 'Dependencies' not in tasks_to_save.columns:
                    tasks_to_save['Dependencies'] = [[]] * len(tasks_to_save) # Añadir columna si no existe
                tasks_to_save['Dependencies'] = tasks_to_save['Dependencies'].apply(lambda x: json.dumps([str(d) for d in x]) if isinstance(x, list) else json.dumps([]))
                
                # Manejar fechas que pueden ser NaT
                tasks_to_save['Actual_Start'] = tasks_to_save['Actual_Start'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)
                tasks_to_save['Actual_Finish'] = tasks_to_save['Actual_Finish'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)
                
                # Asegurar que todas las columnas a guardar existen en tasks_to_save
                cols_to_save = ['project_id', 'TaskID', 'Task', 'Duration_days', 'Duration_hours', 'Dependencies', 'Resource', 'Priority', 'Status', 'Progress', 'Actual_Start', 'Actual_Finish', 'Sprint', 'Story_Points', 'Actual_Cost', 'Epic', 'Tags', 'Business_Value', 'Time_Criticality', 'Risk_Reduction', 'Job_Size', 'RACI_R', 'RACI_A', 'RACI_C', 'RACI_I']
                
                for col in cols_to_save:
                    if col not in tasks_to_save.columns:
                        # Añadir columna con valor por defecto si no existe
                        if col in ['Actual_Start', 'Actual_Finish']:
                            tasks_to_save[col] = pd.NaT
                        elif col in ['Duration_days', 'Duration_hours', 'Story_Points', 'Progress']:
                            tasks_to_save[col] = 0
                        elif col in ['Actual_Cost', 'Business_Value', 'Time_Criticality', 'Risk_Reduction', 'Job_Size']:
                            tasks_to_save[col] = 0.0
                        elif col == 'Dependencies':
                            tasks_to_save[col] = [[]] * len(tasks_to_save)
                        else:
                            tasks_to_save[col] = ''
                
                tasks_to_save[cols_to_save].to_sql('tasks', conn, if_exists='append', index=False)

                # Insertar tareas detalladas nuevas
                if not detailed_df.empty:
                    detailed_to_save = detailed_df.copy()
                    detailed_to_save['project_id'] = project_id
                    detailed_to_save.rename(columns={"Detailed Step": "Detailed_Step"}, inplace=True)
                    detailed_to_save[['project_id', 'TaskID', 'Task', 'Detailed_Step']].to_sql('detailed_tasks', conn, if_exists='append', index=False)

                # Insertar costes adicionales nuevos
                if not additional_costs_df.empty:
                    costs_to_save = additional_costs_df.dropna(subset=["Description", "Cost"]).copy()
                    if not costs_to_save.empty:
                        costs_to_save['project_id'] = project_id
                        costs_to_save[['project_id', 'Description', 'Cost']].to_sql('additional_costs', conn, if_exists='append', index=False)
            return project_id
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                st.warning(f"Base de datos bloqueada. Reintentando en {backoff_factor * (2 ** attempt):.1f} segundos... (Intento {attempt + 1}/{max_retries})")
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                raise
    raise RuntimeError(f"Fallo al guardar el proyecto después de {max_retries} intentos debido a bloqueo de la base de datos.")

def load_project_from_db(project_id: int, profile_costs: Dict[str, float]):
    """Función de carga básica mantenida para compatibilidad"""
    conn = get_db_connection()
    project_data = conn.cursor().execute("SELECT name, description FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project_data: return None, None, None, None, None
    
    tasks_df = pd.read_sql_query("SELECT TaskID, Task, Duration_days, Duration_hours, Dependencies, Resource, Priority, Status, Progress, Actual_Start, Actual_Finish, Sprint, Story_Points, Actual_Cost, Epic, Tags, Business_Value, Time_Criticality, Risk_Reduction, Job_Size, RACI_R, RACI_A, RACI_C, RACI_I FROM tasks WHERE project_id = ?", conn, params=(project_id,))
    if not tasks_df.empty:
        tasks_df["Dependencies"] = tasks_df["Dependencies"].apply(json.loads)
        tasks_df['Actual_Start'] = pd.to_datetime(tasks_df['Actual_Start'], errors='coerce')
        tasks_df['Actual_Finish'] = pd.to_datetime(tasks_df['Actual_Finish'], errors='coerce')
        tasks_df, _ = calculate_task_dates(tasks_df)
        tasks_df = calculate_costs(tasks_df, profile_costs)

    detailed_df = pd.read_sql_query("SELECT TaskID, Task, Detailed_Step FROM detailed_tasks WHERE project_id = ?", conn, params=(project_id,)).rename(columns={"Detailed_Step": "Detailed Step"})
    additional_costs_df = pd.read_sql_query("SELECT Description, Cost FROM additional_costs WHERE project_id = ?", conn, params=(project_id,))
    
    return project_data['name'], project_data['description'], tasks_df, detailed_df, additional_costs_df

def initialize_project_related_data():
    """Inicializa todos los datos relacionados de un proyecto con valores por defecto"""
    return {
        'risks_df': pd.DataFrame(),
        'issues_df': pd.DataFrame(),
        'sprints_df': pd.DataFrame(),
        'change_requests_df': pd.DataFrame(),
        'attachments_df': pd.DataFrame(),
        'okrs_df': pd.DataFrame(),
        'baselines_df': pd.DataFrame(),
        'baseline_tasks_dfs': {},
        'project_prefs_df': pd.DataFrame(),
        'resource_capacity_dfs': {}
    }

def get_project_data_summary():
    """Obtiene un resumen de todos los datos relacionados del proyecto actual"""
    summary = {
        'Tareas principales': len(st.session_state.tasks_df),
        'Tareas detalladas': len(st.session_state.detailed_df),
        'Costos adicionales': len(st.session_state.additional_costs),
        'Riesgos': len(st.session_state.risks_df),
        'Incidencias': len(st.session_state.issues_df),
        'Sprints': len(st.session_state.sprints_df),
        'Change Requests': len(st.session_state.change_requests_df),
        'Attachments': len(st.session_state.attachments_df),
        'OKRs': len(st.session_state.okrs_df),
        'Baselines': len(st.session_state.baselines_df),
        'Preferencias': len(st.session_state.project_prefs_df)
    }
    return summary

# =========================
# GESTIÓN DE SESIONES PERSISTENTES
# =========================

def save_session_to_storage(user_id: int, username: str, role_id: int):
    """Guarda la información de sesión en el session_state persistente"""
    import time
    
    # Crear timestamp de sesión
    session_timestamp = int(time.time())
    
    # Guardar en session_state con clave persistente
    st.session_state['persistent_session'] = {
        'user_id': user_id,
        'username': username,
        'role_id': role_id,
        'timestamp': session_timestamp,
        'valid': True
    }
    
    # Guardar en query params para persistencia entre recargas
    st.query_params.user_id = str(user_id)
    st.query_params.username = username
    st.query_params.role_id = str(role_id)
    st.query_params.timestamp = str(session_timestamp)

def validate_persistent_session():
    """Valida si existe una sesión persistente válida"""
    import time
    
    # Primero verificar session_state
    if 'persistent_session' in st.session_state:
        session_data = st.session_state['persistent_session']
        
        # Verificar que la sesión sea válida
        if not session_data.get('valid', False):
            return False
        
        # Verificar timestamp (sesión válida por 10 minutos de inactividad)
        current_time = int(time.time())
        session_timestamp = session_data.get('timestamp', 0)
        if current_time - session_timestamp > 600:  # 10 minutos en segundos
            # Sesión expirada
            clear_persistent_session()
            return False
        
        # Verificar que el usuario existe en la base de datos
        user = get_user(session_data.get('username', ''))
        if not user or user['id'] != session_data.get('user_id'):
            # Usuario no existe o ID no coincide
            clear_persistent_session()
            return False
        
        return True
    
    # Si no hay session_state, verificar query params
    query_params = st.query_params
    if query_params.get('user_id') and query_params.get('username') and query_params.get('timestamp'):
        try:
            user_id = int(query_params['user_id'])
            username = query_params['username']
            role_id = int(query_params['role_id']) if query_params.get('role_id') else 1
            timestamp = int(query_params['timestamp'])
            
            # Verificar timestamp
            current_time = int(time.time())
            if current_time - timestamp > 600:  # 10 minutos en segundos
                return False
            
            # Verificar que el usuario existe en la base de datos
            user = get_user(username)
            if not user or user['id'] != user_id:
                return False
            
            # Restaurar sesión desde query params
            st.session_state['persistent_session'] = {
                'user_id': user_id,
                'username': username,
                'role_id': role_id,
                'timestamp': timestamp,
                'valid': True
            }
            
            return True
        except (ValueError, IndexError):
            return False
    
    return False

def restore_persistent_session():
    """Restaura la sesión desde el almacenamiento persistente"""
    if validate_persistent_session():
        session_data = st.session_state['persistent_session']
        st.session_state.logged_in = True
        st.session_state.user_id = session_data['user_id']
        st.session_state.username = session_data['username']
        st.session_state.user_role_id = session_data['role_id']
        return True
    return False

def clear_persistent_session():
    """Limpia la sesión persistente"""
    if 'persistent_session' in st.session_state:
        del st.session_state['persistent_session']
    
    # Limpiar query params
    st.query_params.clear()
    
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.user_role_id = None

def check_session_validity():
    """Verifica la validez de la sesión actual y la restaura si es necesario"""
    # Si no está logueado pero hay sesión persistente, intentar restaurar
    if not st.session_state.get('logged_in', False):
        if restore_persistent_session():
            st.toast(f"Sesión restaurada: {st.session_state.username}", icon="🔄")
            return True
        return False
    
    # Si está logueado, verificar que la sesión sea válida
    if st.session_state.get('logged_in', False):
        if not validate_persistent_session():
            # Sesión inválida, limpiar
            clear_persistent_session()
            st.toast("Sesión expirada. Por favor, inicia sesión nuevamente.", icon="⏰")
            return False
        return True
    
    return False

def require_authentication():
    """Decorador para requerir autenticación en funciones críticas"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_session_validity():
                st.error("Debes iniciar sesión para acceder a esta función.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def renew_session_if_active():
    """Renueva la sesión si el usuario está activo (última actividad reciente)"""
    import time
    
    if 'persistent_session' in st.session_state:
        session_data = st.session_state['persistent_session']
        current_time = int(time.time())
        session_timestamp = session_data.get('timestamp', 0)
        
        # Si la sesión tiene menos de 1 hora, renovar timestamp
        if current_time - session_timestamp < 3600:  # 1 hora
            session_data['timestamp'] = current_time
            st.session_state['persistent_session'] = session_data
            return True
    return False

def add_session_activity():
    """Registra actividad del usuario para mantener la sesión activa"""
    if st.session_state.get('logged_in', False):
        # Actualizar timestamp de actividad
        if 'persistent_session' in st.session_state:
            import time
            st.session_state['persistent_session']['timestamp'] = int(time.time())

def apply_pending_wbs_changes():
    """Aplica cambios pendientes de la tabla WBS al session_state si existen"""
    try:
        # Verificar si hay cambios pendientes en la tabla WBS
        if 'edited_df' in st.session_state and not st.session_state['edited_df'].empty:
            edited_df = st.session_state['edited_df']
            
            if not st.session_state.tasks_df.empty:
                # Mapear columnas de vuelta
                column_mapping = {
                    'TaskID': 'ID', 'Task': 'Tarea', 'Priority': 'Prioridad', 'Duration_hours': 'Horas', 'Duration_days': 'Días',
                    'Dependencies': 'Dependencias', 'Resource': 'Recurso', 'Status': 'Estado', 'Progress': 'Progreso',
                    'Start': 'Inicio', 'Finish': 'Fin', 'Actual_Start': 'Inicio Real', 'Actual_Finish': 'Fin Real', 'Cost': 'Coste',
                    'Sprint': 'Sprint', 'Story_Points': 'Puntos', 'Actual_Cost': 'Coste Real'
                }
                inv_map = {v: k for k, v in column_mapping.items()}
                df_to_update = edited_df.rename(columns=inv_map)
                
                # Actualizar campos básicos
                if "Task" in df_to_update.columns:
                    st.session_state.tasks_df["Task"] = df_to_update["Task"]
                if "Priority" in df_to_update.columns:
                    st.session_state.tasks_df["Priority"] = df_to_update["Priority"]
                if "Status" in df_to_update.columns:
                    st.session_state.tasks_df["Status"] = df_to_update["Status"]
                if "Resource" in df_to_update.columns:
                    st.session_state.tasks_df["Resource"] = df_to_update["Resource"]
                if "Sprint" in df_to_update.columns:
                    st.session_state.tasks_df["Sprint"] = df_to_update["Sprint"]
                
                # Actualizar campos de duración (Horas y Días)
                if "Duration_hours" in df_to_update.columns:
                    duration_hours = pd.to_numeric(df_to_update["Duration_hours"], errors='coerce').fillna(8)
                    st.session_state.tasks_df["Duration_hours"] = duration_hours
                
                if "Duration_days" in df_to_update.columns:
                    duration_days = pd.to_numeric(df_to_update["Duration_days"], errors='coerce').fillna(1)
                    st.session_state.tasks_df["Duration_days"] = duration_days
                
                # Actualizar dependencias
                if "Dependencies" in df_to_update.columns:
                    # Convertir string de dependencias separadas por comas a lista
                    dependencies = df_to_update["Dependencies"].apply(
                        lambda x: [d.strip() for d in str(x).split(',') if d.strip()] if pd.notna(x) and str(x).strip() else []
                    )
                    st.session_state.tasks_df["Dependencies"] = dependencies
                
                # Actualizar fechas planificadas
                if "Start" in df_to_update.columns:
                    st.session_state.tasks_df["Start"] = pd.to_datetime(df_to_update["Start"], errors='coerce')
                if "Finish" in df_to_update.columns:
                    st.session_state.tasks_df["Finish"] = pd.to_datetime(df_to_update["Finish"], errors='coerce')
                
                # Actualizar coste
                if "Cost" in df_to_update.columns:
                    cost_values = pd.to_numeric(df_to_update["Cost"], errors='coerce').fillna(0.0)
                    st.session_state.tasks_df["Cost"] = cost_values
                
                # Actualizar campos numéricos con validación
                if "Progress" in df_to_update.columns:
                    progress_values = pd.to_numeric(df_to_update["Progress"], errors='coerce').fillna(0)
                    progress_values = progress_values.clip(0, 100)
                    st.session_state.tasks_df["Progress"] = progress_values
                
                if "Story_Points" in df_to_update.columns:
                    story_points = pd.to_numeric(df_to_update["Story_Points"], errors='coerce').fillna(0)
                    st.session_state.tasks_df["Story_Points"] = story_points
                
                if "Actual_Cost" in df_to_update.columns:
                    actual_cost = pd.to_numeric(df_to_update["Actual_Cost"], errors='coerce').fillna(0.0)
                    st.session_state.tasks_df["Actual_Cost"] = actual_cost
                
                # Actualizar fechas reales
                if "Actual_Start" in df_to_update.columns:
                    st.session_state.tasks_df["Actual_Start"] = pd.to_datetime(df_to_update["Actual_Start"], errors='coerce')
                if "Actual_Finish" in df_to_update.columns:
                    st.session_state.tasks_df["Actual_Finish"] = pd.to_datetime(df_to_update["Actual_Finish"], errors='coerce')
                
                return True
    except Exception as e:
        st.error(f"Error aplicando cambios de WBS: {e}")
        return False
    return False

def load_complete_project_from_db(project_id: int, profile_costs: Dict[str, float]):
    """Carga TODOS los datos relacionados con un proyecto"""
    conn = get_db_connection()
    project_data = conn.cursor().execute("SELECT name, description FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project_data: return None
    
    # Cargar datos básicos del proyecto
    tasks_df = pd.read_sql_query("SELECT TaskID, Task, Duration_days, Duration_hours, Dependencies, Resource, Priority, Status, Progress, Actual_Start, Actual_Finish, Sprint, Story_Points, Actual_Cost, Epic, Tags, Business_Value, Time_Criticality, Risk_Reduction, Job_Size, RACI_R, RACI_A, RACI_C, RACI_I FROM tasks WHERE project_id = ?", conn, params=(project_id,))
    if not tasks_df.empty:
        tasks_df["Dependencies"] = tasks_df["Dependencies"].apply(json.loads)
        tasks_df['Actual_Start'] = pd.to_datetime(tasks_df['Actual_Start'], errors='coerce')
        tasks_df['Actual_Finish'] = pd.to_datetime(tasks_df['Actual_Finish'], errors='coerce')
        tasks_df, _ = calculate_task_dates(tasks_df)
        tasks_df = calculate_costs(tasks_df, profile_costs)

    detailed_df = pd.read_sql_query("SELECT TaskID, Task, Detailed_Step FROM detailed_tasks WHERE project_id = ?", conn, params=(project_id,)).rename(columns={"Detailed_Step": "Detailed Step"})
    additional_costs_df = pd.read_sql_query("SELECT Description, Cost FROM additional_costs WHERE project_id = ?", conn, params=(project_id,))
    
    # Cargar datos relacionados adicionales
    risks_df = pd.read_sql_query("SELECT * FROM risks WHERE project_id = ?", conn, params=(project_id,))
    issues_df = pd.read_sql_query("SELECT * FROM issues WHERE project_id = ?", conn, params=(project_id,))
    sprints_df = pd.read_sql_query("SELECT * FROM sprints WHERE project_id = ?", conn, params=(project_id,))
    change_requests_df = pd.read_sql_query("SELECT * FROM change_requests WHERE project_id = ?", conn, params=(project_id,))
    attachments_df = pd.read_sql_query("SELECT * FROM attachments WHERE project_id = ?", conn, params=(project_id,))
    okrs_df = pd.read_sql_query("SELECT * FROM okrs WHERE project_id = ?", conn, params=(project_id,))
    baselines_df = pd.read_sql_query("SELECT * FROM baselines WHERE project_id = ?", conn, params=(project_id,))
    project_prefs_df = pd.read_sql_query("SELECT * FROM project_prefs WHERE project_id = ?", conn, params=(project_id,))
    
    # Cargar baseline_tasks para cada baseline
    baseline_tasks_dfs = {}
    if not baselines_df.empty:
        for baseline_id in baselines_df['id']:
            baseline_tasks = pd.read_sql_query("SELECT * FROM baseline_tasks WHERE baseline_id = ?", conn, params=(baseline_id,))
            baseline_tasks_dfs[baseline_id] = baseline_tasks
    
    # Cargar resource_capacity para cada sprint
    resource_capacity_dfs = {}
    if not sprints_df.empty:
        for sprint_id in sprints_df['id']:
            resource_capacity = pd.read_sql_query("SELECT * FROM resource_capacity WHERE sprint_id = ?", conn, params=(sprint_id,))
            resource_capacity_dfs[sprint_id] = resource_capacity
    
    return {
        'project_name': project_data['name'],
        'project_description': project_data['description'],
        'tasks_df': tasks_df,
        'detailed_df': detailed_df,
        'additional_costs_df': additional_costs_df,
        'risks_df': risks_df,
        'issues_df': issues_df,
        'sprints_df': sprints_df,
        'change_requests_df': change_requests_df,
        'attachments_df': attachments_df,
        'okrs_df': okrs_df,
        'baselines_df': baselines_df,
        'baseline_tasks_dfs': baseline_tasks_dfs,
        'project_prefs_df': project_prefs_df,
        'resource_capacity_dfs': resource_capacity_dfs
    }

def delete_project_from_db(project_id: int):
    conn = get_db_connection()
    with conn:
        conn.cursor().execute("DELETE FROM projects WHERE id = ?", (project_id,))

def get_user(username: str):
    conn = get_db_connection()
    return conn.cursor().execute("SELECT id, username, password, role_id FROM users WHERE username = ?", (username,)).fetchone()

def create_user(username: str, password_hash: str, role_id: int):
    conn = get_db_connection()
    with conn:
        conn.cursor().execute("INSERT INTO users (username, password, role_id) VALUES (?, ?, ?)", (username, password_hash, role_id))

def get_roles():
    conn = get_db_connection()
    return conn.cursor().execute("SELECT id, name FROM roles").fetchall()

def add_notification(user_id: int, project_id: int, message: str):
    conn = get_db_connection()
    with conn:
        conn.cursor().execute("INSERT INTO notifications (user_id, project_id, message) VALUES (?, ?, ?)", (user_id, project_id, message))

def get_notifications(user_id: int):
    conn = get_db_connection()
    return conn.cursor().execute("SELECT id, message, timestamp, is_read FROM notifications WHERE user_id = ? ORDER BY timestamp DESC", (user_id,)).fetchall()

def mark_notification_as_read(notification_id: int):
    conn = get_db_connection()
    with conn:
        conn.cursor().execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))

# =========================
# Funciones Auxiliares (IA y parsing)
# =========================
@st.cache_data(ttl=3600)
def call_llm_api(provider: str, model: str, prompt: str, expect_json: bool = False, max_retries: int = 3, backoff_factor: float = 1.0) -> str:
    config = API_PROVIDERS.get(provider)
    if not config or not config.get("api_key"): raise ValueError(f"La clave API para '{provider}' no está configurada.")
    api_key = config["api_key"]; url = config["url_template"].format(model=model, api_key=api_key)
    headers = {"Content-Type": "application/json"}
    if provider in ["Groq", "OpenRouter"]: headers["Authorization"] = f"Bearer {api_key}"
    
    data = {}
    if provider == "Gemini":
        data = {"contents": [{"parts": [{"text": prompt}]}], "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]}
        if expect_json: data["generationConfig"] = {"response_mime_type": "application/json"}
    else:
        data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            response_data = response.json()

            if 'error' in response_data:
                raise RuntimeError(response_data['error'].get('message', 'Error desconocido de la API.'))

            if provider in ["Groq", "OpenRouter"]:
                return response_data["choices"][0]["message"]["content"].strip()
            else: # Gemini
                candidate = response_data.get("candidates", [{}])[0]
                if "content" in candidate and "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0]["text"].strip()
                else:
                    raise RuntimeError(f"La IA no generó contenido (razón: {candidate.get('finishReason', 'DESCONOCIDO')}).")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                raise RuntimeError(f"Error de conexión con la API de '{provider}': {e}")
    raise RuntimeError(f"Fallo al llamar a la API de '{provider}' después de {max_retries} intentos.")

@st.cache_data
def get_pdf_text(uploaded_file_bytes: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file_bytes))
        return "\n".join([(p.extract_text() or "") for p in reader.pages]).strip()
    except Exception: return ""

@st.cache_data
def parse_json_wbs(wbs_text: str) -> pd.DataFrame:
    try:
        fence = re.search(r"```(?:json)?\s*(.*?)```", wbs_text, re.DOTALL | re.IGNORECASE)
        json_str = fence.group(1).strip() if fence else wbs_text
        start, end = json_str.find("["), json_str.rfind("]")
        if start != -1 and end > start: json_str = json_str[start : end + 1]
        data = json.loads(json_str)
        if not isinstance(data, list): raise ValueError("El JSON no es una lista de tareas válida.")
        return pd.DataFrame([{
            "TaskID": str(item.get("id", "")).strip(),
            "Task": item.get("nombre", "N/A"),
            "Duration_hours": int(item.get("duracion_horas", 8)),
            "Duration_days": (int(item.get("duracion_horas", 8)) + 7) // 8,
            "Horas": int(item.get("duracion_horas", 8)),
            "Dependencies": [str(d) for d in item.get("dependencias", []) if d],
            "Resource": item.get("perfil", "N/A")
        } for item in data])
    except Exception as e:
        st.error(f"Error procesando la respuesta de la IA para WBS: {e}\nContenido:\n{wbs_text[:500]}...")
        return pd.DataFrame(columns=["TaskID", "Task", "Duration_hours", "Duration_days", "Horas", "Dependencies", "Resource"])

@st.cache_data
def parse_detailed_subtasks(text: str) -> pd.DataFrame:
    subtasks, current_task_id, current_task_name = [], None, None
    try:
        for line in text.strip().splitlines():
            if not (line := line.strip()): continue
            if m := re.match(r"^\[(.+?)\]\s*(.+)$", line):
                current_task_id, current_task_name = m.group(1).strip(), m.group(2).strip()
            elif current_task_id and (line.startswith(("- ", "* ", "• "))):
                # Simplificar la extracción del texto de la subtarea para mayor robustez
                step_text = line.lstrip("-*• ").strip()
                if step_text:
                    subtasks.append({"TaskID": current_task_id, "Task": current_task_name or "", "Detailed Step": step_text})
        return pd.DataFrame(subtasks)
    except Exception as e:
        st.error(f"Error procesando la respuesta de la IA para subtareas detalladas: {e}\nContenido:\n{text[:500]}...")
        return pd.DataFrame(columns=["TaskID", "Task", "Detailed Step"])

# =========================
# Generación de documentos y exportaciones
# =========================

INLINE_MARKDOWN_PATTERN = re.compile(r'(\*\*.+?\*\*|\*.+?\*|`.+?`)')

def _add_formatted_runs(paragraph, text_content):
    """Añade texto con formato inline a un párrafo de Word."""
    parts = INLINE_MARKDOWN_PATTERN.split(text_content)
    for part in parts:
        if not part: continue
        if part.startswith('**') and part.endswith('**'):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith('*') and part.endswith('*'):
            paragraph.add_run(part[1:-1]).italic = True
        elif part.startswith('`') and part.endswith('`'):
            run = paragraph.add_run(part[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(10)
        else:
            paragraph.add_run(part)

def _handle_table(doc, lines, start_idx):
    """Procesa un bloque de tabla Markdown y lo añade al documento Word."""
    table_lines = []
    current_scan_idx = start_idx
    while current_scan_idx < len(lines) and lines[current_scan_idx].strip().startswith('|'):
        table_lines.append(lines[current_scan_idx].strip())
        current_scan_idx += 1

    if len(table_lines) < 2: return 0
    
    header_line = table_lines[0]
    separator_line = table_lines[1]

    if not re.match(r'^\|(?:[-:]+\|)+[-:]*$', separator_line): return 0

    headers = [h.strip() for h in header_line.split('|') if h.strip()]
    if not headers: return 0

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    
    for i, header in enumerate(headers):
        table.rows[0].cells[i].text = header
    
    for row_line in table_lines[2:]:
        cells_text = [c.strip() for c in row_line.split('|') if c.strip()]
        if len(cells_text) == len(headers):
            row_cells = table.add_row().cells
            for i, cell_text in enumerate(cells_text):
                p_cell = row_cells[i].paragraphs[0]
                _add_formatted_runs(p_cell, cell_text)
    
    return len(table_lines)

def enhanced_markdown_to_docx(doc: Document, text: str):
    """Convierte Markdown mejorado a un documento Word, con estilos y tablas."""
    styles = doc.styles
    # Definir estilos si no existen
    if 'HeadingMD' not in styles:
        style = styles.add_style('HeadingMD', WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles['Heading 1']
        style.font.color.rgb = RGBColor(0x2B, 0x54, 0x8B)
    if 'NormalParagraph' not in styles:
        style = styles.add_style('NormalParagraph', WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles['Normal']
        style.paragraph_format.space_after = Pt(8)
    if 'ListBulletCustom' not in styles:
        style = styles.add_style('ListBulletCustom', WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles['List Bullet']
        fmt = style.paragraph_format
        fmt.left_indent, fmt.first_line_indent, fmt.space_after = Pt(36), Pt(-12), Pt(4)
    if 'ListNumberCustom' not in styles:
        style = styles.add_style('ListNumberCustom', WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles['List Number']
        fmt = style.paragraph_format
        fmt.left_indent, fmt.first_line_indent, fmt.space_after = Pt(36), Pt(-12), Pt(4)

    lines = text.splitlines()
    line_idx = 0
    while line_idx < len(lines):
        line = lines[line_idx]
        stripped_line = line.strip()

        if stripped_line.startswith('|'):
            processed_lines = _handle_table(doc, lines, line_idx)
            if processed_lines > 0:
                line_idx += processed_lines
                continue
        
        style_map = {
            "#### ": ('Heading 4', 5), "### ": ('Heading 3', 4),
            "## ": ('Heading 2', 3), "# ": ('HeadingMD', 2),
            "- ": ('ListBulletCustom', 2), "* ": ('ListBulletCustom', 2)
        }
        
        processed = False
        for prefix, (style_name, cut_len) in style_map.items():
            if stripped_line.startswith(prefix):
                p = doc.add_paragraph(style=style_name)
                _add_formatted_runs(p, stripped_line[cut_len:])
                processed = True
                break
        
        if processed:
            line_idx += 1
            continue

        if re.match(r'^\d+\. ', stripped_line):
            p = doc.add_paragraph(style='ListNumberCustom')
            list_text = re.sub(r'^\d+\. ', '', stripped_line)
            _add_formatted_runs(p, list_text)
        elif not stripped_line:
            doc.add_paragraph('', style='NormalParagraph')
        else:
            p = doc.add_paragraph(style='NormalParagraph')
            _add_formatted_runs(p, line)
            
        line_idx += 1


def create_docx_from_text(title: str, body_text: str) -> bytes:
    doc = Document(); doc.add_heading(title, 0); enhanced_markdown_to_docx(doc, body_text)
    with io.BytesIO() as bio: doc.save(bio); return bio.getvalue()

def generate_full_report_docx(title: str, summary_text: str, tasks_df: pd.DataFrame, detailed_df: pd.DataFrame, profile_costs: Dict[str, float], risks_df: Optional[pd.DataFrame] = None, issues_df: Optional[pd.DataFrame] = None, evm_df: Optional[pd.DataFrame] = None, evm_summary: Optional[Dict[str, float]] = None) -> bytes:
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_heading("Resumen Ejecutivo", level=1)
    doc.add_paragraph(summary_text)

    if not tasks_df.empty:
        doc.add_heading("Plan de Tareas (WBS)", level=1)
        df_display = tasks_df.copy()
        if 'Cost' not in df_display.columns:
            df_display["Rate_per_hour"] = df_display["Resource"].map(profile_costs).fillna(0)
            df_display["Cost"] = df_display["Horas"] * df_display["Rate_per_hour"]
        
        df_display = df_display[['TaskID', 'Task', 'Duration_days', 'Resource', 'Start', 'Finish', 'Cost']].copy()
        for col in ['Start', 'Finish']:
            if pd.api.types.is_datetime64_any_dtype(df_display[col]):
                df_display[col] = df_display[col].dt.strftime('%Y-%m-%d').fillna('')
        df_display['Cost'] = df_display['Cost'].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) else "")

        table = doc.add_table(rows=1, cols=len(df_display.columns))
        table.style = 'Table Grid'
        for i, col_name in enumerate(df_display.columns):
            table.rows[0].cells[i].text = col_name
        for _, row in df_display.iterrows():
            row_cells = table.add_row().cells
            for i, val in enumerate(row):
                row_cells[i].text = str(val)

    if not detailed_df.empty:
        doc.add_heading("Desglose Detallado de Tareas", level=1)
        df_detailed_display = detailed_df[['TaskID', 'Task', 'Detailed Step']].copy()
        table = doc.add_table(rows=1, cols=len(df_detailed_display.columns))
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "ID Tarea"; hdr_cells[1].text = "Tarea Principal"; hdr_cells[2].text = "Paso Detallado"
        for _, row in df_detailed_display.iterrows():
            row_cells = table.add_row().cells
            row_cells[0].text = str(row['TaskID']); row_cells[1].text = str(row['Task']); row_cells[2].text = str(row['Detailed Step'])

    # Secciones de Riesgos e Incidencias
    if risks_df is not None and not risks_df.empty:
        doc.add_heading("Riesgos", level=1)
        cols = [c for c in ["description", "probability", "impact", "status", "mitigation_plan"] if c in risks_df.columns]
        if cols:
            table = doc.add_table(rows=1, cols=len(cols))
            table.style = 'Table Grid'
            for i, c in enumerate(cols):
                table.rows[0].cells[i].text = c.capitalize()
            for _, r in risks_df.iterrows():
                rc = table.add_row().cells
                for i, c in enumerate(cols):
                    val = r.get(c, "")
                    rc[i].text = str(val)

    if issues_df is not None and not issues_df.empty:
        doc.add_heading("Incidencias", level=1)
        cols = [c for c in ["description", "severity", "status", "resolution_plan"] if c in issues_df.columns]
        if cols:
            table = doc.add_table(rows=1, cols=len(cols))
            table.style = 'Table Grid'
            for i, c in enumerate(cols):
                table.rows[0].cells[i].text = c.capitalize()
            for _, r in issues_df.iterrows():
                rc = table.add_row().cells
                for i, c in enumerate(cols):
                    val = r.get(c, "")
                    rc[i].text = str(val)

    # Sección de EVA (Earned Value)
    if evm_summary is not None or (evm_df is not None and not evm_df.empty):
        doc.add_heading("Métricas de Valor Ganado (EVA)", level=1)
        if evm_summary:
            for k in ["BAC", "PV", "EV", "AC", "CV", "SV", "CPI", "SPI", "EAC", "VAC"]:
                if k in evm_summary:
                    doc.add_paragraph(f"{k}: {evm_summary[k]:,.2f}" if isinstance(evm_summary[k], (int, float)) else f"{k}: {evm_summary[k]}")
        if evm_df is not None and not evm_df.empty:
            cols = [c for c in ["TaskID", "Task", "BAC", "PV", "EV", "AC", "CV", "SV", "CPI", "SPI", "ETC", "EAC", "VAC"] if c in evm_df.columns]
            table = doc.add_table(rows=1, cols=len(cols))
            table.style = 'Table Grid'
            for i, c in enumerate(cols):
                table.rows[0].cells[i].text = c
            for _, r in evm_df.iterrows():
                rc = table.add_row().cells
                for i, c in enumerate(cols):
                    rc[i].text = str(r.get(c, ""))

    # Distribuciones básicas (Estado y Prioridad)
    if not tasks_df.empty and all(col in tasks_df.columns for col in ["Status", "Priority"]):
        doc.add_heading("Distribuciones de Tareas", level=1)
        status_counts = tasks_df["Status"].value_counts()
        doc.add_paragraph("Por Estado:")
        for idx, val in status_counts.items():
            doc.add_paragraph(f"- {idx}: {val}")
        priority_counts = tasks_df["Priority"].value_counts()
        doc.add_paragraph("Por Prioridad:")
        for idx, val in priority_counts.items():
            doc.add_paragraph(f"- {idx}: {val}")

    with io.BytesIO() as bio:
        doc.save(bio)
        return bio.getvalue()

def export_plan_to_excel(tasks_df: pd.DataFrame, additional_costs_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        if not tasks_df.empty:
            df = tasks_df.copy()
            df["Start"] = pd.to_datetime(df["Start"], errors='coerce')
            df["Finish"] = pd.to_datetime(df["Finish"], errors='coerce')
            df["Cost"] = pd.to_numeric(df["Cost"], errors='coerce')
            df["Dependencies"] = df["Dependencies"].apply(lambda x: ", ".join(map(str, x)) if isinstance(x, list) else "")
            
            cols_order = ['TaskID', 'Task', 'Duration_hours', 'Duration_days', 'Dependencies', 'Resource', 'Start', 'Finish', 'Cost']
            df = df.reindex(columns=[col for col in cols_order if col in df.columns])
            df.to_excel(writer, sheet_name="Plan", index=False)
            
            wb, ws = writer.book, writer.sheets["Plan"]
            money = wb.add_format({"num_format": "€#,##0.00"})
            datefmt = wb.add_format({"num_format": "yyyy-mm-dd"})
            header = {col_name: i for i, col_name in enumerate(df.columns)}
            if "Cost" in header: ws.set_column(header["Cost"], header["Cost"], 12, money)
            if "Start" in header: ws.set_column(header["Start"], header["Start"], 12, datefmt)
            if "Finish" in header: ws.set_column(header["Finish"], header["Finish"], 12, datefmt)
        if not additional_costs_df.empty:
            additional_costs_df.to_excel(writer, sheet_name="Costes Adicionales", index=False)
    return output.getvalue()

def export_to_ical(tasks_df: pd.DataFrame) -> bytes:
    c = Calendar()
    for _, row in tasks_df.iterrows():
        if pd.notna(row['Start']) and pd.notna(row['Finish']):
            e = Event()
            e.name = f"{row['TaskID']} - {row['Task']}"
            e.begin = row['Start']
            e.end = (row['Finish'] + timedelta(days=1)) # iCal end date is exclusive
            e.description = f"Recurso: {row.get('Resource', 'N/A')}\nDuración: {row.get('Duration_days', 'N/A')} días"
            
            c.events.add(e)
            
    return str(c).encode('utf-8')

# =========================
# Funciones de Lógica de Negocio
# =========================
def _hash_df(df: pd.DataFrame): return pd.util.hash_pandas_object(df.apply(lambda col: col.apply(lambda x: tuple(x) if isinstance(x, list) else x)), index=True).sum()

def validate_task_data(df_tasks: pd.DataFrame) -> None:
    required_columns = {'TaskID', 'Task', 'Duration_hours', 'Dependencies', 'Resource'}
    if not required_columns.issubset(df_tasks.columns):
        raise ValueError(f"Columnas requeridas faltantes: {', '.join(required_columns - set(df_tasks.columns))}")

def sanitize_tasks_df(tasks_df: pd.DataFrame, valid_profiles: List[str]) -> pd.DataFrame:
    if tasks_df.empty or 'Resource' not in tasks_df.columns: return tasks_df
    tasks_df['Resource'] = tasks_df['Resource'].apply(lambda r: r if r in valid_profiles else "Sin Asignar")
    return tasks_df

def calculate_task_dates(df_tasks: pd.DataFrame, start_base: date = date.today()) -> Tuple[pd.DataFrame, Set[str]]:
    validate_task_data(df_tasks)
    if df_tasks.empty: return df_tasks, set()

    df = df_tasks.copy()

    if 'Duration_days' not in df.columns:
        df['Duration_hours'] = pd.to_numeric(df['Duration_hours'], errors='coerce').fillna(8).astype(int)
        df['Duration_days'] = (df['Duration_hours'] + 7) // 8
    else:
        # Asegurarse de que Duration_days sea numérico y sin nulos para el cálculo
        df['Duration_days'] = pd.to_numeric(df['Duration_days'], errors='coerce').fillna(1).astype(int)

    df['Start'] = pd.NaT
    df['Finish'] = pd.NaT

    # Usar .to_dict('index') es más eficiente y devuelve diccionarios, no Series
    task_map = df.set_index('TaskID').to_dict('index')
    finish_dates = {}
    problematic_ids = set()

    # Refactorización para un enfoque topológico más claro y robusto
    task_map = {str(row['TaskID']): row.to_dict() for _, row in df.iterrows()}
    
    # 1. Construir grafo de dependencias y calcular grados de entrada
    in_degree = {tid: 0 for tid in task_map}
    adj = {tid: [] for tid in task_map}
    valid_task_ids = set(task_map.keys())

    for tid, task in task_map.items():
        deps = task.get('Dependencies', [])
        if not isinstance(deps, list): deps = []
        
        for dep_id_raw in deps:
            dep_id = str(dep_id_raw)
            if dep_id in valid_task_ids:
                adj[dep_id].append(tid)
                in_degree[tid] += 1
            else:
                # Dependencia rota: registrarla pero no bloquear el cálculo
                problematic_ids.add(dep_id)

    # 2. Cola para el ordenamiento topológico (tareas sin dependencias)
    queue = [tid for tid, degree in in_degree.items() if degree == 0]
    
    # 3. Procesar tareas
    finish_dates = {}
    processed_count = 0
    
    while queue:
        current_tid = queue.pop(0)
        processed_count += 1
        
        task = task_map[current_tid]
        
        # Calcular fecha de inicio basada en las dependencias ya procesadas
        max_dep_finish = pd.Timestamp(start_base) - pd.Timedelta(days=1)
        deps = task.get('Dependencies', [])
        if isinstance(deps, list):
            for dep_id_raw in deps:
                dep_id = str(dep_id_raw)
                if dep_id in finish_dates:
                    max_dep_finish = max(max_dep_finish, finish_dates[dep_id])

        start_date = max_dep_finish + pd.Timedelta(days=1)
        duration_days = max(1, int(task.get('Duration_days', 1)))
        finish_date = start_date + pd.Timedelta(days=duration_days - 1)
        
        # Guardar fechas
        finish_dates[current_tid] = finish_date
        df.loc[df['TaskID'] == current_tid, 'Start'] = start_date
        df.loc[df['TaskID'] == current_tid, 'Finish'] = finish_date

        # Actualizar grados de entrada de los sucesores
        for successor_tid in adj.get(current_tid, []):
            in_degree[successor_tid] -= 1
            if in_degree[successor_tid] == 0:
                queue.append(successor_tid)

    # 4. Detectar ciclos
    if processed_count < len(task_map):
        circular_deps = {tid for tid, degree in in_degree.items() if degree > 0}
        problematic_ids.update(circular_deps)
        
    if problematic_ids:
        st.warning(f"⚠️ Se detectaron dependencias circulares o rotas para las tareas: {', '.join(sorted(list(problematic_ids)))}. Sus fechas pueden ser incorrectas.")

    return df, problematic_ids

@st.cache_data(hash_funcs={pd.DataFrame: _hash_df})
def calculate_costs(df_tasks: pd.DataFrame, profile_costs: Dict[str, float]) -> pd.DataFrame:
    if df_tasks.empty: return df_tasks
    df = df_tasks.copy()
    
    # Usar Duration_hours directamente en lugar de crear una columna "Horas" duplicada
    df["Duration_hours"] = pd.to_numeric(df.get("Duration_hours", df.get("Horas", 8)), errors='coerce').fillna(8)
    df["Rate_per_hour"] = df["Resource"].map(profile_costs).fillna(0)
    df["Cost"] = df["Duration_hours"] * df["Rate_per_hour"]
    return df

@st.cache_data(hash_funcs={pd.DataFrame: _hash_df})
def calculate_critical_path(df_tasks: pd.DataFrame) -> Tuple[Set[str], int]:
    if df_tasks.empty or "Start" not in df_tasks.columns or "Finish" not in df_tasks.columns:
        return set(), 0

    df = df_tasks.dropna(subset=["Start", "Finish"]).copy()
    if df.empty: return set(), 0
    
    df['Start'] = pd.to_datetime(df['Start'])
    df['Finish'] = pd.to_datetime(df['Finish'])
    
    graph = {row.TaskID: [] for _, row in df.iterrows()}
    rev_graph = {row.TaskID: [] for _, row in df.iterrows()}
    for _, row in df.iterrows():
        for dep in row.Dependencies:
            if dep in graph:
                graph[dep].append(row.TaskID)
                rev_graph[row.TaskID].append(dep)

    es = {tid: df.loc[df.TaskID == tid, 'Start'].iloc[0] for tid in graph}
    ef = {tid: df.loc[df.TaskID == tid, 'Finish'].iloc[0] for tid in graph}
    
    project_finish = df['Finish'].max()
    
    # Inicializar ls y lf para todas las tareas con el project_finish
    # Esto asegura que todas las claves existen antes de los cálculos inversos
    ls = {tid: project_finish for tid in graph.keys()}
    lf = {tid: project_finish for tid in graph.keys()}

    for tid in sorted(graph.keys(), key=lambda t: ef[t], reverse=True):
        if not graph[tid]:
            lf[tid] = project_finish
        else:
            # Filtrar sucesores que no estén en ls (dependencias rotas o tareas filtradas)
            valid_successors = [succ for succ in graph[tid] if succ in ls]
            if valid_successors:
                lf[tid] = min(ls[succ] for succ in valid_successors) - pd.Timedelta(days=1)
            else:
                # Si no hay sucesores válidos, se comporta como una tarea final
                lf[tid] = project_finish
        ls[tid] = lf[tid] - (ef[tid] - es[tid])

    critical_path_ids = {tid for tid in graph if (ls[tid] - es[tid]).days == 0}
    duration = (project_finish - df['Start'].min()).days + 1 if not df.empty else 0
    
    return critical_path_ids, duration

@st.cache_data(hash_funcs={pd.DataFrame: _hash_df})
def create_gantt_chart(df_tasks: pd.DataFrame, critical_path_ids: Optional[Set[str]] = None):
    if df_tasks.empty or "Start" not in df_tasks.columns: return None
    df = df_tasks.dropna(subset=["Start", "Finish"]).sort_values("Start").reset_index(drop=True)
    if df.empty: return None
    
    df['y_label'] = df['TaskID'].astype(str) + ' - ' + df['Task']
    df["Color"] = df.apply(lambda r: "Crítica" if (critical_path_ids and r["TaskID"] in critical_path_ids) else r["Resource"], axis=1)
    
    unique_colors = df["Color"].unique()
    color_map = {cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, cat in enumerate(unique_colors)}
    if "Crítica" in color_map:
        color_map["Crítica"] = "#FF5733"

    fig = px.timeline(df, x_start="Start", x_end="Finish", y="y_label", color="Color", color_discrete_map=color_map,
                      hover_name="Task", custom_data=["Resource", "Duration_days", "Start", "Finish"],
                      labels={"Color": "Recurso / Estado", "y_label": "Tarea"}, template="plotly_white")
    fig.update_traces(hovertemplate="<b>%{hover_name}</b><br>Perfil: %{customdata[0]}<br>Duración: %{customdata[1]} días<br>Inicio: %{customdata[2]|%Y-%m-%d}<br>Fin: %{customdata[3]|%Y-%m-%d}<extra></extra>")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title_text="Diagrama de Gantt con Ruta Crítica", height=max(400, len(df) * 30))
    
    # Añadir flechas de dependencia
    y_pos_map = {label: i for i, label in enumerate(df['y_label'])}
    for _, row in df.iterrows():
        if row['Dependencies']:
            for dep_id in row['Dependencies']:
                predecessor = df[df['TaskID'] == dep_id]
                if not predecessor.empty:
                    p_row = predecessor.iloc[0]
                    p_y, s_y = y_pos_map.get(p_row['y_label']), y_pos_map.get(row['y_label'])
                    if p_y is not None and s_y is not None:
                        fig.add_annotation(x=row['Start'], y=s_y, ax=p_row['Finish'], ay=p_y,
                                           xref="x", yref="y", axref="x", ayref="y",
                                           showarrow=True, arrowhead=2, arrowwidth=1.5, arrowcolor="rgba(0,0,0,0.6)")
    return fig

import risk_management  # Importar el módulo de gestión de riesgos

# =========================
# Nivelación de recursos con calendarios laborales
# =========================
def _is_working_day(day: pd.Timestamp, weekends_off: bool, holidays: Set[pd.Timestamp]) -> bool:
    if pd.isna(day):
        return False
    if weekends_off and day.weekday() >= 5:
        return False
    if pd.Timestamp(day.normalize()) in holidays:
        return False
    return True

def level_schedule_with_calendars(df_tasks: pd.DataFrame, daily_capacity_map: Dict[str, float], holidays: Set[pd.Timestamp], weekends_off: bool = True) -> pd.DataFrame:
    if df_tasks.empty:
        return df_tasks
    df = df_tasks.copy()
    df['Duration_hours'] = pd.to_numeric(df.get('Duration_hours', df.get('Horas', 8)), errors='coerce').fillna(8).astype(float)
    # Preparar dependencias como listas
    deps_map = {}
    for _, r in df.iterrows():
        deps = r.get('Dependencies', [])
        deps_map[str(r['TaskID'])] = deps if isinstance(deps, list) else []

    # Mapa de fechas de fin por tarea (usaremos el cálculo actual como earliest)
    # Pasar la fecha de inicio base del proyecto para asegurar consistencia
    project_start_date = df['Start'].min().date() if not df.empty and 'Start' in df.columns and pd.notna(df['Start'].min()) else date.today()
    df_base, _ = calculate_task_dates(df, start_base=project_start_date)
    earliest_start_map = {str(r['TaskID']): (pd.to_datetime(r['Start']) if pd.notna(r['Start']) else pd.Timestamp(project_start_date)) for _, r in df_base.iterrows()}

    # Asignación por recurso y día: horas ya utilizadas
    used_hours: Dict[str, Dict[pd.Timestamp, float]] = {}

    # Ordenar tareas por earliest start y por dependencias (aprox)
    df_sorted = df.sort_values(['Start']).copy() if 'Start' in df.columns else df.copy()

    new_starts = {}
    new_finishes = {}

    for _, task in df_sorted.iterrows():
        task_id = str(task['TaskID'])
        resource = task.get('Resource', 'Sin Asignar')
        hours_needed = float(task['Duration_hours'])
        resource_cap = float(daily_capacity_map.get(resource, 8.0))
        used_hours.setdefault(resource, {})

        # Earliest start considerando dependencias ya niveladas
        dep_finish_dates = []
        for dep in deps_map.get(task_id, []):
            dep_str = str(dep)
            if dep_str in new_finishes and pd.notna(new_finishes[dep_str]):
                dep_finish_dates.append(new_finishes[dep_str])
            elif dep_str in earliest_start_map and pd.notna(earliest_start_map[dep_str]):
                # fallback al cálculo base
                dep_finish_dates.append(pd.to_datetime(df_base[df_base['TaskID'].astype(str)==dep_str]['Finish']).max())
        earliest_start = max(dep_finish_dates) + pd.Timedelta(days=1) if dep_finish_dates else earliest_start_map.get(task_id, pd.Timestamp(date.today()))
        current_day = pd.Timestamp(earliest_start.normalize())

        # Buscar primer día laborable
        while not _is_working_day(current_day, weekends_off, holidays):
            current_day += pd.Timedelta(days=1)

        remaining = hours_needed
        first_start = None
        last_day = current_day
        # Asignar horas día a día respetando capacidad y calendario
        while remaining > 0:
            if not _is_working_day(current_day, weekends_off, holidays):
                current_day += pd.Timedelta(days=1)
                continue
            used = used_hours[resource].get(current_day, 0.0)
            available = max(0.0, resource_cap - used)
            if available <= 0:
                current_day += pd.Timedelta(days=1)
                continue
            allocate = min(available, remaining)
            used_hours[resource][current_day] = used + allocate
            if first_start is None:
                first_start = current_day
            remaining -= allocate
            last_day = current_day
            if remaining > 0:
                current_day += pd.Timedelta(days=1)

        new_starts[task_id] = pd.Timestamp(first_start)
        new_finishes[task_id] = pd.Timestamp(last_day)

    # Aplicar nuevas fechas
    for tid, s in new_starts.items():
        df.loc[df['TaskID'].astype(str)==tid, 'Start'] = s
    for tid, f in new_finishes.items():
        df.loc[df['TaskID'].astype(str)==tid, 'Finish'] = f

    return df

# =========================
# Interfaz de Streamlit (Función Principal MEJORADA)
# =========================
def main():
    st.set_page_config(
        page_title="Suite de Gestión de Proyectos con IA",
        layout="wide",
        page_icon="📊",
        initial_sidebar_state="expanded"
    )
    # Mostrar detalles de errores en el cliente para depuración de pantallas en blanco
    try:
        st.set_option('client.showErrorDetails', True)
    except Exception:
        pass
    
    init_db()
    
    # Verificar y restaurar sesión persistente al inicio
    check_session_validity()
    
    # Renovar sesión si el usuario está activo
    renew_session_if_active()
    
    # Inicializar datos básicos del proyecto
    st.session_state.setdefault("tasks_df", pd.DataFrame())
    st.session_state.setdefault("detailed_df", pd.DataFrame())
    st.session_state.setdefault("project_description", "")
    st.session_state.setdefault("project_name", "")
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("user_role_id", None)
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("loaded_project_id", None)
    st.session_state.setdefault("selected_project_from_selectbox", None) # para mantener la selección del selectbox
    
    # Inicializar datos relacionados del proyecto
    st.session_state.setdefault("risks_df", pd.DataFrame())
    st.session_state.setdefault("issues_df", pd.DataFrame())
    st.session_state.setdefault("sprints_df", pd.DataFrame())
    st.session_state.setdefault("change_requests_df", pd.DataFrame())
    st.session_state.setdefault("attachments_df", pd.DataFrame())
    st.session_state.setdefault("okrs_df", pd.DataFrame())
    st.session_state.setdefault("baselines_df", pd.DataFrame())
    st.session_state.setdefault("baseline_tasks_dfs", {})
    st.session_state.setdefault("project_prefs_df", pd.DataFrame())
    st.session_state.setdefault("resource_capacity_dfs", {})
    
    if "additional_costs" not in st.session_state:
        st.session_state.additional_costs = pd.DataFrame({"Description": pd.Series(dtype='str'), "Cost": pd.Series(dtype='float')})

    st.title("🗂️ Suite de Gestión de Proyectos con IA")
    
    # Mostrar información sobre gestión de sesiones si el usuario está logueado
    if st.session_state.get('logged_in', False):
        with st.expander("ℹ️ Información de Sesión", expanded=False):
            st.info("""
            **Gestión de Sesiones Mejorada:**
            - ✅ Las sesiones persisten al recargar la página
            - ⏰ Timeout automático después de 10 minutos de inactividad
            - 🔄 Renovación automática con actividad del usuario
            - 🛡️ Validación de sesión en operaciones críticas
            - 🧹 Limpieza automática de sesiones expiradas
            """)

    # CSS global: expandir ancho del contenedor central
    if not st.session_state.get("global_css_injected"):
        st.markdown(
            """
            <style>
              .main .block-container { max-width: 100% !important; padding-left: 1rem; padding-right: 1rem; }
              .stAppViewContainer { padding-top: 0 !important; }
              .stApp { overflow-x: clip; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.global_css_injected = True

    # --- Lógica de Autenticación ---
    if not st.session_state.logged_in:
        st.sidebar.header("🔒 Acceso de Usuario")
        auth_option = st.sidebar.radio("Selecciona una opción", ["Iniciar Sesión", "Registrarse"])

        if auth_option == "Iniciar Sesión":
            username = st.sidebar.text_input("Usuario", key="login_username")
            password = st.sidebar.text_input("Contraseña", type="password", key="login_password")
            if st.sidebar.button("Iniciar Sesión"):
                user = get_user(username)
                if user and check_password_hash(user['password'], password):
                    st.session_state.logged_in = True
                    st.session_state.username = user['username']
                    st.session_state.user_role_id = user['role_id']
                    st.session_state.user_id = user['id']
                    
                    # Guardar sesión persistente
                    save_session_to_storage(user['id'], user['username'], user['role_id'])
                    
                    st.toast(f"Bienvenido, {st.session_state.username}!", icon="👋")
                    st.rerun()
                else:
                    st.toast("Usuario o contraseña incorrectos.", icon="❌")
        else: # Registrarse
            new_username = st.sidebar.text_input("Nuevo Usuario", key="register_username")
            new_password = st.sidebar.text_input("Nueva Contraseña", type="password", key="register_password")
            confirm_password = st.sidebar.text_input("Confirmar Contraseña", type="password", key="register_confirm_password")
            
            roles = get_roles()
            role_names = {role['name']: role['id'] for role in roles}
            selected_role_name = st.sidebar.selectbox("Rol", list(role_names.keys()))
            selected_role_id = role_names[selected_role_name]

            if st.sidebar.button("Registrarse"):
                if new_password != confirm_password:
                    st.toast("Las contraseñas no coinciden.", icon="❌")
                elif get_user(new_username):
                    st.toast("El nombre de usuario ya existe.", icon="❌")
                else:
                    hashed_password = generate_password_hash(new_password)
                    create_user(new_username, hashed_password, selected_role_id)
                    st.toast("Usuario registrado exitosamente. Ahora puedes iniciar sesión.", icon="✅")
    else: # Usuario logueado
        # --- BARRA LATERAL SIMPLIFICADA ---
        with st.sidebar:
            # Mostrar estado de sesión con indicador de tiempo
            import time
            if 'persistent_session' in st.session_state:
                session_timestamp = st.session_state['persistent_session'].get('timestamp', 0)
                current_time = int(time.time())
                time_remaining = 600 - (current_time - session_timestamp)  # 10 minutos en segundos
                hours_remaining = time_remaining // 3600
                minutes_remaining = (time_remaining % 3600) // 60
                
                if time_remaining > 0:
                    st.success(f"✅ Sesión activa: {st.session_state.username}")
                    st.caption(f"⏰ Tiempo restante: {hours_remaining}h {minutes_remaining}m")
                else:
                    st.warning("⚠️ Sesión expirada")
            else:
                st.success(f"Sesión iniciada como: {st.session_state.username}")
            
            # Botón Logout siempre visible para usuarios logueados
            if st.button("Cerrar Sesión", use_container_width=True):
                # Guardar el nombre de usuario para el mensaje de despedida
                username = st.session_state.get("username", "Usuario")
                
                # Limpiar sesión persistente
                clear_persistent_session()
                
                # Limpiar session_state
                st.session_state.clear()
                st.toast(f"Sesión cerrada. ¡Hasta pronto, {username}!", icon="👋")
                st.rerun()

            st.header("⚙️ Configuración Global")
            provider = st.selectbox("Proveedor de IA", list(API_PROVIDERS.keys()) + ["Ninguno (manual)"])
            model = st.selectbox(f"Modelo de {provider}", API_PROVIDERS.get(provider, {}).get("models", []), index=0) if provider != "Ninguno (manual)" else None
            
            st.markdown("---")
            st.header("💾 Gestión de Proyectos")
            
            # Mostrar resumen de datos del proyecto actual
            if st.session_state.get('loaded_project_id'):
                with st.expander("📊 Resumen de Datos del Proyecto", expanded=False):
                    data_summary = get_project_data_summary()
                    for key, value in data_summary.items():
                        if value > 0:
                            st.metric(key, value)
                        else:
                            st.text(f"{key}: Sin datos")
            
            projects = get_project_list(st.session_state.user_id)
            project_options = {p['id']: p['name'] for p in projects}
            # Usar st.session_state.selected_project_from_selectbox para controlar el valor del selectbox
            # Esto permite que el valor persista incluso si loaded_project_id cambia temporalmente
            current_selected_index = None
            if st.session_state.loaded_project_id in project_options:
                current_selected_index = list(project_options.keys()).index(st.session_state.loaded_project_id)
            
            selected_id = st.selectbox(
                "Cargar Proyecto Existente",
                options=list(project_options.keys()),
                format_func=project_options.get,
                index=current_selected_index,
                placeholder="Selecciona un proyecto...",
                key="project_selector_box" # Añadir una clave para el selectbox
            )
            
            st.session_state.project_name = st.text_input(
                "Nombre del Proyecto Actual",
                value=st.session_state.project_name,
                key="project_name_input"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Guardar", use_container_width=True, type="primary", disabled=(not st.session_state.project_name or st.session_state.tasks_df.empty)):
                    # Verificar sesión antes de guardar
                    if not check_session_validity():
                        st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
                        st.stop()
                    
                    # Registrar actividad del usuario
                    add_session_activity()
                    
                    try:
                        # Aplicar cambios pendientes de la tabla WBS antes de guardar
                        apply_pending_wbs_changes()
                        
                        # Preparar todos los datos del proyecto para guardar
                        complete_project_data = {
                            'tasks_df': st.session_state.tasks_df,
                            'detailed_df': st.session_state.detailed_df,
                            'additional_costs_df': st.session_state.additional_costs,
                            'risks_df': st.session_state.risks_df,
                            'issues_df': st.session_state.issues_df,
                            'sprints_df': st.session_state.sprints_df,
                            'change_requests_df': st.session_state.change_requests_df,
                            'attachments_df': st.session_state.attachments_df,
                            'okrs_df': st.session_state.okrs_df,
                            'baselines_df': st.session_state.baselines_df,
                            'baseline_tasks_dfs': st.session_state.baseline_tasks_dfs,
                            'project_prefs_df': st.session_state.project_prefs_df,
                            'resource_capacity_dfs': st.session_state.resource_capacity_dfs
                        }
                        
                        save_complete_project_to_db(
                            st.session_state.project_name,
                            st.session_state.project_description,
                            complete_project_data
                        )
                        st.toast(f"Proyecto '{st.session_state.project_name}' guardado con todos los datos relacionados.", icon="✅")
                    except Exception as e:
                        st.toast(f"Error al guardar: {str(e)}", icon="❌")
            with col2:
                 if selected_id and st.button("Eliminar", use_container_width=True):
                    # Verificar sesión antes de eliminar
                    if not check_session_validity():
                        st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
                        st.stop()
                    
                    # Registrar actividad del usuario
                    add_session_activity()
                    
                    try:
                        delete_project_from_db(selected_id)
                        st.toast(f"Proyecto '{project_options[selected_id]}' eliminado.", icon="🗑️")
                        
                        # Limpiar solo los datos del proyecto, NO la sesión del usuario
                        project_data_keys = [
                            'project_name', 'project_description', 'tasks_df', 'detailed_df', 
                            'additional_costs', 'risks_df', 'issues_df', 'sprints_df', 
                            'change_requests_df', 'attachments_df', 'okrs_df', 'baselines_df', 
                            'baseline_tasks_dfs', 'project_prefs_df', 'resource_capacity_dfs',
                            'loaded_project_id'
                        ]
                        for key in project_data_keys:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error eliminando proyecto: {str(e)}")

        # --- CONFIGURACIÓN EN PÁGINA PRINCIPAL ---
        config_col1, config_col2 = st.columns(2)
        with config_col1:
            with st.expander("👤 Configuración de Perfiles y Costes"):
                if 'available_profiles' not in st.session_state:
                    st.session_state.available_profiles = ["Project Manager", "Developer", "Designer", "QA", "Analyst", "Sin Asignar"]
                
                selected_profiles = st.multiselect(
                    "Perfiles disponibles en este proyecto",
                    st.session_state.available_profiles,
                    default=st.session_state.available_profiles,
                    key="profile_selector"
                )
                
                new_profile_col1, new_profile_col2 = st.columns([3,1])
                new_profile = new_profile_col1.text_input("Agregar nuevo perfil", label_visibility="collapsed", placeholder="Nombre del nuevo perfil")
                if new_profile_col2.button("Agregar") and new_profile:
                    if new_profile not in st.session_state.available_profiles:
                        st.session_state.available_profiles.append(new_profile)
                        st.rerun()
                
                profile_costs = {}
                for profile in selected_profiles:
                    profile_costs[profile] = st.number_input(
                        f"Coste por hora para {profile}",
                        min_value=0.0,
                        value=st.session_state.get(f"cost_{profile}", 50.0 if profile == "Project Manager" else 40.0),
                        step=1.0,
                        format="%.2f",
                        key=f"cost_{profile}"
                    )
        
        with config_col2:
            with st.expander("🔔 Notificaciones"):
                user_notifications = get_notifications(st.session_state.user_id)
                unread_notifications = [n for n in user_notifications if not n['is_read']]
                
                if unread_notifications:
                    st.info(f"Tienes {len(unread_notifications)} notificaciones nuevas.")
                    for notif in unread_notifications[:3]: # Mostrar solo las 3 más recientes
                        st.markdown(f"<small>_{pd.to_datetime(notif['timestamp']).strftime('%Y-%m-%d %H:%M')}_: {notif['message']}</small>", unsafe_allow_html=True)
                        if st.button(f"Marcar como leída ({notif['id']})", key=f"read_notif_{notif['id']}"):
                            mark_notification_as_read(notif['id'])
                            st.rerun()
                else:
                    st.success("No tienes notificaciones nuevas.")
                
                if st.button("Ver historial completo"):
                    st.session_state.show_all_notifications = not st.session_state.get("show_all_notifications", False)

                if st.session_state.get("show_all_notifications"):
                    for notif in user_notifications:
                        status = "✅" if notif['is_read'] else "📧"
                        st.markdown(f"{status} _{pd.to_datetime(notif['timestamp']).strftime('%Y-%m-%d %H:%M')}_: {notif['message']}")

        # Lógica de carga/creación de proyecto
        # Si el usuario selecciona un proyecto diferente en el selectbox
        if selected_id != st.session_state.get("loaded_project_id"):
            if selected_id: # Si se ha seleccionado un proyecto
                try:
                    st.session_state.loaded_project_id = selected_id
                    # Usar la función completa de carga
                    complete_project_data = load_complete_project_from_db(selected_id, profile_costs)
                    if complete_project_data:
                        st.session_state.update(
                            project_name=complete_project_data.get('project_name', ""),
                            project_description=complete_project_data.get('project_description', ""),
                            tasks_df=complete_project_data.get('tasks_df', pd.DataFrame()),
                            detailed_df=complete_project_data.get('detailed_df', pd.DataFrame()),
                            additional_costs=complete_project_data.get('additional_costs_df', pd.DataFrame({"Description": [], "Cost": []})),
                            # Cargar todos los datos relacionados
                            risks_df=complete_project_data.get('risks_df', pd.DataFrame()),
                            issues_df=complete_project_data.get('issues_df', pd.DataFrame()),
                            sprints_df=complete_project_data.get('sprints_df', pd.DataFrame()),
                            change_requests_df=complete_project_data.get('change_requests_df', pd.DataFrame()),
                            attachments_df=complete_project_data.get('attachments_df', pd.DataFrame()),
                            okrs_df=complete_project_data.get('okrs_df', pd.DataFrame()),
                            baselines_df=complete_project_data.get('baselines_df', pd.DataFrame()),
                            baseline_tasks_dfs=complete_project_data.get('baseline_tasks_dfs', {}),
                            project_prefs_df=complete_project_data.get('project_prefs_df', pd.DataFrame()),
                            resource_capacity_dfs=complete_project_data.get('resource_capacity_dfs', {})
                        )
                        # Mostrar resumen de datos cargados
                        data_summary = get_project_data_summary()
                        loaded_items = [f"{k}: {v}" for k, v in data_summary.items() if v > 0]
                        summary_text = f"Proyecto '{complete_project_data.get('project_name')}' cargado con: {', '.join(loaded_items)}" if loaded_items else f"Proyecto '{complete_project_data.get('project_name')}' cargado (sin datos relacionados)"
                        st.toast(summary_text, icon="✅")
                    else:
                        st.error("No se pudo cargar el proyecto seleccionado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error cargando proyecto: {str(e)}")
            else: # Si se deselecciona el proyecto (selected_id es None)
                st.session_state.loaded_project_id = None
                st.session_state.project_name = ""
                st.session_state.project_description = ""
                st.session_state.tasks_df = pd.DataFrame()
                st.session_state.detailed_df = pd.DataFrame()
                st.session_state.additional_costs = pd.DataFrame({"Description": [], "Cost": []})
                # Limpiar todos los datos relacionados
                st.session_state.risks_df = pd.DataFrame()
                st.session_state.issues_df = pd.DataFrame()
                st.session_state.sprints_df = pd.DataFrame()
                st.session_state.change_requests_df = pd.DataFrame()
                st.session_state.attachments_df = pd.DataFrame()
                st.session_state.okrs_df = pd.DataFrame()
                st.session_state.baselines_df = pd.DataFrame()
                st.session_state.baseline_tasks_dfs = {}
                st.session_state.project_prefs_df = pd.DataFrame()
                st.session_state.resource_capacity_dfs = {}
                st.toast("Proyecto deseleccionado.", icon="✅")
                st.rerun()
        
        # Se elimina el bloque `elif` que causaba la creación automática y el bucle de recarga.
        # La creación y guardado de proyectos ahora se maneja exclusivamente a través del botón "Guardar".

        st.markdown("---")

        # --- ESTRUCTURA DE PESTAÑAS PRINCIPAL ---
        tabs = st.tabs([
            "📝 Definición y Generación",
            "📋 Plan de Tareas (WBS)",
            "📌 Tablero Kanban",
            "⚠️ Riesgos e Incidencias",
            "📊 Análisis y Documentos"
        ])
        tab_definition, tab_wbs, tab_kanban, tab_risk, tab_analysis = tabs

        is_name_empty = not st.session_state.project_name.strip()

        with tab_definition:
            st.header("1. Definición del Proyecto")
            
            # Lógica para mostrar mensajes post-rerun
            if "success_message" in st.session_state:
                st.success(st.session_state.success_message)
                del st.session_state.success_message

            st.session_state.project_description = st.text_area("Describe el proyecto o pega el contenido aquí", value=st.session_state.project_description, height=200)
            
            if is_name_empty:
                st.warning("⚠️ **Debe establecer un 'Nombre del Proyecto Actual' en la barra lateral antes de generar el plan.**")
            
            col1, col2 = st.columns([1,1])
            with col1:
                uploaded_file = st.file_uploader("O sube un documento de requisitos", type=["pdf", "txt", "md"], key="pdf_uploader")
                if uploaded_file and st.session_state.get('processed_file_id') != uploaded_file.name:
                    content = ""
                    if uploaded_file.type == "application/pdf":
                        content = get_pdf_text(uploaded_file.getvalue())
                    else:
                        content = uploaded_file.getvalue().decode("utf-8")
                    
                    if content:
                        st.session_state.project_description = content
                        st.session_state.processed_file_id = uploaded_file.name
                        st.toast("Contenido del documento cargado exitosamente. Ahora puedes generar el plan de proyecto.", icon="✅")
            
            with col2:
                st.write("") # Espaciador
                st.write("") # Espaciador
                if st.button("🚀 Generar Plan de Proyecto Completo", use_container_width=True, type="primary", disabled=(not st.session_state.project_name.strip() or provider == "Ninguno (manual)")):
                    if not st.session_state.project_description.strip():
                        st.error("Por favor, describe el proyecto para empezar.", icon="🚨")
                        st.session_state.project_description = st.session_state.project_description or ""
                    elif provider == "Ninguno (manual)":
                        st.error("Selecciona un proveedor de IA para generar el plan.", icon="🚨")
                    else:
                        wbs_generated = False
                        with st.spinner("Paso 1/2: Generando WBS...") as spinner:
                            try:
                                valid_profiles = ", ".join(profile_costs.keys())
                                prompt = PROMPT_WBS_JSON.format(input_text=st.session_state.project_description, valid_profiles=valid_profiles)
                                wbs_text = call_llm_api(provider, model, prompt, expect_json=(provider == "Gemini"))
                                df_wbs = parse_json_wbs(wbs_text)
                                sanitized_df = sanitize_tasks_df(df_wbs, list(profile_costs.keys()))
                                dated_df, problem_ids = calculate_task_dates(sanitized_df)
                                
                                required_cols = {'Priority': 'Media', 'Status': 'No Iniciada', 'Progress': 0.0, 'Actual_Start': pd.NaT, 'Actual_Finish': pd.NaT}
                                for col, default in required_cols.items():
                                    if col not in dated_df.columns: dated_df[col] = default
                                
                                dated_df = calculate_costs(dated_df, profile_costs)
                                st.session_state.tasks_df = dated_df
                                st.success("WBS generado y calculado."); wbs_generated = True
                            except Exception as e: st.error(f"Error al generar WBS: {e}")

                        if wbs_generated:
                            with st.spinner("Paso 2/2: Generando desglose detallado..."):
                                try:
                                    tasks_str = "\n".join(f"[{r.TaskID}] {r.Task}" for _, r in st.session_state.tasks_df.iterrows())
                                    detailed_text = call_llm_api(provider, model, PROMPT_DETAILED_SUBTASKS.format(task_list_str=tasks_str))
                                    st.session_state.detailed_df = parse_detailed_subtasks(detailed_text)
                                    # Guardar el proyecto automáticamente después de la generación exitosa
                                    project_id = save_project_to_db(
                                        st.session_state.project_name,
                                        st.session_state.project_description,
                                        st.session_state.tasks_df,
                                        st.session_state.detailed_df,
                                        st.session_state.additional_costs
                                    )
                                    
                                    project_name_for_message = st.session_state.project_name
                                    st.session_state.success_message = f"✅ ¡Proyecto '{project_name_for_message}' se ha generado con éxito! Cárgalo desde el menú lateral para continuar trabajando con el Proyecto."
                                    
                                    # Limpiar el estado para permitir la carga del nuevo proyecto o la creación de otro
                                    st.session_state.project_name = ""
                                    st.session_state.project_description = ""
                                    st.session_state.tasks_df = pd.DataFrame()
                                    st.session_state.detailed_df = pd.DataFrame()
                                    st.session_state.additional_costs = pd.DataFrame({"Description": [], "Cost": []})
                                    st.session_state.loaded_project_id = None
                                    if 'processed_file_id' in st.session_state:
                                        del st.session_state['processed_file_id']
                                    
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error generando desglose: {e}")
                                    st.toast("❌ Error en generación de detalles", icon="❌")

        with tab_wbs:
            st.header("2. Plan de Tareas (WBS)")
            if not st.session_state.tasks_df.empty:
                df_display = st.session_state.tasks_df.copy()
                column_mapping = {
                    'TaskID': 'ID', 'Task': 'Tarea', 'Priority': 'Prioridad', 'Duration_hours': 'Horas', 'Duration_days': 'Días',
                    'Dependencies': 'Dependencias', 'Resource': 'Recurso', 'Status': 'Estado', 'Progress': 'Progreso',
                    'Start': 'Inicio', 'Finish': 'Fin', 'Actual_Start': 'Inicio Real', 'Actual_Finish': 'Fin Real', 'Cost': 'Coste',
                    'Sprint': 'Sprint', 'Story_Points': 'Puntos', 'Actual_Cost': 'Coste Real'
                }
                
                df_display = df_display.rename(columns=column_mapping)
                display_cols = [col for col in column_mapping.values() if col in df_display.columns]
                df_display["Dependencias"] = df_display["Dependencias"].apply(lambda x: ", ".join(map(str, x)) if isinstance(x, list) else (x or ""))
                
                edited_df = st.data_editor(
                    df_display[display_cols], num_rows="dynamic", use_container_width=True, height=400, key="wbs_editor",
                    column_config={
                        "Prioridad": st.column_config.SelectboxColumn(options=["Alta", "Media", "Baja"], required=True),
                        "Estado": st.column_config.SelectboxColumn(options=["No Iniciada", "En Progreso", "Completada", "Bloqueada"], required=True),
                        "Progreso": st.column_config.NumberColumn("Progreso", format="%d%%", min_value=0, max_value=100, step=1),
                        "Inicio Real": st.column_config.DateColumn(format="YYYY-MM-DD"),
                        "Fin Real": st.column_config.DateColumn(format="YYYY-MM-DD"),
                        "Recurso": st.column_config.SelectboxColumn(options=list(profile_costs.keys()), required=True),
                        "Sprint": st.column_config.TextColumn(),
                        "Puntos": st.column_config.NumberColumn(min_value=0, step=1),
                        "Coste Real": st.column_config.NumberColumn(format="€%.2f", min_value=0.0, step=1.0),
                    }
                )

                # Guardar el DataFrame editado en session_state para uso posterior
                st.session_state['edited_df'] = edited_df

                if st.button("Recalcular Fechas y Costes", use_container_width=True):
                    try:
                        inv_map = {v: k for k, v in column_mapping.items()}
                        df_to_recalc = edited_df.rename(columns=inv_map)
                        df_to_recalc["Duration_hours"] = pd.to_numeric(df_to_recalc["Horas"], errors='coerce').fillna(8)
                        df_to_recalc["Dependencies"] = df_to_recalc["Dependencies"].str.split(r'[ ,]+').apply(lambda x: [i for i in x if i])
                        # Normalizar nuevos campos
                        if "Story_Points" in df_to_recalc.columns:
                            df_to_recalc["Story_Points"] = pd.to_numeric(df_to_recalc["Story_Points"], errors='coerce').fillna(0)
                        if "Actual_Cost" in df_to_recalc.columns:
                            df_to_recalc["Actual_Cost"] = pd.to_numeric(df_to_recalc["Actual_Cost"], errors='coerce').fillna(0.0)
                        
                        recalculated_df, problem_ids = calculate_task_dates(df_to_recalc)
                        final_df = calculate_costs(recalculated_df, profile_costs)
                        st.session_state.tasks_df = final_df
                        st.success("Plan recalculado.")
                        st.rerun()
                    except Exception as e: st.error(f"Error en los datos introducidos: {e}")

                with st.expander("🧮 Nivelación Automática con Calendarios"):
                    st.markdown("Define capacidad diaria por recurso, fines de semana y festivos, y ejecuta la nivelación.")
                    resources = st.session_state.tasks_df['Resource'].dropna().unique().tolist()
                    # Cargar preferencias guardadas
                    cap_map = {}
                    loaded_caps = {}
                    loaded_weekends = True
                    loaded_holidays_str = ""
                    if st.session_state.get("loaded_project_id"):
                        try:
                            prefs = get_db_connection().cursor().execute("SELECT weekends_off, holidays, capacities_json FROM project_prefs WHERE project_id = ?", (st.session_state.loaded_project_id,)).fetchone()
                            if prefs:
                                loaded_weekends = bool(prefs['weekends_off'])
                                loaded_holidays_str = prefs['holidays'] or ""
                                loaded_caps = json.loads(prefs['capacities_json'] or "{}")
                        except Exception:
                            pass
                    for r in resources:
                        cap_map[r] = st.number_input(f"Capacidad diaria de {r} (horas)", min_value=0.0, value=float(loaded_caps.get(r, 8.0)), step=0.5, key=f"cap_{r}")
                    weekends_off = st.checkbox("Excluir fines de semana", value=loaded_weekends)
                    holidays_input = st.text_input("Festivos (YYYY-MM-DD separados por comas)", value=loaded_holidays_str)
                    holidays_set = set()
                    if holidays_input.strip():
                        try:
                            holidays_set = set(pd.to_datetime([h.strip() for h in holidays_input.split(',') if h.strip()]))
                        except Exception:
                            st.warning("Formato de festivos inválido. Ej: 2025-12-25, 2026-01-01")
                    save_prefs_col1, save_prefs_col2 = st.columns(2)
                    with save_prefs_col1:
                        if st.button("Guardar Preferencias", use_container_width=True) and st.session_state.get("loaded_project_id"):
                            try:
                                conn2 = get_db_connection()
                                caps_json = json.dumps({r: cap_map[r] for r in resources})
                                conn2.cursor().execute("INSERT INTO project_prefs (project_id, weekends_off, holidays, capacities_json) VALUES (?, ?, ?, ?) ON CONFLICT(project_id) DO UPDATE SET weekends_off=excluded.weekends_off, holidays=excluded.holidays, capacities_json=excluded.capacities_json", (st.session_state.loaded_project_id, int(weekends_off), holidays_input, caps_json))
                                conn2.commit()
                                st.success("Preferencias guardadas")
                            except Exception as e:
                                st.error(f"Error guardando preferencias: {e}")
                    if st.button("Ejecutar Nivelación", use_container_width=True):
                        try:
                            # Guardar snapshot para deshacer
                            st.session_state['_pre_level_snapshot'] = st.session_state.tasks_df.copy()
                            leveled = level_schedule_with_calendars(st.session_state.tasks_df, cap_map, holidays_set, weekends_off)
                            st.session_state.tasks_df = calculate_costs(leveled, profile_costs)
                            st.success("Nivelación aplicada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error en nivelación: {e}")
                    if st.button("Deshacer Nivelación", use_container_width=True, disabled=('_pre_level_snapshot' not in st.session_state)):
                        st.session_state.tasks_df = st.session_state.get('_pre_level_snapshot', st.session_state.tasks_df)
                        st.session_state.pop('_pre_level_snapshot', None)
                        st.success("Nivelación revertida.")
                        st.rerun()

                if not st.session_state.detailed_df.empty:
                    with st.expander("📋 Ver Desglose Detallado de Tareas"):
                        detailed_display = st.session_state.detailed_df.rename(columns={"TaskID": "ID Tarea", "Task": "Tarea Principal", "Detailed Step": "Subtarea"})
                        st.dataframe(detailed_display, use_container_width=True, hide_index=True)
            else:
                st.info("👆 Genera un plan de proyecto en la pestaña 'Definición y Generación' o carga uno existente desde la barra lateral.")

        with tab_kanban:
            st.header("3. Tablero Kanban Interactivo")
            if not st.session_state.tasks_df.empty:
                def update_kanban_task(task_id: str, new_status: str):
                    task_index = st.session_state.tasks_df.index[st.session_state.tasks_df['TaskID'] == task_id]
                    if not task_index.empty:
                        original_status = st.session_state.tasks_df.loc[task_index[0], 'Status']
                        if original_status != new_status:
                            st.session_state.tasks_df.loc[task_index[0], 'Status'] = new_status
                            task_name = st.session_state.tasks_df.loc[task_index[0], 'Task']
                            add_notification(st.session_state.user_id, st.session_state.loaded_project_id, f"Tarea '{task_name}' movida a '{new_status}'.")
                            save_project_to_db(st.session_state.project_name, st.session_state.project_description, st.session_state.tasks_df, st.session_state.detailed_df, st.session_state.additional_costs)
                            st.toast(f"Tarea '{task_id}' movida a '{new_status}'.", icon="✅")

                task_statuses = ["No Iniciada", "En Progreso", "Completada", "Bloqueada"]
                event_data = None

                # La vista nativa de Kanban siempre está activa
                cols = st.columns(len(task_statuses))
                for idx, status in enumerate(task_statuses):
                    with cols[idx]:
                        st.subheader(status)
                        col_tasks = st.session_state.tasks_df[st.session_state.tasks_df['Status'] == status]
                        if col_tasks.empty:
                            st.info("Arrastra/mueve tareas aquí (usar selector)")
                        for _, task_row in col_tasks.iterrows():
                            box = st.container(border=True)
                            with box:
                                st.markdown(f"**ID:** {task_row['TaskID']}  ")
                                st.markdown(f"**Tarea:** {task_row['Task']}")
                                st.markdown(f"**Recurso:** {task_row['Resource']}")
                                start_date = task_row['Start'].strftime('%d/%m/%Y') if pd.notnull(task_row['Start']) else '—'
                                finish_date = task_row['Finish'].strftime('%d/%m/%Y') if pd.notnull(task_row['Finish']) else '—'
                                st.caption(f"Inicio: {start_date}  |  Fin: {finish_date}")
                                st.progress(int(task_row.get('Progress', 0)))
                                new_stat = st.selectbox(
                                    "Mover a",
                                    task_statuses,
                                    index=task_statuses.index(status),
                                    key=f"mv_{task_row['TaskID']}"
                                )
                                if new_stat != status:
                                    update_kanban_task(task_row['TaskID'], new_stat)
                                    st.rerun()
                # Fin de vista nativa; no se renderiza HTML extra

                if isinstance(event_data, dict):
                    update_kanban_task(event_data.get("taskId"), event_data.get("newStatus"))
                    st.rerun()
            else:
                st.info("👆 Genera un plan de proyecto para poder usar el tablero Kanban.")

        with tab_risk:
            try:
                st.header("⚠️ Gestión de Riesgos e Incidencias")
                if st.session_state.get("loaded_project_id"):
                    conn = get_db_connection()
                    # Sugerir riesgos por IA
                    with st.expander("🤖 Sugerir Riesgos con IA"):
                        if st.button("Generar propuesta de riesgos", disabled=(provider == "Ninguno (manual)")):
                            try:
                                df_tmp = st.session_state.tasks_df if not st.session_state.tasks_df.empty else pd.DataFrame()
                                task_list_str = "\n".join(f"- {r.Task}" for _, r in df_tmp.iterrows())
                                risks_json_text = call_llm_api(provider, model, PROMPT_RISK_SUGGESTION.format(project_description=st.session_state.project_description, task_list=task_list_str), expect_json=(provider=="Gemini"))
                                # Intentar extraer JSON
                                m = re.search(r"```(?:json)?\s*(.*?)```", risks_json_text, re.DOTALL | re.IGNORECASE)
                                json_str = m.group(1).strip() if m else risks_json_text
                                risks_list = json.loads(json_str)
                                inserted = 0
                                cur = conn.cursor()
                                for item in risks_list:
                                    desc = item.get('description')
                                    prob = float(item.get('probability', 0))
                                    impact = item.get('impact', 'Medio')
                                    mitig = item.get('mitigation_plan', '')
                                    if not desc:
                                        continue
                                    cur.execute("INSERT INTO risks (project_id, description, probability, impact, mitigation_plan) VALUES (?, ?, ?, ?, ?)", (st.session_state.loaded_project_id, desc, prob, impact, mitig))
                                    inserted += 1
                                conn.commit()
                                st.success(f"{inserted} riesgos sugeridos insertados")
                            except Exception as e:
                                st.error(f"Error generando riesgos: {e}")
                    
                    risk_management.render_risk_management_ui(conn, st.session_state.loaded_project_id)
                else:
                    st.info("👆 Primero carga o crea un proyecto para gestionar riesgos e incidencias.", icon="ℹ️")
            except Exception as e:
                st.error("Se produjo un error al renderizar Riesgos e Incidencias.")
                st.exception(e)
                
        with tab_analysis:
            st.header("5. Análisis y Documentación")
            if not st.session_state.tasks_df.empty:
                df_show = st.session_state.tasks_df
                # Asegurar columnas usadas en análisis
                if 'Sprint' not in df_show.columns:
                    df_show['Sprint'] = ''
                if 'Story_Points' not in df_show.columns:
                    df_show['Story_Points'] = 0
                if 'Status' not in df_show.columns:
                    df_show['Status'] = 'No Iniciada'
                crit_ids, duration = calculate_critical_path(df_show)
                work_cost = df_show["Cost"].sum() if "Cost" in df_show.columns else 0
                additional_cost = pd.to_numeric(st.session_state.additional_costs.get("Cost"), errors='coerce').fillna(0).sum()
                
                st.subheader("Visión General del Proyecto")
                c1, c2, c3 = st.columns(3)
                c1.metric("Coste Total Estimado", f"€{work_cost + additional_cost:,.2f}")
                c2.metric("Duración Total Estimada", f"{duration} días")
                c3.metric("Tareas en Ruta Crítica", f"{len(crit_ids)}")


                with st.expander("📈 Diagrama de Gantt", expanded=True):
                    gantt_fig = create_gantt_chart(df_show, crit_ids)
                    if gantt_fig: st.plotly_chart(gantt_fig, use_container_width=True)
                    else: st.warning("No se pudo generar el Diagrama de Gantt.")





                # Simulación Monte Carlo (duración/coste)
                with st.expander("🎲 Simulación Monte Carlo"):
                    # Cargar preferencias guardadas
                    sims_default, var_default = 1000, 20
                    if st.session_state.get('loaded_project_id'):
                        try:
                            prefs = get_db_connection().cursor().execute("SELECT mc_sims, mc_variability_pct FROM project_prefs WHERE project_id = ?", (st.session_state.loaded_project_id,)).fetchone()
                            if prefs:
                                sims_default = int(prefs['mc_sims'] or sims_default)
                                var_default = int(prefs['mc_variability_pct'] or var_default)
                        except Exception:
                            pass
                    sims = st.slider("Nº simulaciones", 100, 5000, int(sims_default), step=100)
                    var_pct = st.slider("Variabilidad % (sigma)", 0, 50, int(var_default))
                    if st.button("Guardar Parámetros Monte Carlo") and st.session_state.get('loaded_project_id'):
                        try:
                            connp = get_db_connection()
                            connp.cursor().execute("INSERT INTO project_prefs (project_id, mc_sims, mc_variability_pct) VALUES (?, ?, ?) ON CONFLICT(project_id) DO UPDATE SET mc_sims=excluded.mc_sims, mc_variability_pct=excluded.mc_variability_pct", (st.session_state.loaded_project_id, int(sims), int(var_pct)))
                            connp.commit(); st.success("Parámetros guardados")
                        except Exception as e:
                            st.error(f"Error guardando parámetros: {e}")
                    if st.button("Restaurar Monte Carlo (1000 sims, 20%)") and st.session_state.get('loaded_project_id'):
                        try:
                            connp = get_db_connection()
                            connp.cursor().execute("INSERT INTO project_prefs (project_id, mc_sims, mc_variability_pct) VALUES (?, ?, ?) ON CONFLICT(project_id) DO UPDATE SET mc_sims=1000, mc_variability_pct=20", (st.session_state.loaded_project_id, 1000, 20))
                            connp.commit(); st.success("Parámetros restaurados")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error restaurando: {e}")
                    if st.button("Ejecutar Monte Carlo"):
                        if df_show.empty:
                            st.warning("No hay tareas")
                        else:
                            rng = np.random.default_rng(42)
                            base_days = df_show['Duration_days'].fillna(1).astype(float).values
                            base_cost = pd.to_numeric(df_show.get('Cost', 0), errors='coerce').fillna(0).values
                            dur_samples = []
                            cost_samples = []
                            sigma = var_pct/100.0
                            for _ in range(sims):
                                factor = rng.lognormal(mean=0.0, sigma=sigma, size=len(base_days))
                                
                                # Aplicar variabilidad a las duraciones de las tareas individuales
                                simulated_task_durations = np.maximum(1, np.round(base_days * factor))
                                
                                # Crear un DataFrame temporal para recalcular las fechas con las duraciones simuladas
                                # Es crucial usar una copia para no modificar el df_show original
                                temp_df_tasks = df_show.copy()
                                temp_df_tasks['Duration_days'] = simulated_task_durations
                                
                                # Recalcular las fechas de las tareas y la duración del proyecto
                                # Se asume que calculate_task_dates devuelve el DataFrame actualizado y la duración total del proyecto
                                # Si calculate_task_dates no devuelve la duración total, se necesitaría una función auxiliar
                                recalculated_df, _ = calculate_task_dates(temp_df_tasks)
                                
                                # La duración del proyecto es la diferencia entre la fecha de fin máxima y la fecha de inicio mínima
                                if not recalculated_df.empty and pd.notna(recalculated_df['Start'].min()) and pd.notna(recalculated_df['Finish'].max()):
                                    dur = (recalculated_df['Finish'].max() - recalculated_df['Start'].min()).days + 1
                                else:
                                    dur = 0 # En caso de que no haya tareas o fechas válidas
                                
                                cost = np.sum(base_cost * factor) # El cálculo del coste sigue siendo una suma directa
                                
                                dur_samples.append(dur)
                                cost_samples.append(cost)
                            
                            p50_dur = np.percentile(dur_samples, 50); p80_dur = np.percentile(dur_samples, 80)
                            p50_cost = np.percentile(cost_samples, 50); p80_cost = np.percentile(cost_samples, 80)

                            # Almacenar resultados en session_state para el informe
                            st.session_state['mc_results'] = {
                                'p50_dur': p50_dur, 'p80_dur': p80_dur,
                                'p50_cost': p50_cost, 'p80_cost': p80_cost,
                                'sims': sims, 'sigma_pct': var_pct
                            }

                            c1, c2 = st.columns(2)
                            c1.metric("Duración P50 / P80 (días)", f"{int(p50_dur)} / {int(p80_dur)}")
                            c2.metric("Coste P50 / P80", f"€{p50_cost:,.0f} / €{p80_cost:,.0f}")
                            fig_hist = go.Figure()
                            fig_hist.add_trace(go.Histogram(x=dur_samples, nbinsx=40, name='Duración'))
                            fig_hist.update_layout(title="Distribución de Duración (Monte Carlo)")
                            st.plotly_chart(fig_hist, use_container_width=True)

                    # Opción para descargar el informe de Monte Carlo
                    if 'mc_results' in st.session_state and st.button("📄 Descargar Informe Monte Carlo", use_container_width=True, disabled=(provider == "Ninguno (manual)")):
                        with st.spinner("Generando informe de Monte Carlo..."):
                            try:
                                mc_res = st.session_state['mc_results']
                                report_args = {
                                    'p50_dur': mc_res['p50_dur'], 'p80_dur': mc_res['p80_dur'],
                                    'p50_cost': mc_res['p50_cost'], 'p80_cost': mc_res['p80_cost'],
                                    'sims': mc_res['sims'], 'sigma_pct': mc_res['sigma_pct'],
                                    'project_description': st.session_state.project_description
                                }
                                report_text = call_llm_api(provider, model, PROMPT_MONTE_CARLO_REPORT.format(**report_args))
                                st.session_state['monte_carlo_report_doc'] = create_docx_from_text('Informe_Monte_Carlo', report_text)
                                st.toast("'Informe_Monte_Carlo.docx' generado.", icon="✅")
                            except Exception as e:
                                st.error(f"Error al generar informe de Monte Carlo: {e}")
                        if 'monte_carlo_report_doc' in st.session_state:
                            st.download_button("📥 Descargar Informe Monte Carlo", st.session_state['monte_carlo_report_doc'], 'Informe_Monte_Carlo.docx', use_container_width=True)


                # Heatmap de riesgos y CRs/RAID
                with st.expander("🛡️ Riesgos (Heatmap) y Cambios (CR) / RAID"):
                    conn = get_db_connection()
                    risks_df = pd.read_sql_query("SELECT * FROM risks WHERE project_id = ?", conn, params=(st.session_state.loaded_project_id,)) if st.session_state.get('loaded_project_id') else pd.DataFrame()
                    if not risks_df.empty:
                        # Mapear impacto a número y construir matriz 2D (probabilidad vs impacto)
                        impact_map = {'Bajo':1,'Medio':2,'Alto':3}
                        df_r = risks_df.copy(); df_r['impact_n'] = df_r['impact'].map(impact_map).fillna(1)
                        df_r['probability'] = pd.to_numeric(df_r['probability'], errors='coerce').fillna(0.0)
                        # Clustering k-means (k=3) sobre (probabilidad, impacto)
                        try:
                            from math import inf
                            from random import sample
                            points = df_r[['probability','impact_n']].to_numpy(dtype=float)
                            k = 3 if len(points) >= 3 else max(1, len(points))
                            # Inicialización aleatoria simple
                            centroids = points[sample(range(len(points)), k)] if len(points) >= k and k>0 else points
                            # Iterar k-means (pocas iteraciones)
                            for _ in range(10):
                                # asignación
                                labels = []
                                for p in points:
                                    dists = [np.linalg.norm(p-c) for c in centroids]
                                    labels.append(int(np.argmin(dists)))
                                # actualización
                                new_centroids = []
                                for ci in range(k):
                                    cluster_pts = points[np.array(labels)==ci]
                                    if len(cluster_pts)>0:
                                        new_centroids.append(cluster_pts.mean(axis=0))
                                    else:
                                        new_centroids.append(centroids[ci])
                                new_centroids = np.array(new_centroids)
                                if np.allclose(new_centroids, centroids):
                                    break
                                centroids = new_centroids
                            df_r['cluster'] = labels if len(points)>0 else []
                        except Exception:
                            df_r['cluster'] = 0

                        # Heatmap 2D (densidad) y centroides
                        fig2d = go.Figure()
                        fig2d.add_trace(go.Scatter(x=df_r['probability'], y=df_r['impact_n'], mode='markers', marker=dict(color=df_r['cluster'], colorscale='Viridis', size=10), text=df_r['description']))
                        # Cuadrantes
                        fig2d.add_shape(type='line', x0=0.5, x1=0.5, y0=0.5, y1=3.5, line=dict(dash='dash', color='gray'))
                        fig2d.add_shape(type='line', x0=0.0, x1=1.0, y0=2.0, y1=2.0, line=dict(dash='dash', color='gray'))
                        # Centroides
                        if 'cluster' in df_r.columns and len(df_r)>0:
                            for ci in sorted(df_r['cluster'].unique()):
                                cl = df_r[df_r['cluster']==ci]
                                if not cl.empty:
                                    fig2d.add_trace(go.Scatter(x=[cl['probability'].mean()], y=[cl['impact_n'].mean()], mode='markers+text', marker=dict(symbol='x', size=14, color='red'), text=[f'C{ci}'], textposition='top center'))
                        fig2d.update_layout(title='Riesgos: Probabilidad vs Impacto (clusters)', xaxis_title='Probabilidad', yaxis_title='Impacto (1-3)', yaxis=dict(tickmode='array', tickvals=[1,2,3], ticktext=['Bajo','Medio','Alto']))
                        st.plotly_chart(fig2d, use_container_width=True)
                        umbral = st.slider("Umbral de riesgo (prob*impact)", 0.0, 3.0, 1.5, 0.1)
                        high_risks = df_r[df_r['probability']*df_r['impact_n']>=umbral]
                        if not high_risks.empty:
                            st.warning(f"Riesgos sobre umbral: {len(high_risks)}")
                    st.subheader("Change Requests (CR)")
                    with st.form("cr_form"):
                        cr_title = st.text_input("Título")
                        cr_desc = st.text_area("Descripción")
                        cr_impact = st.text_area("Impacto")
                        if st.form_submit_button("Guardar CR") and st.session_state.get('loaded_project_id'):
                            cur = conn.cursor()
                            cur.execute("INSERT INTO change_requests (project_id, title, description, impact) VALUES (?, ?, ?, ?)", (st.session_state.loaded_project_id, cr_title, cr_desc, cr_impact))
                            conn.commit(); st.success("CR guardado")
                    crs = pd.read_sql_query("SELECT id, title, status, created_at FROM change_requests WHERE project_id = ? ORDER BY created_at DESC", conn, params=(st.session_state.loaded_project_id,)) if st.session_state.get('loaded_project_id') else pd.DataFrame()
                    if not crs.empty:
                        st.dataframe(crs, use_container_width=True)
                    st.subheader("RAID (Vista Unificada)")
                    # R: risks ya mostrados; A: Assumptions (usar 'assumptions' en descripción del proyecto si existen), I: issues (tabla), D: dependencies (de tareas)
                    issues_df = pd.read_sql_query("SELECT description, severity, status FROM issues WHERE project_id = ?", conn, params=(st.session_state.loaded_project_id,)) if st.session_state.get('loaded_project_id') else pd.DataFrame()
                    dep_count = df_show['Dependencies'].apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
                    st.markdown(f"- Riesgos: {len(risks_df) if not risks_df.empty else 0}\n- Incidencias: {len(issues_df) if not issues_df.empty else 0}\n- Dependencias: {dep_count}\n- Asunciones: extraer manualmente del alcance/propuesta")



                # Nivelación básica de recursos (sugerencias)
                with st.expander("🧮 Nivelación de Recursos (sugerida)"):
                    if not df_show.empty:
                        load = df_show.groupby('Resource')['Duration_hours'].sum().reset_index().rename(columns={'Duration_hours':'hours'})
                        st.dataframe(load, use_container_width=True)
                        st.info("Próxima iteración: desplazar tareas automáticamente cuando la carga supere la capacidad del sprint")

                with st.expander("💶 Desglose de Costes"):
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.markdown("**Costes de Trabajo por Perfil**")
                        cost_by_profile = df_show.groupby("Resource")["Cost"].sum().reset_index()
                        st.dataframe(cost_by_profile, use_container_width=True, hide_index=True, column_config={"Resource": "Perfil", "Cost": st.column_config.NumberColumn("Coste (€)", format="€%.2f")})
                    with cc2:
                        st.markdown("**Costes Adicionales**")
                        st.session_state.additional_costs = st.data_editor(st.session_state.additional_costs, num_rows="dynamic", use_container_width=True,
                            column_config={"Description": st.column_config.TextColumn("Descripción", required=True), "Cost": st.column_config.NumberColumn("Coste (€)", format="€%.2f", required=True)})

                with st.expander("📊 Informes Personalizados"):
                    st.subheader("Configurar Informe Personalizado")
                    
                    # Selector de métricas
                    metric_options = ["Coste", "Duración", "Progreso", "Tareas por Estado", "Tareas por Prioridad"]
                    selected_metrics = st.multiselect("Métricas a incluir", metric_options, default=["Coste", "Duración"])
                    
                    # Filtros
                    st.subheader("Filtros")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        resource_filter = st.multiselect("Recurso", options=df_show["Resource"].unique().tolist())
                    with col2:
                        status_filter = st.multiselect("Estado", options=df_show["Status"].unique().tolist())
                    with col3:
                        priority_filter = st.multiselect("Prioridad", options=df_show["Priority"].unique().tolist())
                    
                    # Aplicar filtros
                    filtered_df = df_show.copy()
                    if resource_filter:
                        filtered_df = filtered_df[filtered_df["Resource"].isin(resource_filter)]
                    if status_filter:
                        filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]
                    if priority_filter:
                        filtered_df = filtered_df[filtered_df["Priority"].isin(priority_filter)]
                    
                    # Tipo de visualización
                    chart_type = st.selectbox("Tipo de gráfico", ["Barras", "Líneas", "Pastel", "Dispersión"])
                    
                    # Generar visualización
                    if not filtered_df.empty and selected_metrics:
                        st.subheader("Visualización Personalizada")
                        try:
                            if chart_type == "Barras":
                                fig = px.bar(filtered_df, x="Task", y="Cost" if "Coste" in selected_metrics else "Duration_days")
                            elif chart_type == "Líneas":
                                fig = px.line(filtered_df, x="Start", y="Cost" if "Coste" in selected_metrics else "Duration_days")
                            elif chart_type == "Pastel":
                                fig = px.pie(filtered_df, names="Resource", values="Cost" if "Coste" in selected_metrics else "Duration_days")
                            else: # Dispersión
                                fig = px.scatter(filtered_df, x="Duration_days", y="Cost", color="Resource")
                            
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error al generar gráfico: {str(e)}")
                    else:
                        st.info("Selecciona métricas y aplica filtros para generar el informe")
                
                with st.expander("📄 Documentos e Informes"):
                    doc_col1, doc_col2 = st.columns(2)
                    roles_str = ", ".join(df_show["Resource"].dropna().unique())
                    milestones_tasks = df_show[df_show["Task"].str.contains("milestone|hito", case=False, na=False)]["Task"].tolist()
                    task_list_str = "\n".join(f"- {r.Task}" for _, r in df_show.iterrows())
                    common_args = {"project_description": st.session_state.project_description, "duration": duration, "cost": work_cost + additional_cost, "milestones": "\n".join(f"- {t}" for t in milestones_tasks) or "- N/A", "roles": roles_str, "task_list": task_list_str}
                    
                    def generate_text_doc(button_label, prompt, args, state_key, filename):
                        if st.button(button_label, use_container_width=True, disabled=(provider == "Ninguno (manual)")):
                            with st.spinner("Generando..."):
                                try:
                                    text = call_llm_api(provider, model, prompt.format(**args))
                                    st.session_state[state_key] = create_docx_from_text(filename.replace('.docx', ''), text)
                                    st.toast(f"'{filename}' generado.", icon="✅")
                                except Exception as e: st.toast(f"Error: {e}", icon="❌")
                        if state_key in st.session_state: st.download_button(f"📥 Descargar {filename}", st.session_state[state_key], filename, use_container_width=True, key=f"dl_{state_key}")
                    
                    with doc_col1:
                        st.markdown("**Documentos de Proyecto**")
                        generate_text_doc("📜 Acta de Constitución", PROMPT_PROJECT_CHARTER, common_args, 'charter_doc', 'Acta_de_Constitucion.docx')
                        generate_text_doc("📝 Definición de Alcance", PROMPT_SCOPE_STATEMENT, common_args, 'scope_doc', 'Definicion_de_Alcance.docx')
                        generate_text_doc("📄 Documento Funcional", PROMPT_FUNCTIONAL_DOC, common_args, 'functional_doc', 'Documento_Funcional.docx')
                        # Documento exclusivo de Historias de Usuario
                        generate_text_doc("📚 Historias de Usuario", PROMPT_USER_STORIES, common_args, 'stories_doc', 'Historias_de_Usuario.docx')
                        # Revisión de Requisitos y Casos de Prueba
                        if st.button("🧐 Revisión IA de Requisitos", use_container_width=True, disabled=(provider == "Ninguno (manual)")):
                            with st.spinner("Analizando requisitos..."):
                                try:
                                    review_text = call_llm_api(provider, model, PROMPT_REQUIREMENTS_REVIEW.format(project_description=st.session_state.project_description))
                                    st.session_state['requirements_review_doc'] = create_docx_from_text('Revision_de_Requisitos', review_text)
                                    st.toast("'Revision_de_Requisitos.docx' generado.", icon="✅")
                                except Exception as e: st.toast(f"Error: {e}", icon="❌")
                        if 'requirements_review_doc' in st.session_state:
                            st.download_button("📥 Descargar Revisión de Requisitos", st.session_state['requirements_review_doc'], 'Revision_de_Requisitos.docx', use_container_width=True)
                        if st.button("🧪 Generar Casos de Prueba desde HUs", use_container_width=True, disabled=(provider == "Ninguno (manual)")):
                            with st.spinner("Generando casos de prueba..."):
                                try:
                                    # usar el texto de HUs si existe
                                    stories_bytes = st.session_state.get('stories_doc')
                                    stories_md = task_list_str if stories_bytes is None else "Historias generadas (ver docx adjunto)"
                                    tc_text = call_llm_api(provider, model, PROMPT_TEST_CASES_FROM_HUS.format(stories_markdown=stories_md))
                                    st.session_state['test_cases_doc'] = create_docx_from_text('Casos_de_Prueba', tc_text)
                                    st.toast("'Casos_de_Prueba.docx' generado.", icon="✅")
                                except Exception as e: st.toast(f"Error: {e}", icon="❌")
                        if 'test_cases_doc' in st.session_state:
                            st.download_button("📥 Descargar Casos de Prueba", st.session_state['test_cases_doc'], 'Casos_de_Prueba.docx', use_container_width=True)
                    
                    with doc_col2:
                        st.markdown("**Exportaciones y Reportes**")
                        if st.button("📋 Generar Informe Completo", use_container_width=True, disabled=(provider == "Ninguno (manual)")):
                            with st.spinner("Generando Informe..."):
                                try:
                                    summary_args = {**common_args, 'project_title': st.session_state.project_name, 'task_count': len(df_show), 'critical_task_count': len(crit_ids)}
                                    summary_text = call_llm_api(provider, model, PROMPT_EXECUTIVE_SUMMARY.format(**summary_args))
                                    # traer datos de riesgos e incidencias
                                    conn = get_db_connection()
                                    risks_df = pd.read_sql_query("SELECT description, probability, impact, status, mitigation_plan FROM risks WHERE project_id = ?", conn, params=(st.session_state.loaded_project_id,)) if st.session_state.get("loaded_project_id") else pd.DataFrame()
                                    issues_df = pd.read_sql_query("SELECT description, severity, status, resolution_plan FROM issues WHERE project_id = ?", conn, params=(st.session_state.loaded_project_id,)) if st.session_state.get("loaded_project_id") else pd.DataFrame()
                                    # calcular EVA (robusto ante columnas faltantes)
                                    df_for_evm = df_show.copy()
                                    # Asegurar columnas y tipos para EVA sin usar fillna sobre escalares
                                    if 'Actual_Cost' in df_for_evm.columns:
                                        df_for_evm['Actual_Cost'] = pd.to_numeric(df_for_evm['Actual_Cost'], errors='coerce').fillna(0.0)
                                    else:
                                        df_for_evm['Actual_Cost'] = pd.Series(0.0, index=df_for_evm.index)
                                    if 'Progress' in df_for_evm.columns:
                                        df_for_evm['Progress'] = pd.to_numeric(df_for_evm['Progress'], errors='coerce').fillna(0)
                                    else:
                                        df_for_evm['Progress'] = pd.Series(0, index=df_for_evm.index)
                                    for col in ['Start','Finish']:
                                        if col in df_for_evm.columns:
                                            df_for_evm[col] = pd.to_datetime(df_for_evm[col], errors='coerce')
                                        else:
                                            df_for_evm[col] = pd.Series(pd.NaT, index=df_for_evm.index)
                                    if 'Cost' in df_for_evm.columns:
                                        df_for_evm['Cost'] = pd.to_numeric(df_for_evm['Cost'], errors='coerce').fillna(0.0)
                                    else:
                                        df_for_evm['Cost'] = pd.Series(0.0, index=df_for_evm.index)
                                    evm_df = eva.calculate_evm(df_for_evm) if not df_for_evm.empty else pd.DataFrame()
                                    evm_summary = eva.calculate_project_evm(evm_df) if not evm_df.empty else {}
                                    st.session_state['report_doc'] = generate_full_report_docx("Informe Completo de Proyecto", summary_text, df_show, st.session_state.detailed_df, profile_costs, risks_df=risks_df, issues_df=issues_df, evm_df=evm_df, evm_summary=evm_summary)
                                    st.toast("'Informe_Completo.docx' generado.", icon="✅")
                                except Exception as e: st.error(f"Error al generar informe: {e}")
                        if 'report_doc' in st.session_state: st.download_button("📥 Descargar Informe Completo", st.session_state['report_doc'], 'Informe_Completo.docx', use_container_width=True)

                        # Exportación a PDF con gráficos
                        st.markdown("**Exportación a PDF**")
                        def fig_to_png_bytes(fig):
                            try:
                                return pio.to_image(fig, format='png', scale=2)
                            except Exception:
                                return None
                        if st.button("🖨️ Exportar PDF con Gráficos", use_container_width=True):
                            try:
                                # Reutilizar gráficos generados: Gantt y, si hay sprint, burndown
                                figs = []
                                gantt_fig = create_gantt_chart(df_show, crit_ids)
                                if gantt_fig: figs.append(("Diagrama de Gantt", gantt_fig))
                                # Intentar generar burndown del primer sprint si existe
                                conn = get_db_connection()
                                sprints_df = pd.read_sql_query("SELECT id, name, start_date, end_date FROM sprints WHERE project_id = ? ORDER BY start_date", conn, params=(st.session_state.loaded_project_id,)) if st.session_state.get("loaded_project_id") else pd.DataFrame()
                                if not sprints_df.empty:
                                    sprint_row = sprints_df.iloc[0]
                                    sp_name = sprint_row['name']
                                    sp_start = pd.to_datetime(sprint_row['start_date'])
                                    sp_end = pd.to_datetime(sprint_row['end_date'])
                                    sprint_tasks = df_show[df_show['Sprint'] == sp_name].copy()
                                    sprint_tasks['Story_Points'] = pd.to_numeric(sprint_tasks.get('Story_Points', 0), errors='coerce').fillna(0)
                                    if not sprint_tasks.empty:
                                        total_points = sprint_tasks['Story_Points'].sum()
                                        date_range = pd.date_range(sp_start, sp_end)
                                        progress_by_day = []
                                        for d in date_range:
                                            completed_points = sprint_tasks[(sprint_tasks['Status'] == 'Completada') & (pd.to_datetime(sprint_tasks['Finish'], errors='coerce') <= d)]['Story_Points'].sum()
                                            remaining = max(0, total_points - completed_points)
                                            progress_by_day.append({"date": d, "remaining": remaining, "completed": completed_points})
                                        burn_df = pd.DataFrame(progress_by_day)
                                        ideal_line = pd.Series(index=date_range, data=[total_points - (total_points * i / (len(date_range)-1 if len(date_range)>1 else 1)) for i in range(len(date_range))])
                                        fig_bd = go.Figure()
                                        fig_bd.add_trace(go.Scatter(x=burn_df['date'], y=burn_df['remaining'], mode='lines+markers', name='Real'))
                                        fig_bd.add_trace(go.Scatter(x=date_range, y=ideal_line, mode='lines', name='Ideal'))
                                        fig_bd.update_layout(title=f"Burndown - {sp_name}")
                                        figs.append(("Burndown", fig_bd))

                                # Construir PDF
                                pdf_bytes = io.BytesIO()
                                c = canvas.Canvas(pdf_bytes, pagesize=A4)
                                width, height = A4
                                margin = 40
                                # Portada
                                c.setFont("Helvetica-Bold", 14)
                                c.drawString(margin, height - margin, f"Informe Visual - {st.session_state.project_name}")
                                c.setFont("Helvetica", 10)
                                c.drawString(margin, height - margin - 14, pd.Timestamp.today().strftime('%Y-%m-%d %H:%M'))
                                c.drawString(margin, height - margin - 28, f"Autor: {st.session_state.get('username','')} ")
                                c.showPage()

                                # (Opcional) Índice simple
                                c.setFont("Helvetica-Bold", 12)
                                c.drawString(margin, height - margin, "Índice")
                                y = height - margin - 20
                                for i, (title, _) in enumerate(figs, start=1):
                                    c.setFont("Helvetica", 10)
                                    c.drawString(margin, y, f"{i}. {title}")
                                    y -= 14
                                c.showPage()

                                for title, fig in figs:
                                    img_bytes = fig_to_png_bytes(fig)
                                    if img_bytes:
                                        c.setFont("Helvetica-Bold", 12)
                                        c.drawString(margin, height - margin, title)
                                        img = ImageReader(io.BytesIO(img_bytes))
                                        # Ajustar imagen a la página
                                        img_w, img_h = fig.layout.width if hasattr(fig, 'layout') else (800, 600), fig.layout.height if hasattr(fig, 'layout') else (600, 400)
                                        max_w = width - 2*margin
                                        max_h = height - 2*margin - 20
                                        scale = min(max_w / 800, max_h / 600)
                                        draw_w = 800 * scale
                                        draw_h = 600 * scale
                                        c.drawImage(img, margin, height - margin - 20 - draw_h, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
                                        c.showPage()

                                c.save()
                                st.download_button("📥 Descargar PDF", data=pdf_bytes.getvalue(), file_name="Informe_Visual.pdf", use_container_width=True)
                            except Exception as e:
                                st.error(f"Error al generar PDF: {e}")
                        
                        export_col1, export_col2, export_col3 = st.columns(3)
                        export_col1.download_button("📊 Excel", data=export_plan_to_excel(df_show, st.session_state.additional_costs), file_name="Plan.xlsx", use_container_width=True)
                        export_col2.download_button("📝 JSON", data=df_show.to_json(orient='records', date_format='iso'), file_name="plan.json", mime="application/json", use_container_width=True)
                        export_col3.download_button("🗓️ iCal", data=export_to_ical(df_show), file_name="plan.ics", mime="text/calendar", use_container_width=True)
            else:
                st.info("👆 Genera un plan de proyecto para ver el análisis y la documentación.")

if __name__ == "__main__":
    main()