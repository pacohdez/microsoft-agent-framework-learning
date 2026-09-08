import os
import asyncio
from dotenv import load_dotenv
from agent_framework import tool, WorkflowEvent
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.orchestrations import HandoffBuilder, HandoffAgentUserRequest
from azure.identity import DefaultAzureCredential

load_dotenv()

# ── Cliente ───────────────────────────────────────────────

chat_client = OpenAIChatCompletionClient(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    credential=DefaultAzureCredential(),
    model=os.getenv("AZURE_OPENAI_MODEL"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# ── Herramientas de Nutrición ─────────────────────────────

@tool
def consultar_calorias(alimento: str) -> str:
    """Consulta las calorías aproximadas de un alimento."""
    calorias = {
        "arroz": "130 kcal por 100g", "pollo": "165 kcal por 100g",
        "aguacate": "160 kcal por 100g", "huevo": "155 kcal por 100g",
        "tortilla": "218 kcal por 100g", "frijoles": "127 kcal por 100g",
        "atún": "116 kcal por 100g", "plátano": "89 kcal por 100g",
    }
    for key, value in calorias.items():
        if key in alimento.lower():
            return f"{alimento}: {value}"
    return f"No tengo datos de calorías para '{alimento}'."

@tool
def sugerir_comida_saludable(objetivo: str) -> str:
    """Sugiere opciones de comida según el objetivo del usuario."""
    sugerencias = {
        "bajar peso":    "Ensalada de pollo, verduras al vapor, fruta fresca.",
        "ganar músculo": "Arroz con pollo, huevos, atún, frutos secos.",
        "mantenimiento": "Dieta balanceada: proteínas, carbohidratos y grasas saludables.",
        "energía":       "Avena, plátano, frutos secos, batatas, quinoa.",
        "vegetariano":   "Legumbres, tofu, quinoa, huevos, verduras de hoja verde.",
    }
    for key, value in sugerencias.items():
        if key in objetivo.lower():
            return f"Para {key}: {value}"
    return f"Para '{objetivo}': mantén una dieta variada y equilibrada."

# ── Herramientas de Ejercicio ─────────────────────────────

@tool
def consultar_calorias_ejercicio(ejercicio: str, minutos: int) -> str:
    """Consulta las calorías quemadas en un ejercicio según el tiempo."""
    calorias_por_minuto = {
        "correr": 10, "caminar": 4, "ciclismo": 8,
        "natación": 9, "pesas": 6, "yoga": 3, "elíptica": 7,
    }
    for key, cal_min in calorias_por_minuto.items():
        if key in ejercicio.lower():
            return f"{ejercicio} por {minutos} min: ~{cal_min * minutos} kcal quemadas."
    return f"No tengo datos para '{ejercicio}', pero cualquier actividad es beneficiosa."

@tool
def recomendar_ejercicio_por_objetivo(objetivo: str, nivel: str) -> str:
    """Recomienda tipo de ejercicio según objetivo y nivel del usuario."""
    recomendaciones = {
        ("bajar peso",    "principiante"): "Caminar 30 min, natación suave, yoga.",
        ("bajar peso",    "intermedio"):   "Correr 20 min, HIIT 3x/semana, ciclismo.",
        ("ganar músculo", "principiante"): "Pesas con peso ligero, 3 días/semana.",
        ("ganar músculo", "intermedio"):   "Pesas progresivas, 4 días/semana.",
        ("resistencia",   "principiante"): "Caminar + trotar intervalado.",
        ("resistencia",   "intermedio"):   "Correr 5K, natación continua.",
    }
    key = (objetivo.lower(), nivel.lower())
    if key in recomendaciones:
        return f"Para {objetivo} ({nivel}): {recomendaciones[key]}"
    return f"Para {objetivo} ({nivel}): combina cardio y fuerza progresivamente."

# ── Agentes (usando as_agent()) ───────────────────────────

coordinador = chat_client.as_agent(
    name="CoordinadorBot",
    instructions="""
    Eres un coordinador de bienestar llamado CoordinadorBot.
    Saluda al usuario y explica que tienes dos especialistas disponibles:
    - NutricionBot: para preguntas de alimentación, dieta y calorías de alimentos.
    - EjercicioBot: para preguntas de ejercicio, rutinas y calorías quemadas.
    Transfiere al especialista correcto según lo que necesite el usuario.
    Cuando hagas handoff, avisa brevemente al usuario con quién va a hablar.
    """,
    description="Coordinador que enruta al especialista correcto.",
    require_per_service_call_history_persistence=True,
)

nutricion = chat_client.as_agent(
    name="NutricionBot",
    instructions="""
    Eres un nutricionista experto llamado NutricionBot.
    Te especializas en alimentación saludable, calorías y planes de comida.
    Usa tus herramientas para dar información precisa.
    Si te preguntan sobre ejercicio, transfiere de vuelta al CoordinadorBot.
    """,
    description="Especialista en nutrición y alimentación saludable.",
    tools=[consultar_calorias, sugerir_comida_saludable],
    require_per_service_call_history_persistence=True,
)

ejercicio = chat_client.as_agent(
    name="EjercicioBot",
    instructions="""
    Eres un entrenador personal experto llamado EjercicioBot.
    Te especializas en rutinas de ejercicio y rendimiento físico.
    Usa tus herramientas para dar recomendaciones precisas.
    Si te preguntan sobre nutrición, transfiere de vuelta al CoordinadorBot.
    """,
    description="Especialista en rutinas de ejercicio y entrenamiento.",
    tools=[consultar_calorias_ejercicio, recomendar_ejercicio_por_objetivo],
    require_per_service_call_history_persistence=True,
)

# ── Workflow ──────────────────────────────────────────────

workflow = (
    HandoffBuilder(
        name="bienestar",
        participants=[coordinador, nutricion, ejercicio],
    )
    .with_start_agent(coordinador)
    .add_handoff(coordinador, [nutricion, ejercicio])
    .add_handoff(nutricion,   [coordinador])
    .add_handoff(ejercicio,   [coordinador])
    .build()
)

# ── Main ──────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("🌟 BienestarBot — Nutrición + Ejercicio")
    print("=" * 60)
    print("(escribe 'salir' para terminar)\n")

    pending_requests: list[WorkflowEvent] = []

    # Mensaje inicial
    async for event in workflow.run(
        "El usuario acaba de entrar. Salúdalo y preséntate brevemente.",
        stream=True,
    ):
        if event.type == "request_info":
            pending_requests.append(event)
            for msg in event.data.agent_response.messages[-1:]:
                print(f"🤖 [{event._source_executor_id}]: {msg.text}\n")

    # Loop conversacional
    while True:
        user_input = input("👤 Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            print("\n🤖 Bot: ¡Cuídate mucho! Hasta pronto. 💪🥗")
            break

        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(user_input)
            for req in pending_requests
        }

        pending_requests = []
        async for event in workflow.run(responses=responses, stream=True):
            if event.type == "request_info" and isinstance(event.data, HandoffAgentUserRequest):
                pending_requests.append(event)
                for msg in event.data.agent_response.messages[-1:]:
                    print(f"\n🤖 [{event._source_executor_id}]: {msg.text}\n")

asyncio.run(main())