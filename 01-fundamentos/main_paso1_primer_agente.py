"""
Paso 1 — Primer agente con Microsoft Agent Framework
Concepto: Agent, instructions, agent.run()
"""
import os
import asyncio
from dotenv import load_dotenv
from agent_framework import Agent
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

async def main():
    client = get_client()

    agent = Agent(
        client=client,
        name="ChefBot",
        instructions="""
        Eres un chef experto en cocina mexicana.
        Respondes preguntas sobre recetas, ingredientes y técnicas de cocina.
        Siempre eres amable, entusiasta y das consejos prácticos.
        Tus respuestas son concisas, máximo 3 párrafos.
        """,
    )

    preguntas = [
        "¿Cuáles son los ingredientes básicos del mole poblano?",
        "¿Cuál es el secreto para una buena salsa verde?",
    ]

    print("=" * 50)
    print("🍳 ChefBot — Paso 1: Primer agente")
    print("=" * 50)

    for pregunta in preguntas:
        print(f"\n👤 Usuario: {pregunta}")
        resultado = await agent.run(pregunta)
        print(f"🤖 ChefBot: {resultado}")

asyncio.run(main())