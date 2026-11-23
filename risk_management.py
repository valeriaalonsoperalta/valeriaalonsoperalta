# risk_management.py - Módulo de Gestión de Riesgos e Incidencias
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

def init_risk_tables(conn):
    cursor = conn.cursor()
    # Tabla de riesgos
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
    
    # Tabla de incidencias
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
    conn.commit()

def create_risk(conn, project_id, description, probability, impact, mitigation_plan=""):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO risks (project_id, description, probability, impact, mitigation_plan) VALUES (?, ?, ?, ?, ?)",
        (project_id, description, probability, impact, mitigation_plan)
    )
    conn.commit()
    return cursor.lastrowid

def create_issue(conn, project_id, description, severity, resolution_plan=""):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO issues (project_id, description, severity, resolution_plan) VALUES (?, ?, ?, ?)",
        (project_id, description, severity, resolution_plan)
    )
    conn.commit()
    return cursor.lastrowid

def get_risks(conn, project_id):
    return pd.read_sql_query("SELECT * FROM risks WHERE project_id = ?", conn, params=(project_id,))

def get_issues(conn, project_id):
    return pd.read_sql_query("SELECT * FROM issues WHERE project_id = ?", conn, params=(project_id,))

def render_risk_management_ui(conn, project_id):
    st.header("⚠️ Gestión de Riesgos e Incidencias")
    
    tab1, tab2 = st.tabs(["Riesgos", "Incidencias"])
    
    with tab1:
        st.subheader("Registro de Riesgos")
        with st.form("risk_form"):
            risk_desc = st.text_area("Descripción del riesgo")
            risk_prob = st.slider("Probabilidad (0-1)", 0.0, 1.0, 0.5)
            risk_impact = st.selectbox("Impacto", ["Bajo", "Medio", "Alto"])
            risk_mitigation = st.text_area("Plan de mitigación")
            if st.form_submit_button("Guardar Riesgo"):
                create_risk(conn, project_id, risk_desc, risk_prob, risk_impact, risk_mitigation)
                st.success("Riesgo registrado")
        
        st.subheader("Riesgos Registrados")
        risks_df = get_risks(conn, project_id)
        if not risks_df.empty:
            st.dataframe(risks_df)
        else:
            st.info("No hay riesgos registrados")
    
    with tab2:
        st.subheader("Registro de Incidencias")
        with st.form("issue_form"):
            issue_desc = st.text_area("Descripción de la incidencia")
            issue_severity = st.selectbox("Severidad", ["Bajo", "Medio", "Alto", "Crítico"])
            issue_resolution = st.text_area("Plan de resolución")
            if st.form_submit_button("Guardar Incidencia"):
                create_issue(conn, project_id, issue_desc, issue_severity, issue_resolution)
                st.success("Incidencia registrada")
        
        st.subheader("Incidencias Registradas")
        issues_df = get_issues(conn, project_id)
        if not issues_df.empty:
            st.dataframe(issues_df)
        else:
            st.info("No hay incidencias registradas")