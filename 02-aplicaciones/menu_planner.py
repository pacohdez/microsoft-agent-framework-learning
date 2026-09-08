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

# ── Base de datos de platillos por categoría ──────────────

PLATILLOS = {
    "desayuno": {
        "mexicano":     ["Chilaquiles", "Huevos rancheros", "Tamales", "Atole con pan dulce", "Enfrijoladas"],
        "internacional": ["Avena", "Hotcakes", "Omelette", "Yogur con fruta", "Tostadas con aguacate"],
        "vegetariano":  ["Smoothie bowl", "Quesadillas de champiñones", "Fruta con granola", "Huevos con espinacas"],
    },
    "comida": {
        "mexicano":     ["Pozole", "Tacos de guisado", "Enchiladas", "Mole", "Caldo de res", "Chiles rellenos"],
        "internacional": ["Pasta", "Arroz frito", "Hamburguesa", "Ensalada César", "Sopa de verduras"],
        "vegetariano":  ["Lentejas", "Sopa de champiñones", "Tacos de nopales", "Curry de verduras"],
    },
    "cena": {
        "mexicano":     ["Quesadillas", "Sopa de lima", "Molletes", "Tostadas", "Enfrijoladas"],
        "internacional": ["Sándwich", "Pizza", "Wrap", "Ensalada mixta", "Crema de verduras"],
        "vegetariano":  ["Verduras al vapor", "Sopa de tomate", "Quesadillas de champiñones", "Ensalada de quinoa"],
    },
}

# ── Herramientas ──────────────────────────────────────────

@tool
def obtener_opciones_platillos(
    tiempo_del_dia: str,
    tipo_cocina: str,
) -> str:
    """Obtiene opciones de platillos según el tiempo del día y tipo de cocina.
    tiempo_del_dia: 'desayuno', 'comida' o 'cena'.
    tipo_cocina: 'mexicano', 'internacional' o 'vegetariano'.
    """
    tiempo = tiempo_del_dia.lower()
    tipo = tipo_cocina.lower()

    if tiempo not in PLATILLOS:
        return f"Tiempo del día '{tiempo}' no válido. Usa: desayuno, comida o cena."
    if tipo not in PLATILLOS[tiempo]:
        return f"Tipo de cocina '{tipo}' no válido. Usa: mexicano, internacional o vegetariano."

    opciones = PLATILLOS[tiempo][tipo]
    return f"Opciones de {tiempo} ({tipo}): {', '.join(opciones)}"


@tool
def guardar_menu(menu_json: str) -> str:
    """Guarda el menú semanal generado en un archivo JSON.
    Recibe el menú como string JSON con la estructura:
    {dia: {desayuno: str, comida: str, cena: str}}
    """
    try:
        menu = json.loads(menu_json)
        with open("menu_semanal.json", "w", encoding="utf-8") as f:
            json.dump(menu, f, ensure_ascii=False, indent=2)
        return "Menú guardado exitosamente en 'menu_semanal.json'."
    except json.JSONDecodeError:
        return "Error: el menú no tiene formato JSON válido."


@tool
def generar_lista_compras(menu_json: str) -> str:
    """Genera una lista de compras básica basada en el menú semanal.
    Recibe el menú como string JSON con la estructura:
    {dia: {desayuno: str, comida: str, cena: str}}
    """
    ingredientes_base = {
        "Chilaquiles":             ["tortillas", "salsa roja", "crema", "queso", "cebolla"],
        "Huevos rancheros":        ["huevos", "salsa", "tortillas", "frijoles"],
        "Tamales":                 ["masa", "chile", "carne de cerdo", "hoja de maíz"],
        "Pozole":                  ["maíz cacahuazintle", "cerdo", "chile guajillo", "lechuga", "rábano"],
        "Enchiladas":              ["tortillas", "chile ancho", "pollo", "crema", "queso"],
        "Quesadillas":             ["tortillas de harina", "queso Oaxaca", "chile"],
        "Lentejas":                ["lentejas", "jitomate", "cebolla", "ajo", "zanahoria"],
        "Pasta":                   ["pasta", "jitomate", "ajo", "albahaca", "queso parmesano"],
        "Curry de verduras":       ["papa", "zanahoria", "leche de coco", "curry en polvo"],
        "Ensalada César":          ["lechuga romana", "crutones", "queso parmesano", "aderezo César"],
        "Avena":                   ["avena", "leche", "miel", "fruta"],
        "Hotcakes":                ["harina", "huevo", "leche", "mantequilla", "miel"],
    }

    try:
        menu = json.loads(menu_json)
        compras = set()
        platillos_sin_mapa = []

        for dia, tiempos in menu.items():
            for _, platillo in tiempos.items():
                encontrado = False
                for nombre, ingredientes in ingredientes_base.items():
                    if nombre.lower() in platillo.lower():
                        compras.update(ingredientes)
                        encontrado = True
                        break
                if not encontrado:
                    platillos_sin_mapa.append(platillo)

        lista = sorted(compras)
        resultado = "Lista de compras:\n" + "\n".join(f"  • {i}" for i in lista)

        if platillos_sin_mapa:
            resultado += f"\n\nNota: agrega ingredientes para: {', '.join(set(platillos_sin_mapa))}"

        return resultado
    except json.JSONDecodeError:
        return "Error: formato de menú inválido."


# ── Agente ────────────────────────────────────────────────

async def main():
    client = get_client()

    agent = Agent(
        client=client,
        name="MenuBot",
        instructions="""
        Eres un nutricionista y chef experto llamado MenuBot.
        Tu tarea es crear un menú semanal personalizado (7 días, con desayuno, comida y cena).

        Flujo que debes seguir:
        1. Saluda y pregunta el nombre del usuario.
        2. Pregunta cuántas personas comen en casa.
        3. Pregunta sus preferencias: ¿mexicano, internacional, mixto o vegetariano?
        4. Pregunta si hay restricciones alimentarias (sin gluten, sin picante, alergia a lácteos, etc.)
        5. Con esa información, usa las herramientas para obtener opciones y genera el menú completo.
        6. Presenta el menú día por día de forma clara y atractiva.
        7. Usa guardar_menu para guardar el menú en JSON.
        8. Usa generar_lista_compras para generar y mostrar la lista de compras.
        9. Pregunta si desea ajustar algo.

        Cuando generes el menú para guardar, usa exactamente este formato JSON:
        {"Lunes": {"desayuno": "...", "comida": "...", "cena": "..."},
         "Martes": {"desayuno": "...", "comida": "...", "cena": "..."}, ...}
        """,
        tools=[obtener_opciones_platillos, guardar_menu, generar_lista_compras],
    )

    session = agent.create_session()

    print("=" * 60)
    print("🥗 MenuBot — Planificador de Menú Semanal")
    print("=" * 60)
    print("(escribe 'salir' para terminar)\n")

    # Mensaje inicial — el agente arranca la conversación
    inicio = await agent.run(
        "El usuario acaba de abrir la aplicación. Salúdalo e inicia el flujo.",
        session=session,
    )
    print(f"🤖 MenuBot: {inicio}\n")

    while True:
        user_input = input("👤 Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            print("\n🤖 MenuBot: ¡Hasta pronto! Que disfrutes tu semana de comidas.")
            break

        respuesta = await agent.run(user_input, session=session)
        print(f"\n🤖 MenuBot: {respuesta}\n")

asyncio.run(main())