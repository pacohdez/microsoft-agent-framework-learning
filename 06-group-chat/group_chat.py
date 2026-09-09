"""
Paso 6 — Group Chat con GroupChatBuilder
Conceptos: GroupChatState, set_select_speakers_func, speaker selection patterns
Todos los agentes comparten el historial completo de la conversación.
"""
import os
import asyncio
from dotenv import load_dotenv
from agent_framework import Role, WorkflowRunState
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.orchestrations import GroupChatBuilder, GroupChatState
from azure.identity import DefaultAzureCredential

load_dotenv()

# ── Cliente ───────────────────────────────────────────────

chat_client = OpenAIChatCompletionClient(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    credential=DefaultAzureCredential(),
    model=os.getenv("AZURE_OPENAI_MODEL"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

# ── Agentes participantes ─────────────────────────────────

creativo = chat_client.as_agent(
    name="Creativo",
    instructions="""
    Eres un chef creativo e innovador especializado en cocina mexicana.
    Propones ideas originales, fusiones atrevidas y técnicas modernas.
    Tus respuestas son entusiastas y visionarias. Máximo 3 oraciones.
    """,
    description="Chef creativo que propone ideas innovadoras.",
)

critico = chat_client.as_agent(
    name="Critico",
    instructions="""
    Eres un crítico gastronómico exigente y analítico.
    Evalúas las ideas desde la perspectiva de autenticidad, viabilidad
    y aceptación del público. Señalas problemas con respeto. Máximo 3 oraciones.
    """,
    description="Crítico gastronómico que evalúa ideas.",
)

sintetizador = chat_client.as_agent(
    name="Sintetizador",
    instructions="""
    Eres un chef ejecutivo que sintetiza debates gastronómicos.
    Tomas lo mejor de las ideas y críticas para proponer un plan concreto y equilibrado.
    Siempre terminas con una conclusión accionable. Máximo 3 oraciones.
    """,
    description="Chef ejecutivo que sintetiza y concluye.",
)

# ── Patrones de selección de speaker ─────────────────────

def seleccion_round_robin(state: GroupChatState) -> str:
    """Round Robin: cada agente habla en orden fijo."""
    nombres = list(state.participants.keys())
    return nombres[state.current_round % len(nombres)]


def seleccion_sin_repeticion(state: GroupChatState) -> str:
    """Sin repetición: el mismo agente no habla dos veces seguidas."""
    nombres = list(state.participants.keys())
    ultimo_speaker = None
    for msg in reversed(state.conversation):
        if hasattr(msg, "author_name") and msg.author_name:
            ultimo_speaker = msg.author_name
            break
    disponibles = [n for n in nombres if n != ultimo_speaker]
    return disponibles[state.current_round % len(disponibles)]


def seleccion_con_peso(state: GroupChatState) -> str:
    """Con peso: el Creativo habla más seguido."""
    patron = ["Creativo", "Critico", "Creativo", "Sintetizador"]
    return patron[state.current_round % len(patron)]


def seleccion_por_contenido(state: GroupChatState) -> str:
    """Por contenido: el siguiente speaker depende de lo que se dijo."""
    if state.current_round == 0:
        return "Creativo"
    ultimo_texto = ""
    if state.conversation:
        ultimo = state.conversation[-1]
        if hasattr(ultimo, "text") and ultimo.text:
            ultimo_texto = ultimo.text.lower()
    if any(w in ultimo_texto for w in ["idea", "propongo", "podría", "innovar"]):
        return "Critico"
    if any(w in ultimo_texto for w in ["problema", "riesgo", "difícil", "preocupa"]):
        return "Creativo"
    return "Sintetizador"


def terminar_por_consenso(state: GroupChatState) -> bool:
    """Termina cuando algún agente menciona consenso."""
    for msg in state.conversation:
        texto = msg.text.upper() if hasattr(msg, "text") and msg.text else ""
        if "CONSENSO" in texto or "ACUERDO" in texto or "CONCLUSIÓN" in texto:
            return True
    return False

# ── Ejecutor del workflow ─────────────────────────────────

async def ejecutar_group_chat(patron: str, tema: str):
    PATRONES = {
        "round_robin":    seleccion_round_robin,
        "sin_repeticion": seleccion_sin_repeticion,
        "con_peso":       seleccion_con_peso,
        "por_contenido":  seleccion_por_contenido,
    }
    fn_seleccion = PATRONES.get(patron, seleccion_round_robin)

    workflow = GroupChatBuilder(
        participants=[creativo, critico, sintetizador],
        selection_func=fn_seleccion,
        max_rounds=6,
    ).build()

    print(f"\n{'='*60}")
    print(f"🍳 Group Chat — Patrón: {patron.upper()}")
    print(f"📌 Tema: {tema}")
    print(f"{'='*60}\n")

    # ← Capturamos mensajes durante la ejecución
    transcripcion = []

    async for event in workflow.run(tema, stream=True):
        if (event.type == "executor_completed"
                and event.executor_id not in (None, "group_chat_orchestrator")
                and isinstance(event.data, list)
                and event.data
                and hasattr(event.data[0], "agent_response")):

            respuesta = event.data[0].agent_response
            if hasattr(respuesta, "messages"):
                for msg in respuesta.messages:
                    if hasattr(msg, "text") and msg.text:
                        transcripcion.append({
                            "agente": event.executor_id,
                            "texto": msg.text,
                        })

        elif event.type == "status":
            if event.state == WorkflowRunState.IDLE:
                print("✅ Group chat finalizado!\n")

    # Mostrar transcripción
    if transcripcion:
        print(f"\n{'='*60}")
        print("📋 TRANSCRIPCIÓN COMPLETA")
        print(f"{'='*60}")
        for i, entrada in enumerate(transcripcion, start=1):
            print(f"\n{'-'*60}")
            print(f"{i:02d} [{entrada['agente']}]")
            print(f"{'-'*60}")
            print(entrada["texto"])
    else:
        # Fallback: inspeccionar todos los eventos
        print("⚠️ No se capturaron mensajes — revisando estructura de eventos...")
        async for event in workflow.run(tema, stream=True):
            print(f"Evento: {event.type} | executor: {getattr(event, 'executor_id', '-')}")
            if hasattr(event, "data") and event.data is not None:
                print(f"  data type: {type(event.data)}")
                print(f"  data: {event.data}")

# ── Main ──────────────────────────────────────────────────

async def main():
    tema = "¿Cómo podemos modernizar los tacos al pastor manteniendo su esencia?"

    # Prueba el patrón que prefieras cambiando este valor:
    # "round_robin" | "sin_repeticion" | "con_peso" | "por_contenido"
    await ejecutar_group_chat(patron="round_robin", tema=tema)

asyncio.run(main())