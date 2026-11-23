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
