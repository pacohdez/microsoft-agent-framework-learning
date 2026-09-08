import os
import asyncio
from dotenv import load_dotenv
from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.orchestrations import SequentialBuilder, ConcurrentBuilder
from azure.identity import DefaultAzureCredential

load_dotenv()

def get_client():
    return OpenAIChatCompletionClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        credential=DefaultAzureCredential(),
        model=os.getenv("AZURE_OPENAI_MODEL"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

# ═══════════════════════════════════════════════════════════
# PARTE 1 — SEQUENTIAL: pipeline de análisis de recetas
# Flujo: AnalizadorBot → NutricionistaBot → PresentadorBot
# Cada agente enriquece el trabajo del anterior
# ═══════════════════════════════════════════════════════════

async def demo_sequential():
    client = get_client()

    analizador = Agent(
        client=client,
        name="AnalizadorBot",
        instructions="""
        Eres un chef analítico. Dado un platillo, identifica:
        1. Sus ingredientes principales (máximo 5)
        2. La técnica de cocción principal
        3. El tiempo estimado de preparación
        Sé conciso y estructurado.
        """,
    )

    nutricionista = Agent(
        client=client,
        name="NutricionistaBot",
        instructions="""
        Eres un nutricionista. Basándote en el análisis del platillo anterior:
        1. Estima las calorías aproximadas por porción
        2. Identifica los macronutrientes principales (proteínas, carbohidratos, grasas)
        3. Da una calificación de salud del 1 al 10
        Complementa lo que ya se dijo, no lo repitas.
        """,
    )

    presentador = Agent(
        client=client,
        name="PresentadorBot",
        instructions="""
        Eres un editor gastronómico. Toma todo el análisis anterior y crea
        una ficha de receta final, atractiva y bien estructurada con:
        - Nombre del platillo con emoji
        - Resumen en una línea
        - Ingredientes clave
        - Técnica y tiempo
        - Info nutricional
        - Puntuación de salud con justificación breve
        Hazlo visualmente atractivo usando emojis.
        """,
    )

    # Sequential: analizador → nutricionista → presentador
    # intermediate_output_from muestra el progreso de cada agente
    workflow = SequentialBuilder(
        participants=[analizador, nutricionista, presentador],
        intermediate_output_from=[analizador, nutricionista],
    ).build()

    print("=" * 60)
    print("🔄 SEQUENTIAL — Pipeline de análisis de recetas")
    print("=" * 60)

    platillo = "Tacos al pastor"
    print(f"\n📥 Input: {platillo}\n")
    print("-" * 60)

    result = await workflow.run(f"Analiza este platillo: {platillo}")

    for output in result.get_outputs():
        for msg in output.messages:
            print(f"\n[{msg.author_name}]:\n{msg.text}\n")
            print("-" * 60)


# ═══════════════════════════════════════════════════════════
# PARTE 2 — CONCURRENT: análisis paralelo de un platillo
# Tres agentes analizan el mismo platillo simultáneamente
# desde perspectivas diferentes
# ═══════════════════════════════════════════════════════════

async def demo_concurrent():
    client = get_client()

    chef = Agent(
        client=client,
        name="ChefBot",
        instructions="""
        Eres un chef experto. Dado un platillo, describe en 3-4 líneas:
        - La técnica de preparación clave
        - El secreto para hacerlo bien
        - Un consejo profesional
        """,
    )

    nutricionista = Agent(
        client=client,
        name="NutricionistaBot",
        instructions="""
        Eres un nutricionista. Dado un platillo, describe en 3-4 líneas:
        - Su perfil nutricional general
        - Sus beneficios para la salud
        - A quién se lo recomendarías (o no)
        """,
    )

    historiador = Agent(
        client=client,
        name="HistoriadorBot",
        instructions="""
        Eres un historiador gastronómico. Dado un platillo, describe en 3-4 líneas:
        - Su origen e historia
        - Su importancia cultural
        - Una curiosidad interesante
        """,
    )

    # Concurrent: los tres analizan en paralelo el mismo input
    workflow = ConcurrentBuilder(
        participants=[chef, nutricionista, historiador],
    ).build()

    print("\n" + "=" * 60)
    print("⚡ CONCURRENT — Análisis paralelo de un platillo")
    print("=" * 60)

    platillo = "Pozole rojo"
    print(f"\n📥 Input: {platillo}\n")
    print("-" * 60)

    result = await workflow.run(f"Analiza este platillo: {platillo}")

    for output in result.get_outputs():
        for msg in output.messages:
            print(f"\n[{msg.author_name}]:\n{msg.text}\n")
            print("-" * 60)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

async def main():
    await demo_sequential()
    await demo_concurrent()

asyncio.run(main())