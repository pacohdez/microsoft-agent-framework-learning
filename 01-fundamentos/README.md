# 01 — Fundamentos

Tres pasos progresivos para aprender los conceptos base de Agent Framework.

| Archivo | Concepto | Descripción |
|---|---|---|
| `main_paso1_primer_agente.py` | `Agent` + `agent.run()` | Agente básico sin herramientas |
| `main_paso2_herramientas.py` | `@tool` decorator | Herramientas con invocación paralela |
| `main_paso3_sesiones.py` | `create_session()` | Memoria multi-turno |

## Ejecución
```bash
uv run main_paso1_primer_agente.py
uv run main_paso2_herramientas.py
uv run main_paso3_sesiones.py
```