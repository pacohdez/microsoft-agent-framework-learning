# 03 — Multi-agente con Handoff

Patrón HandoffBuilder con tres agentes especializados y un coordinador.

## Topología
CoordinadorBot
├──→ NutricionBot (alimentación y calorías)
└──→ EjercicioBot (rutinas y entrenamiento)

## Conceptos clave
- `client.as_agent()` en lugar de `Agent()` para workflows
- `require_per_service_call_history_persistence=True`
- `workflow.run(stream=True)` con loop de eventos
- `_source_executor_id` para identificar el agente que responde

## Ejecución
```bash
uv run bienestar_agent.py
```