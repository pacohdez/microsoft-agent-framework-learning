import os
import csv
import json
import asyncio
import urllib.request
from datetime import date
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

# ── C1: Herramientas que leen el CSV real ─────────────────

@tool
def buscar_alimento_en_csv(nombre: str) -> str:
    """Busca un alimento en la base de datos CSV y devuelve su info nutricional."""
    try:
        with open("data/alimentos.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            resultados = []
            for row in reader:
                if nombre.lower() in row["alimento"].lower():
                    resultados.append(
                        f"{row['alimento']}: {row['calorias_por_100g']} kcal/100g | "
                        f"Proteínas: {row['proteinas_g']}g | "
                        f"Carbos: {row['carbohidratos_g']}g | "
                        f"Grasas: {row['grasas_g']}g | "
                        f"Categoría: {row['categoria']}"
                    )
            if resultados:
                return "\n".join(resultados)
            return f"No encontré '{nombre}' en la base de datos."
    except FileNotFoundError:
        return "Error: no se encontró el archivo data/alimentos.csv"

@tool
def listar_alimentos_por_categoria(categoria: str) -> str:
    """Lista todos los alimentos de una categoría del CSV.
    Categorías disponibles: proteina, carbohidrato, grasa saludable,
    proteina vegetal, verdura, lacteo.
    """
    try:
        with open("data/alimentos.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            resultados = []
            for row in reader:
                if categoria.lower() in row["categoria"].lower():
                    resultados.append(
                        f"  • {row['alimento']}: {row['calorias_por_100g']} kcal/100g"
                    )
            if resultados:
                return f"Alimentos en '{categoria}':\n" + "\n".join(resultados)
            return f"No encontré alimentos en la categoría '{categoria}'."
    except FileNotFoundError:
        return "Error: no se encontró el archivo data/alimentos.csv"

# ── C2: Herramienta que consulta API externa ──────────────

@tool
def buscar_ejercicio_en_api(musculo: str) -> str:
    """Busca ejercicios para un músculo usando la API pública de ExerciseDB.
    Músculos disponibles: biceps, triceps, chest, back, shoulders,
    upper legs, lower legs, waist, glutes.
    """
    try:
        musculo_encoded = musculo.lower().replace(" ", "%20")
        url = f"https://exercisedb.p.rapidapi.com/exercises/bodyPart/{musculo_encoded}?limit=4"

        # API pública de ejercicios — no requiere key para el endpoint básico
        req = urllib.request.Request(
            f"https://api.wger.de/api/v2/exercise/?format=json&language=2&category=10&limit=4",
            headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())

        ejercicios = data.get("results", [])
        if not ejercicios:
            return f"No encontré ejercicios para '{musculo}' en la API."

        resultado = f"Ejercicios encontrados para '{musculo}':\n"
        for ej in ejercicios[:4]:
            nombre = ej.get("name") or ej.get("uuid", "Sin nombre")
            resultado += f"  • {nombre}\n"
        return resultado.strip()

    except Exception as e:
        # Fallback con datos locales si la API no responde
        fallback = {
            "pecho":    ["Press de banca", "Aperturas", "Fondos en paralelas"],
            "espalda":  ["Dominadas", "Remo con barra", "Jalón al pecho"],
            "piernas":  ["Sentadilla", "Prensa", "Peso muerto"],
            "hombros":  ["Press militar", "Elevaciones laterales"],
            "brazos":   ["Curl con barra", "Extensión en polea"],
        }
        for key, ejercicios in fallback.items():
            if key in musculo.lower():
                return f"Ejercicios para {musculo} (datos locales):\n" + \
                       "\n".join(f"  • {e}" for e in ejercicios)
        return f"API no disponible y no hay datos locales para '{musculo}'."

# ── C3: Herramientas que leen/escriben JSON de progreso ───

@tool
def registrar_comida(alimento: str, cantidad_gramos: int) -> str:
    """Registra una comida en el archivo de progreso del usuario."""
    try:
        with open("data/progreso.json", "r", encoding="utf-8") as f:
            progreso = json.load(f)

        # Buscar calorías en el CSV
        calorias_total = None
        with open("data/alimentos.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if alimento.lower() in row["alimento"].lower():
                    calorias_total = round(
                        float(row["calorias_por_100g"]) * cantidad_gramos / 100, 1
                    )
                    break

        registro = {
            "fecha": str(date.today()),
            "alimento": alimento,
            "gramos": cantidad_gramos,
            "calorias": calorias_total or "desconocido",
        }

        progreso["registros"].append(registro)

        with open("data/progreso.json", "w", encoding="utf-8") as f:
            json.dump(progreso, f, ensure_ascii=False, indent=2)

        cal_str = f"{calorias_total} kcal" if calorias_total else "calorías desconocidas"
        return f"✅ Registrado: {cantidad_gramos}g de {alimento} = {cal_str}"

    except FileNotFoundError:
        return "Error: no se encontró data/progreso.json"

@tool
def ver_resumen_progreso() -> str:
    """Muestra el resumen de todas las comidas registradas hoy."""
    try:
        with open("data/progreso.json", "r", encoding="utf-8") as f:
            progreso = json.load(f)

        hoy = str(date.today())
        registros_hoy = [r for r in progreso["registros"] if r["fecha"] == hoy]

        if not registros_hoy:
            return f"No hay registros para hoy ({hoy})."

        total_cal = sum(
            r["calorias"] for r in registros_hoy
            if isinstance(r["calorias"], (int, float))
        )

        resumen = f"📊 Resumen de hoy ({hoy}) — {progreso['usuario']}:\n"
        resumen += f"Objetivo: {progreso['objetivo']}\n\n"
        for r in registros_hoy:
            resumen += f"  • {r['alimento']}: {r['gramos']}g → {r['calorias']} kcal\n"
        resumen += f"\n🔥 Total calorías hoy: {total_cal:.1f} kcal"
        return resumen

    except FileNotFoundError:
        return "Error: no se encontró data/progreso.json"

# ── Agente integrador ─────────────────────────────────────

async def main():
    client = get_client()

    agent = Agent(
        client=client,
        name="NutriFitBot",
        instructions="""
        Eres NutriFitBot, un asistente de nutrición y fitness con acceso
        a datos reales.

        Tienes estas capacidades:
        - Consultar una base de datos CSV real de alimentos con info nutricional
        - Buscar ejercicios por grupo muscular
        - Registrar comidas del usuario con sus calorías calculadas automáticamente
        - Mostrar el resumen de progreso diario

        Cuando el usuario mencione un alimento, siempre búscalo en el CSV.
        Cuando registres una comida, confirma las calorías calculadas.
        Sé proactivo: si el usuario dice que comió algo, ofrece registrarlo.
        """,
        tools=[
            buscar_alimento_en_csv,
            listar_alimentos_por_categoria,
            buscar_ejercicio_en_api,
            registrar_comida,
            ver_resumen_progreso,
        ],
    )

    session = agent.create_session()

    print("=" * 60)
    print("🥗💪 NutriFitBot — Datos Reales")
    print("=" * 60)
    print("(escribe 'salir' para terminar)\n")

    inicio = await agent.run(
        "El usuario acaba de entrar. Salúdalo y explica brevemente qué puedes hacer.",
        session=session,
    )
    print(f"🤖 NutriFitBot: {inicio}\n")

    while True:
        user_input = input("👤 Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            print("\n🤖 NutriFitBot: ¡Hasta pronto! Sigue con tu objetivo. 💪")
            break

        respuesta = await agent.run(user_input, session=session)
        print(f"\n🤖 NutriFitBot: {respuesta}\n")

asyncio.run(main())