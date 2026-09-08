"""
Paso 2 — Herramientas con @tool
Conceptos: @tool decorator, tools=[...], invocación paralela automática
El LLM decide cuándo y cuántas herramientas invocar simultáneamente.
"""
import os
import asyncio
from dotenv import load_dotenv
from agent_framework import Agent, tool
from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential

load_dotenv()

def get_client():
    return OpenAIChatCompletionClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        credential=DefaultAzureCredential(),
        model=os.getenv("AZURE_OPENAI_MODEL"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

@tool
def get_ingredientes(platillo: str) -> str:
    """Devuelve los ingredientes principales de un platillo mexicano."""
    recetas = {
        "tacos al pastor": "cerdo adobado, piña, cebolla, cilantro, tortilla de maíz",
        "guacamole":       "aguacate, limón, cebolla, cilantro, chile serrano, sal",
        "chiles en nogada": "chile poblano, picadillo de carne, nogada, granada, perejil",
        "pozole":          "maíz cacahuazintle, cerdo, chile guajillo, orégano, lechuga, rábano",
        "mole poblano":    "chile mulato, chile ancho, chocolate, ajonjolí, plátano macho, pavo",
    }
    platillo_lower = platillo.lower()
    for key, value in recetas.items():
        if key in platillo_lower or platillo_lower in key:
            return f"Ingredientes de {key}: {value}"
    return f"No tengo la receta de '{platillo}' en mi base de datos."

@tool
def get_tiempo_preparacion(platillo: str) -> str:
    """Devuelve el tiempo estimado de preparación de un platillo mexicano."""
    tiempos = {
        "tacos al pastor": "2 horas (incluye marinado)",
        "guacamole":       "10 minutos",
        "chiles en nogada": "3 horas",
        "pozole":          "4 horas",
        "mole poblano":    "6 horas",
    }
    platillo_lower = platillo.lower()
    for key, value in tiempos.items():
        if key in platillo_lower or platillo_lower in key:
            return f"Tiempo de preparación de {key}: {value}"
    return f"No tengo el tiempo de preparación de '{platillo}'."

@tool
def get_nivel_dificultad(platillo: str) -> str:
    """Devuelve el nivel de dificultad para preparar un platillo mexicano."""
    niveles = {
        "tacos al pastor": "⭐⭐⭐ Intermedio",
        "guacamole":       "⭐ Fácil",
        "chiles en nogada": "⭐⭐⭐⭐ Difícil",
        "pozole":          "⭐⭐⭐ Intermedio",
        "mole poblano":    "⭐⭐⭐⭐⭐ Experto",
    }
    platillo_lower = platillo.lower()
    for key, value in niveles.items():
        if key in platillo_lower or platillo_lower in key:
            return f"Dificultad de {key}: {value}"
    return f"No tengo el nivel de dificultad de '{platillo}'."

async def main():
    client = get_client()

    agent = Agent(
        client=client,
        name="ChefBot",
        instructions="""
        Eres un chef experto en cocina mexicana.
        Cuando te pregunten sobre un platillo, usa las herramientas disponibles
        para consultar ingredientes, tiempo de preparación y dificultad.
        Complementa la información de las herramientas con tu conocimiento.
        Sé amable y entusiasta en tus respuestas.
        """,
        tools=[get_ingredientes, get_tiempo_preparacion, get_nivel_dificultad],
    )

    print("=" * 55)
    print("🍳 ChefBot — Paso 2: Herramientas con @tool")
    print("=" * 55)

    preguntas = [
        "¿Qué ingredientes necesito para hacer guacamole?",
        "Quiero hacer mole poblano, ¿qué tan difícil es y cuánto tiempo tarda?",
        "Dame toda la información que tengas sobre los tacos al pastor.",
    ]

    for pregunta in preguntas:
        print(f"\n👤 Usuario: {pregunta}")
        resultado = await agent.run(pregunta)
        print(f"🤖 ChefBot: {resultado}")

asyncio.run(main())