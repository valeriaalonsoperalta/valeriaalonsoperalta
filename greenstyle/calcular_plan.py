import sys, json
sys.path.insert(0, sys.argv[1])  # carpeta que contiene app.py
import app
from datetime import date
costs = {"Project Manager":60.0,"Developer":50.0,"Designer":45.0,"QA":40.0,"Analyst":45.0,"Sin Asignar":0.0}
txt = open(sys.argv[2]).read()
df = app.parse_json_wbs(txt)
df = app.sanitize_tasks_df(df, list(costs))
df, probs = app.calculate_task_dates(df, start_base=date.today())
df = app.calculate_costs(df, costs)
crit, dur = app.calculate_critical_path(df)
print("Problemas:", probs)
print(f"Coste Total Estimado: €{df['Cost'].sum():,.2f}")
print(f"Duración Total Estimada: {dur} días")
print("Horas totales:", df['Duration_hours'].sum())
for _, r in df.iterrows():
    print(f"{'CRIT' if r.TaskID in crit else '    '} [{r.TaskID}] {r.Task} | {r.Resource} | {r.Duration_hours}h | {r.Start.date()} → {r.Finish.date()} | €{r.Cost:,.0f}")
