"""Lanza la Suite usando respuestas escritas por Claude en lugar de llamar a Gemini/Groq/OpenRouter.

Uso (desde la raíz del repositorio):  streamlit run greenstyle/run_app_con_claude.py
Las respuestas están en greenstyle/claude_llm/ y siguen los prompts de app.py.
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "greenstyle", "claude_llm")
sys.path.insert(0, ROOT)
import app

def _read(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return f.read()

def claude_llm(provider, model, prompt, expect_json=False, **kwargs):
    if "Director de Programa especializado" in prompt:
        get = lambda pat: (re.search(pat, prompt) or [None, "?"])[1]
        hitos = prompt.split("Hitos Clave:\n", 1)[1].strip() if "Hitos Clave:\n" in prompt else "- N/A"
        if hitos == "- N/A":
            hitos = "- Cierre de la fase de Análisis y aprobación de la arquitectura\n- Aprobación de los diseños\n- Finalización del desarrollo\n- Aceptación de usuario (UAT)\n- Publicación en las tiendas y go-live"
        return _read("acta_constitucion_ia.md").format(
            duracion=get(r"Duración: (\d+)"), coste=get(r"Costo: €([\d,\.]+)"),
            roles=get(r"Roles Clave: (.+)"), hitos=hitos)
    if "Estructura de Desglose de Trabajo (WBS)" in prompt:
        return _read("wbs_perfiles_agiles.json")
    if "desglósala en 3-5 subtareas" in prompt:
        return _read("subtareas.txt")
    if "Risk Manager senior" in prompt:
        return _read("riesgos.json")
    if "analista senior de requisitos" in prompt:
        return _read("revision_requisitos.md")
    if "resumen ejecutivo" in prompt:
        get = lambda pat: (re.search(pat, prompt) or [None, "?"])[1]
        return _read("resumen_ejecutivo.md").format(
            title=get(r"Título: (.+)"), dur=get(r"Duración: (\d+)"), cost=get(r"Costo: €([\d,\.]+)"),
            tasks=get(r"Tareas Totales: (\d+)"), crit=get(r"Tareas Críticas: (\d+)"))
    raise RuntimeError("Sin respuesta preparada por Claude para este prompt.")

app.call_llm_api = claude_llm
app.main()
