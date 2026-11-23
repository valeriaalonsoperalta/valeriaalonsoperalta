"""Lanza scrum_simulator.py usando respuestas escritas por Claude en lugar de la API de Gemini.

Uso (desde la raíz del repositorio):  streamlit run scrum/run_con_claude.py
No modifica scrum_simulator.py: sustituye el modelo de Gemini por uno que lee
las respuestas preparadas en scrum/claude_llm/.
"""
import os, re, json, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "claude_llm")
os.environ["GEMINI_API_KEY"] = "respuestas-de-claude"  # no se usa ninguna clave real
import google.generativeai as genai

def _read(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return f.read()

class _Resp:
    def __init__(self, text): self.text = text

class ClaudeModel:
    def __init__(self, model_name=None, system_instruction="", generation_config=None, **kw):
        self.system = system_instruction or ""
    def generate_content(self, prompt):
        if "Product Owner experto" in self.system:
            return _Resp(_read("backlog.json"))
        if "simulando el día a día" in self.system:
            dia = re.search(r"día (\d+) de un sprint", prompt).group(1)
            return _Resp(json.dumps({"evento": json.loads(_read("eventos.json"))[dia]}, ensure_ascii=False))
        if "presentando los resultados" in self.system:
            return _Resp(_read("review.md"))
        if "Agile Coach" in self.system:
            return _Resp(_read("retro.md"))
        raise RuntimeError("Sin respuesta preparada por Claude para este prompt.")

genai.configure = lambda **kw: None
genai.GenerativeModel = ClaudeModel
os.chdir(HERE)
runpy.run_path(os.path.join(HERE, "scrum_simulator.py"), run_name="__main__")
