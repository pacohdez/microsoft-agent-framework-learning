"""
Paso 3 — Conversaciones multi-turno con memoria de sesión
Conceptos: agent.create_session(), session=session en cada run()
Sin sesión: el LLM recibe [system] + [mensaje actual]
Con sesión: el LLM recibe [system] + [historial completo] + [mensaje actual]
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
        Eres un chef experto en cocina mexicana llamado ChefBot.
        Cuando te pregunten sobre un platillo, usa las herramientas disponibles.
        Recuerda el contexto de la conversación para dar respuestas personalizadas.
        Sé amable, entusiasta y usa el nombre del usuario si te lo dice.
        """,
        tools=[get_ingredientes, get_tiempo_preparacion, get_nivel_dificultad],
    )

    # La clave: crear sesión y pasarla en cada run()
    session = agent.create_session()

    print("=" * 55)
    print("🍳 ChefBot — Paso 3: Conversación con memoria de sesión")
    print("(escribe 'salir' para terminar)")
    print("=" * 55)

    while True:
        user_input = input("\n👤 Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            print("\n🤖 ChefBot: ¡Hasta luego! Que disfrutes cocinando.")
            break
        resultado = await agent.run(user_input, session=session)
        print(f"\n🤖 ChefBot: {resultado}")

asyncio.run(main())