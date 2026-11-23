# Plan "Lanzamiento App GreenStyle"

- `wbs_greenstyle.json`: plan de tareas (WBS) generado con Claude siguiendo las reglas de `PROMPT_WBS_JSON` de `app.py`.
- `calcular_plan.py`: aplica las funciones de la app (`parse_json_wbs`, `calculate_task_dates`, `calculate_costs`, `calculate_critical_path`) con las tarifas del laboratorio (PM 60 €, Developer 50 €, Designer 45 €, QA 40 €, Analyst 45 €).

Ejecución (desde la raíz del repositorio, con el entorno virtual activado):

```bash
python greenstyle/calcular_plan.py . greenstyle/wbs_greenstyle.json
```

Resultado con inicio el 23/11/2026:

- Coste Total Estimado: €56.200,00 (1.160 horas)
- Duración Total Estimada: 90 días (23/11/2026 → 20/02/2027)
- Ruta crítica (14 tareas): 1, 2, 4, 9, 10, 12, 13, 14, 15, 18, 20, 21, 22, 24 — p. ej. "Checkout e integración de pasarela Stripe".

La fecha de inicio es la del día de ejecución, así que las fechas cambian si se vuelve a ejecutar otro día; el coste y la duración no.
