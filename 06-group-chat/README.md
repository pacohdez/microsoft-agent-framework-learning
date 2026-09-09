# 06 — Group Chat con GroupChatBuilder

Conversación multi-agente donde todos los participantes comparten el historial
completo y cada uno puede leer y construir sobre lo que dijeron los demás.

## Diferencia clave vs otros patrones

| Patrón | Los agentes se ven entre sí |
|---|---|
| Sequential | Solo al agente anterior |
| Concurrent | No — trabajan independiente |
| Handoff | Solo al agente activo |
| **Group Chat** | ✅ Todos ven todo |

## Conceptos clave

- `GroupChatBuilder(participants=[...], selection_func=fn, max_rounds=N).build()`
- `GroupChatState` con campos: `current_round`, `participants`, `conversation`
- La función de selección decide quién habla a continuación
- Se importa de `agent_framework.orchestrations`

## Patrones de selección implementados

| Patrón | Descripción | Cuándo usarlo |
|---|---|---|
| `round_robin` | Orden fijo y predecible | Debates estructurados |
| `sin_repeticion` | Nadie habla dos veces seguidas | Conversaciones variadas |
| `con_peso` | Un agente habla más seguido | Cuando un rol domina |
| `por_contenido` | El contenido decide quién sigue | Conversaciones reactivas |

## Lecciones aprendidas

- `selection_func` se pasa en el constructor, no como método de cadena
- Para terminar, usar `max_rounds` en el constructor — retornar `None` no funciona
- La transcripción se captura en `executor_completed` filtrando `group_chat_orchestrator`
- El evento `output` solo devuelve el mensaje de cierre del orquestador

## Ejecución

```bash
uv run group_chat.py
```

Cambia el patrón en `main()` para experimentar con los 4 modos:

```python
await ejecutar_group_chat(patron="round_robin", tema=tema)
# "round_robin" | "sin_repeticion" | "con_peso" | "por_contenido"
```