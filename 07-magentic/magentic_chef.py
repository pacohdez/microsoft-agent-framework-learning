"""
Paso 7 — Magentic con MagenticBuilder
El patrón más sofisticado: un manager LLM decide dinámicamente
qué agente invocar, en qué orden, y si necesita loops de retroalimentación.

Diferencia clave vs otros patrones:
- Sequential/Concurrent: orden fijo predeterminado
- Handoff: agentes se transfieren el control entre sí
- GroupChat: turno por turno con función de selección
- Magentic: el manager LLM decide TODO en tiempo real

Ejemplo: Panel de expertos culinarios donde el manager decide
si un platillo necesita más investigación antes de aprobarlo.
"""
import os
import asyncio
from dotenv import load_dotenv
from agent_framework import tool, WorkflowRunState
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.orchestrations import MagenticBuilder
from azure.identity import DefaultAzureCredential

load_dotenv()

# ── Cliente ───────────────────────────────────────────────

chat_client = OpenAIChatCompletionClient(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    credential=DefaultAzureCredential(),
    model=os.getenv("AZURE_OPENAI_MODEL"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# ── Herramientas ──────────────────────────────────────────

@tool
def evaluar_autenticidad(platillo: str, descripcion: str) -> str:
    """Evalúa qué tan auténtico es un platillo respecto a la tradición mexicana.
    Devuelve una puntuación del 1 al 10 y observaciones.
    """
    # Palabras que aumentan la autenticidad
    elementos_tradicionales = [
        "chile", "maíz", "tortilla", "trompo", "comal", "metate",
        "nixtamal", "epazote", "hierba santa", "hoja de maíz", "mole",
        "adobe", "piloncillo", "canela", "comino"
    ]
    # Palabras que reducen la autenticidad
    elementos_fusion = [
        "molecular", "espuma", "gel", "nitrógeno", "sous vide",
        "quinoa", "kale", "sriracha", "wasabi", "trufa"
    ]

    texto = f"{platillo} {descripcion}".lower()
    puntos_trad = sum(1 for e in elementos_tradicionales if e in texto)
    puntos_fusion = sum(1 for e in elementos_fusion if e in texto)

    puntuacion = max(1, min(10, 5 + puntos_trad - (puntos_fusion * 2)))
    nivel = "Alta" if puntuacion >= 7 else "Media" if puntuacion >= 4 else "Baja"

    resultado = f"""EVALUACIÓN DE AUTENTICIDAD: {platillo}
Puntuación: {puntuacion}/10 — Autenticidad {nivel}
Elementos tradicionales detectados: {puntos_trad}
Elementos de fusión detectados: {puntos_fusion}"""

    if puntuacion < 4:
        resultado += "\n⚠️ ALERTA: Autenticidad muy baja — requiere revisión profunda de la propuesta."

    return resultado


@tool
def analizar_tecnica_coccion(platillo: str, metodo: str) -> str:
    """Analiza si la técnica de cocción es apropiada para el platillo.
    Devuelve observaciones técnicas y posibles mejoras.
    """
    tecnicas_tradicionales = {
        "tacos": ["trompo", "comal", "plancha", "sartén"],
        "mole": ["cazuela", "comal", "molcajete"],
        "tamales": ["vaporera", "tamalera"],
        "pozole": ["olla", "cazuela"],
        "enchiladas": ["comal", "sartén"],
    }

    metodo_lower = metodo.lower()
    platillo_lower = platillo.lower()

    tecnicas_ok = []
    for p, tecnicas in tecnicas_tradicionales.items():
        if p in platillo_lower:
            tecnicas_ok = tecnicas
            break

    es_apropiado = any(t in metodo_lower for t in tecnicas_ok) if tecnicas_ok else True

    return f"""ANÁLISIS TÉCNICO: {platillo}
Método propuesto: {metodo}
Técnicas tradicionales para este platillo: {', '.join(tecnicas_ok) if tecnicas_ok else 'No hay referencia específica'}
¿Técnica apropiada?: {'✅ Sí' if es_apropiado else '⚠️ No — considerar técnicas tradicionales'}
Observación: {'El método respeta la tradición culinaria.' if es_apropiado else 'El método se aleja de la preparación tradicional. Investigar más.'}"""


@tool
def revisar_ingredientes(platillo: str, ingredientes: str) -> str:
    """Revisa si los ingredientes son consistentes con la receta tradicional.
    Devuelve una lista de ingredientes faltantes o inapropiados.
    """
    recetas_base = {
        "tacos al pastor": ["cerdo", "chile guajillo", "achiote", "piña", "cebolla", "cilantro", "tortilla"],
        "mole poblano": ["chile mulato", "chile ancho", "chocolate", "ajonjolí", "plátano", "tortilla"],
        "pozole": ["maíz", "cerdo", "chile guajillo", "oregano", "lechuga", "rábano"],
        "guacamole": ["aguacate", "limón", "cebolla", "cilantro", "chile serrano"],
        "chiles en nogada": ["chile poblano", "nuez", "granada", "perejil", "carne"],
    }

    platillo_lower = platillo.lower()
    ingredientes_lower = ingredientes.lower()

    receta_ref = None
    for p, ing in recetas_base.items():
        if p in platillo_lower or any(palabra in platillo_lower for palabra in p.split()):
            receta_ref = (p, ing)
            break

    if not receta_ref:
        return f"No tengo receta de referencia para '{platillo}'. Proceder con criterio general."

    nombre_ref, ingredientes_ref = receta_ref
    faltantes = [i for i in ingredientes_ref if i not in ingredientes_lower]
    extras = [w for w in ingredientes_lower.split(",") if w.strip() and not any(
        i in w for i in ingredientes_ref
    )]

    return f"""REVISIÓN DE INGREDIENTES: {platillo}
Referencia: {nombre_ref}
Ingredientes faltantes: {', '.join(faltantes) if faltantes else 'Ninguno ✅'}
Ingredientes no tradicionales: {', '.join(extras[:3]) if extras else 'Ninguno ✅'}
{'⚠️ ALERTA: Faltan ingredientes esenciales — investigar la propuesta.' if len(faltantes) > 2 else '✅ Los ingredientes principales están presentes.'}"""


@tool
def generar_dictamen_final(platillo: str, resumen: str) -> str:
    """Genera el dictamen final del panel de expertos sobre la propuesta culinaria."""
    return f"""
{'='*55}
📋 DICTAMEN FINAL DEL PANEL DE EXPERTOS
{'='*55}
Platillo evaluado: {platillo}

{resumen}

Emitido por: Panel Culinario de Expertos en Cocina Mexicana
{'='*55}
"""

# ── Agentes especializados ────────────────────────────────

investigador = chat_client.as_agent(
    name="Investigador",
    description="Investiga el contexto histórico y cultural del platillo.",
    instructions="""
    Eres un investigador gastronómico especializado en cocina mexicana.
    Tu rol es investigar el origen, historia y contexto cultural de los platillos.
    Usa evaluar_autenticidad para dar una puntuación objetiva.
    Sé conciso — máximo 4 oraciones por respuesta.
    """,
    tools=[evaluar_autenticidad],
)

chef_tecnico = chat_client.as_agent(
    name="ChefTecnico",
    description="Evalúa la técnica de cocción y el método de preparación.",
    instructions="""
    Eres un chef técnico experto en métodos de cocina mexicana tradicional.
    Evalúas si las técnicas propuestas son correctas y apropiadas.
    Usa analizar_tecnica_coccion para dar una evaluación objetiva.
    Sé conciso — máximo 4 oraciones por respuesta.
    """,
    tools=[analizar_tecnica_coccion],
)

nutriologo = chat_client.as_agent(
    name="Nutriologo",
    description="Revisa los ingredientes y su consistencia con la receta tradicional.",
    instructions="""
    Eres un nutriólogo especializado en gastronomía mexicana tradicional.
    Revisas si los ingredientes son correctos y completos.
    Usa revisar_ingredientes para dar una evaluación objetiva.
    Sé conciso — máximo 4 oraciones por respuesta.
    """,
    tools=[revisar_ingredientes],
)

dictaminador = chat_client.as_agent(
    name="Dictaminador",
    description="Emite el dictamen final consolidando todas las evaluaciones.",
    instructions="""
    Eres el presidente del panel culinario.
    ESTE ES EL PASO FINAL — después de emitir el dictamen, la tarea está COMPLETA.
    Consolida todas las evaluaciones en un veredicto claro:
    ✅ APROBADO / ⚠️ APROBADO CON OBSERVACIONES / ❌ RECHAZADO
    Usa generar_dictamen_final para emitir el dictamen oficial.
    Confirma "DICTAMEN EMITIDO — TAREA COMPLETA" al finalizar.
    """,
    tools=[generar_dictamen_final],
)

# ── Manager — el cerebro del workflow ────────────────────

manager = chat_client.as_agent(
    name="DirectorPanel",
    description="Director del panel que coordina a todos los expertos.",
    instructions="""
    Eres el Director del Panel de Expertos en Cocina Mexicana.

    TU EQUIPO:
    - Investigador: evalúa autenticidad histórica y cultural
    - ChefTecnico: evalúa técnicas de cocción
    - Nutriologo: revisa ingredientes y consistencia
    - Dictaminador: emite el dictamen final (PASO FINAL)

    FLUJO NORMAL:
    1. Investigador — evaluar autenticidad
    2. ChefTecnico — evaluar técnica
    3. Nutriologo — revisar ingredientes
    4. Dictaminador — emitir dictamen final

    FLUJO CON ALERTA (si algún agente reporta "⚠️ ALERTA"):
    - Solicita al Investigador una investigación más profunda del problema
    - Luego procede al Dictaminador

    TERMINACIÓN:
    - La tarea está COMPLETA cuando el Dictaminador confirma "DICTAMEN EMITIDO"
    - NO invoques más agentes después del Dictaminador
    """,
)

# ── Workflow ──────────────────────────────────────────────

workflow = MagenticBuilder(
    participants=[investigador, chef_tecnico, nutriologo, dictaminador],
    manager_agent=manager,
    max_round_count=15,
    max_stall_count=3,
).build()

# ── Main ──────────────────────────────────────────────────

async def main():
    # Propuesta normal — debería seguir flujo estándar
    tarea_normal = """
    Evalúa esta propuesta de platillo:
    Nombre: Tacos al Pastor Modernos
    Descripción: Cerdo marinado en adobo tradicional de chile guajillo y achiote,
    cocinado en trompo. Servido en tortilla de maíz nixtamalizado con piña,
    cebolla y cilantro. Salsa de chile de árbol.
    Método de cocción: trompo tradicional con comal.
    Ingredientes: cerdo, chile guajillo, achiote, piña, cebolla, cilantro, tortilla, sal.
    """

    # Propuesta con alerta — debería generar loop de investigación
    tarea_con_alerta = """
    Evalúa esta propuesta de platillo:
    Nombre: Tacos al Pastor Fusión
    Descripción: Carne de cerdo con espuma de piña molecular,
    gel de cilantro y sriracha. Servido en tortilla de quinoa con kale.
    Método de cocción: sous vide a 65°C.
    Ingredientes: cerdo, sriracha, quinoa, kale, espuma molecular de piña.
    """

    print("=" * 55)
    print("🍳 MAGENTIC — Panel de Expertos Culinarios")
    print("=" * 55)
    print("\nℹ️  El manager decidirá dinámicamente el flujo.")
    print("    Si detecta alertas, hará un loop de investigación.\n")

    secuencia = []

    async for event in workflow.run(tarea_normal, stream=True):
        if event.type == "executor_invoked":
            nombre = event.executor_id.split(":")[-1] if ":" in event.executor_id else event.executor_id
            secuencia.append(nombre)
            print(f"⚡ Invocando: {nombre}")

        elif event.type == "executor_completed":
            nombre = event.executor_id.split(":")[-1] if ":" in event.executor_id else event.executor_id

            # Magentic devuelve AgentExecutorResponse directamente en event.data
            if hasattr(event, "data") and event.data is not None:
                data = event.data

                # Caso 1: AgentExecutorResponse directo
                if hasattr(data, "agent_response"):
                    resp = data.agent_response
                    if hasattr(resp, "messages"):
                        for msg in resp.messages:
                            if hasattr(msg, "text") and msg.text and nombre != "magentic_orchestrator":
                                texto = msg.text[:300] + "..." if len(msg.text) > 300 else msg.text
                                print(f"  ✓ [{nombre}]: {texto}\n")

                # Caso 2: lista de respuestas
                elif isinstance(data, list) and data:
                    for item in data:
                        if hasattr(item, "agent_response"):
                            resp = item.agent_response
                            if hasattr(resp, "messages"):
                                for msg in resp.messages:
                                    if hasattr(msg, "text") and msg.text and nombre != "magentic_orchestrator":
                                        texto = msg.text[:300] + "..." if len(msg.text) > 300 else msg.text
                                        print(f"  ✓ [{nombre}]: {texto}\n")

        elif event.type == "output":
            if hasattr(event, "data") and event.data is not None:
                if hasattr(event.data, "text") and event.data.text:
                    print(f"\n📋 OUTPUT FINAL:\n{event.data.text}\n")

        elif event.type == "status":
            if event.state == WorkflowRunState.IDLE:
                print("\n✅ Workflow completado!")

    print(f"\n📊 Secuencia de agentes invocados:")
    print(" → ".join(secuencia))
    print(f"\nTotal de invocaciones: {len(secuencia)}")

asyncio.run(main())