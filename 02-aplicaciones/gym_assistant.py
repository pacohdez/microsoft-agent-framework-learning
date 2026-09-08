import os
import asyncio
import json
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

# ── Base de ejercicios ────────────────────────────────────

EJERCICIOS = {
    "pecho": {
        "hombre": ["Press de banca", "Aperturas con mancuernas", "Fondos en paralelas", "Press inclinado", "Cruces en polea"],
        "mujer":  ["Press con mancuernas", "Flexiones", "Aperturas en máquina", "Press en máquina", "Pull-over"],
    },
    "espalda": {
        "hombre": ["Dominadas", "Remo con barra", "Jalón al pecho", "Remo en polea", "Peso muerto"],
        "mujer":  ["Jalón al pecho", "Remo en máquina", "Peso muerto rumano", "Pullover en polea", "Remo con mancuerna"],
    },
    "piernas": {
        "hombre": ["Sentadilla", "Prensa de piernas", "Extensión de cuádriceps", "Curl femoral", "Pantorrillas de pie"],
        "mujer":  ["Sentadilla sumo", "Hip thrust", "Peso muerto rumano", "Abducción de cadera", "Curl femoral"],
    },
    "hombros": {
        "hombre": ["Press militar", "Elevaciones laterales", "Elevaciones frontales", "Pájaros", "Press Arnold"],
        "mujer":  ["Press con mancuernas", "Elevaciones laterales", "Elevaciones frontales", "Pájaros en máquina", "Face pull"],
    },
    "brazos": {
        "hombre": ["Curl con barra", "Extensión en polea", "Curl martillo", "Fondos en banco", "Curl concentrado"],
        "mujer":  ["Curl con mancuernas", "Extensión de tríceps", "Curl martillo", "Kickback de tríceps", "Curl en máquina"],
    },
    "abdomen": {
        "hombre": ["Crunch", "Plancha", "Elevación de piernas", "Rueda abdominal", "Crunch en polea"],
        "mujer":  ["Crunch", "Plancha", "Tijeras", "Mountain climbers", "Crunch oblicuo"],
    },
    "gluteos": {
        "hombre": ["Sentadilla profunda", "Peso muerto", "Estocadas", "Hip thrust", "Extensión de cadera"],
        "mujer":  ["Hip thrust", "Sentadilla búlgara", "Patada de glúteo", "Abducción en máquina", "Peso muerto rumano"],
    },
    "cardio": {
        "hombre": ["Caminadora 20 min", "Bicicleta estática 15 min", "Remo ergométrico 15 min", "Elíptica 20 min"],
        "mujer":  ["Caminadora inclinada 20 min", "Bicicleta estática 20 min", "Elíptica 20 min", "Saltar la cuerda 10 min"],
    },
}

SERIES_POR_TIEMPO = {
    30:  {"series": 2, "repeticiones": 10, "descanso": "45 seg"},
    45:  {"series": 3, "repeticiones": 12, "descanso": "60 seg"},
    60:  {"series": 3, "repeticiones": 12, "descanso": "75 seg"},
    90:  {"series": 4, "repeticiones": 15, "descanso": "90 seg"},
    120: {"series": 4, "repeticiones": 15, "descanso": "90 seg"},
}

# ── Herramientas ──────────────────────────────────────────

@tool
def obtener_ejercicios(area: str, genero: str) -> str:
    """Obtiene la lista de ejercicios para un área muscular y género específico.
    area: pecho, espalda, piernas, hombros, brazos, abdomen, gluteos, cardio.
    genero: hombre o mujer.
    """
    area = area.lower().replace("é", "e").replace("ó", "o")
    genero = genero.lower()

    if area not in EJERCICIOS:
        areas = ", ".join(EJERCICIOS.keys())
        return f"Área '{area}' no válida. Áreas disponibles: {areas}."
    if genero not in ["hombre", "mujer"]:
        return "Género no válido. Usa 'hombre' o 'mujer'."

    ejercicios = EJERCICIOS[area][genero]
    return f"Ejercicios de {area} para {genero}: {', '.join(ejercicios)}"


@tool
def obtener_config_series(tiempo_disponible_minutos: int) -> str:
    """Devuelve la configuración de series, repeticiones y descanso según el tiempo disponible.
    tiempo_disponible_minutos: tiempo en minutos (30, 45, 60, 90 o 120).
    """
    tiempos = sorted(SERIES_POR_TIEMPO.keys())
    tiempo_ajustado = min(tiempos, key=lambda t: abs(t - tiempo_disponible_minutos))
    config = SERIES_POR_TIEMPO[tiempo_ajustado]
    return (
        f"Con {tiempo_disponible_minutos} min disponibles: "
        f"{config['series']} series × {config['repeticiones']} repeticiones, "
        f"descanso {config['descanso']} entre series."
    )


@tool
def guardar_rutina(rutina_json: str) -> str:
    """Guarda la rutina semanal generada en un archivo JSON.
    Recibe la rutina como string JSON con la estructura:
    {dia: {area: str, ejercicios: [str], series: int, repeticiones: int, descanso: str}}
    """
    try:
        rutina = json.loads(rutina_json)
        with open("rutina_semanal.json", "w", encoding="utf-8") as f:
            json.dump(rutina, f, ensure_ascii=False, indent=2)
        return "Rutina guardada exitosamente en 'rutina_semanal.json'."
    except json.JSONDecodeError:
        return "Error: la rutina no tiene formato JSON válido."


@tool
def calcular_distribucion_dias(
    dias_por_semana: int,
    areas_objetivo: str,
) -> str:
    """Sugiere cómo distribuir los grupos musculares en los días disponibles.
    dias_por_semana: número de días (1 a 6).
    areas_objetivo: áreas separadas por coma, ej: 'pecho, espalda, piernas'.
    """
    areas = [a.strip().lower() for a in areas_objetivo.split(",")]

    distribuciones = {
        1: ["Full body (todo el cuerpo en una sesión)"],
        2: ["Día 1: tren superior", "Día 2: tren inferior"],
        3: ["Día 1: pecho + tríceps", "Día 2: espalda + bíceps", "Día 3: piernas + hombros"],
        4: ["Día 1: pecho + hombros", "Día 2: piernas", "Día 3: espalda + bíceps", "Día 4: brazos + abdomen"],
        5: ["Día 1: pecho", "Día 2: espalda", "Día 3: piernas", "Día 4: hombros + brazos", "Día 5: cardio + abdomen"],
        6: ["Día 1: pecho", "Día 2: espalda", "Día 3: piernas", "Día 4: hombros", "Día 5: brazos + abdomen", "Día 6: cardio + glúteos"],
    }

    if dias_por_semana not in distribuciones:
        return f"Días no válido. Elige entre 1 y 6 días."

    dist = distribuciones[dias_por_semana]
    resultado = f"Distribución sugerida para {dias_por_semana} días/semana:\n"
    resultado += "\n".join(f"  • {d}" for d in dist)
    resultado += f"\n\nÁreas objetivo detectadas: {', '.join(areas)}"
    return resultado


# ── Agente ────────────────────────────────────────────────

async def main():
    client = get_client()

    agent = Agent(
        client=client,
        name="GymBot",
        instructions="""
        Eres un entrenador personal experto llamado GymBot.
        Tu tarea es crear una rutina de gym semanal completamente personalizada.

        Flujo que debes seguir:
        1. Saluda y pregunta el nombre del usuario.
        2. Pregunta su género (hombre/mujer) para adaptar los ejercicios.
        3. Pregunta cuántos días por semana puede ir al gym.
        4. Pregunta cuántos minutos tiene disponibles por sesión.
        5. Pregunta qué áreas quiere trabajar (pecho, espalda, piernas, etc.)
           o si quiere trabajar todo el cuerpo.
        6. Pregunta su nivel: principiante, intermedio o avanzado.
        7. Usa calcular_distribucion_dias para sugerir cómo distribuir los grupos.
        8. Usa obtener_ejercicios y obtener_config_series para construir cada día.
        9. Presenta la rutina completa de forma clara, día por día.
        10. Usa guardar_rutina para guardar en JSON.
        11. Ofrece consejos finales según su nivel.
        12. Pregunta si desea ajustar algo.

        Consejos importantes:
        - Para principiantes: recomienda pesos ligeros y enfocarse en la técnica.
        - Para intermedios: sugiere progresión de cargas.
        - Para avanzados: sugiere técnicas como superseries o drop sets.
        - Siempre incluye al menos un día de descanso.
        - Siempre incluye calentamiento (5-10 min) y estiramiento (5 min).
        """,
        tools=[obtener_ejercicios, obtener_config_series,
               guardar_rutina, calcular_distribucion_dias],
    )

    session = agent.create_session()

    print("=" * 60)
    print("💪 GymBot — Asistente de Rutinas Personalizadas")
    print("=" * 60)
    print("(escribe 'salir' para terminar)\n")

    inicio = await agent.run(
        "El usuario acaba de abrir la app. Salúdalo e inicia el flujo.",
        session=session,
    )
    print(f"🤖 GymBot: {inicio}\n")

    while True:
        user_input = input("👤 Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            print("\n🤖 GymBot: ¡Mucho éxito en tus entrenamientos! 💪")
            break

        respuesta = await agent.run(user_input, session=session)
        print(f"\n🤖 GymBot: {respuesta}\n")

asyncio.run(main())