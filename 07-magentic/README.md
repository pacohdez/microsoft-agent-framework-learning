# 07 — Magentic con MagenticBuilder

El patrón más sofisticado de MAF. Un manager LLM decide dinámicamente
qué agente invocar, en qué orden, y si necesita loops de retroalimentación
basándose en los resultados intermedios.

## Diferencia clave vs Group Chat

| | Group Chat | Magentic |
|---|---|---|
| **Quién decide el flujo** | Tu función de selección | Manager LLM |
| **El flujo es** | Predecible | Adaptativo |
| **Loops posibles** | No | ✅ Sí |
| **Cuándo usarlo** | Debate estructurado | Problemas abiertos |

## Cuándo usar Magentic

- El flujo requiere bifurcaciones condicionales según resultados intermedios
- Necesitas loops de retroalimentación — revisitar agentes anteriores
- La secuencia óptima de agentes no se conoce de antemano
- La complejidad de la tarea justifica el overhead del LLM manager

## Conceptos clave

```python
workflow = MagenticBuilder(
    participants=[agente1, agente2, agente3],  # lista, no dict
    manager_agent=manager,                      # no .with_standard_manager()
    max_round_count=20,                         # límite de rondas totales
    max_stall_count=5,                          # replanifica tras N rondas sin avance
).build()
```

## Lecciones aprendidas

- `participants` es una lista — NO un diccionario con nombres como keys
- El manager se pasa como `manager_agent=` en el constructor
- `.with_standard_manager()` NO existe en esta versión
- El manager aparece como `magentic_orchestrator` en los eventos
- Las respuestas se capturan en `executor_completed` con `event.data.agent_response`
- El evento `output` contiene el resumen final del manager
- El manager puede seguir invocando agentes después del "TAREA COMPLETA"
  si `max_round_count` no se ha alcanzado — instrucciones claras de terminación
  en el manager ayudan a reducir esto

## Flujo observado

**Propuesta normal** (sin alertas):
manager → Investigador → manager → ChefTecnico → Nutriologo → Dictaminador

**Propuesta con alerta** (autenticidad baja):
manager → Investigador → manager → ChefTecnico → Nutriologo →
Dictaminador → manager (replanifica) → Investigador (2a vez) → Dictaminador


## Ejecución

```bash
uv run magentic_chef.py
```

Cambia entre tareas en `main()` para ver el flujo adaptativo:

```python
# Flujo normal — sin loops
await workflow.run(tarea_normal, stream=True)

# Flujo con alerta — genera loop de retroalimentación
await workflow.run(tarea_con_alerta, stream=True)
```