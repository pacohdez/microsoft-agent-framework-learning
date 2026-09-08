# 🤖 Microsoft Agent Framework — Learning Path

Repositorio de aprendizaje progresivo de **Microsoft Agent Framework (MAF)**
con Python y Azure OpenAI, partiendo desde un agente básico hasta aplicaciones
multi-agente con datos reales.

## 🛠️ Stack tecnológico

- Python 3.11 + `uv`
- Microsoft Agent Framework (`agent-framework-core`, `agent-framework-openai`, `agent-framework-orchestrations`)
- Azure OpenAI (GPT-4o) con autenticación via Service Principal
- MongoDB (motor async)

## 📚 Contenido

| Módulo | Concepto | Descripción |
|---|---|---|
| `01-fundamentos` | Agente básico, tools, sesiones | ChefBot — asistente de cocina mexicana |
| `02-aplicaciones` | Flujos multi-paso, herramientas reales | MenuBot y GymBot |
| `03-multi-agente` | Patrón Handoff | BienestarBot — nutrición + ejercicio |
| `04-workflows` | Sequential y Concurrent | Pipeline de análisis de recetas |
| `05-datos-reales` | CSV, JSON, APIs externas | NutriFitBot con datos reales |

## ⚙️ Configuración

1. Clona el repositorio
2. Crea el entorno con `uv`:
```bash
   uv sync
```
3. Crea tu `.env` basándote en `.env.example`
4. Ejecuta cualquier módulo:
```bash
   uv run 01-fundamentos/main_paso1_primer_agente.py
```

## 📖 Documentación

Consulta `docs/MAF_Resumen_Aprendizaje.md` para el resumen completo
con todos los conceptos, patrones y código funcional.

## 🔑 Patrones aprendidos

- `Agent` + `instructions` + `agent.run()`
- `@tool` decorator con invocación paralela automática
- `agent.create_session()` para memoria multi-turno
- `HandoffBuilder` para enrutamiento dinámico entre agentes
- `SequentialBuilder` para pipelines en cadena
- `ConcurrentBuilder` para ejecución paralela
- Integración con datos reales: CSV, JSON, APIs externas