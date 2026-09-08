# 04 — Workflows: Sequential y Concurrent

Dos patrones de orquestación automática sin intervención del usuario.

| Patrón | Builder | Cuándo usarlo |
|---|---|---|
| Sequential | `SequentialBuilder` | Pipeline donde cada agente enriquece al anterior |
| Concurrent | `ConcurrentBuilder` | Múltiples perspectivas independientes en paralelo |

## Ejecución
```bash
uv run workflows.py
```