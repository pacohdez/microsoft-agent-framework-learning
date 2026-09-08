# 📘 Resumen de Aprendizaje — Microsoft Agent Framework (MAF)

> Python 3.11 · `uv` · Azure OpenAI · Service Principal

---

## ⚙️ Configuración del entorno

### Instalación de paquetes

```bash
uv init mi-agente --python 3.11
cd mi-agente
uv add agent-framework-core
uv add agent-framework-openai
uv add agent-framework-orchestrations
uv add azure-identity
uv add python-dotenv
```

### Archivo `.env`

```env
AZURE_TENANT_ID=tu-tenant-id
AZURE_CLIENT_ID=tu-client-id
AZURE_CLIENT_SECRET=tu-client-secret
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

### Patrón de cliente (usado en todos los archivos)

```python
import os
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential

load_dotenv()  # siempre explícito — MAF no lo carga automáticamente

def get_client():
    return OpenAIChatCompletionClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        credential=DefaultAzureCredential(),
        model=os.getenv("AZURE_OPENAI_MODEL"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
```

### Lecciones clave de configuración

- La autenticación por API key puede estar deshabilitada en Azure — usar `DefaultAzureCredential()` con Service Principal
- `load_dotenv()` debe llamarse explícitamente en cada script
- `AZURE_OPENAI_MODEL` debe ser el nombre del **deployment** (`gpt-4o`), no el alias del modelo
- El import correcto del decorador es `from agent_framework import tool`
- Los `ExperimentalWarning` de `SkillResource` y `MemoryStore` son no bloqueantes

---

## ✅ Paso 1 — Primer agente (`main.py`)

**Conceptos:** `Agent`, `instructions`, `agent.run()`

```python
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

    for pregunta in preguntas:
        print(f"\n👤 Usuario: {pregunta}")
        resultado = await agent.run(pregunta)
        print(f"🤖 ChefBot: {resultado}")

asyncio.run(main())
```

---

## ✅ Paso 2 — Herramientas con `@tool` (`main.py` actualizado)

**Conceptos:** `@tool` decorator, `tools=[...]`, invocación paralela automática

```python
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
        "guacamole": "aguacate, limón, cebolla, cilantro, chile serrano, sal",
        "chiles en nogada": "chile poblano, picadillo de carne, nogada, granada, perejil",
        "pozole": "maíz cacahuazintle, cerdo, chile guajillo, orégano, lechuga, rábano",
        "mole poblano": "chile mulato, chile ancho, chocolate, ajonjolí, plátano macho, pavo",
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
        "guacamole": "10 minutos",
        "chiles en nogada": "3 horas",
        "pozole": "4 horas",
        "mole poblano": "6 horas",
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
        "guacamole": "⭐ Fácil",
        "chiles en nogada": "⭐⭐⭐⭐ Difícil",
        "pozole": "⭐⭐⭐ Intermedio",
        "mole poblano": "⭐⭐⭐⭐⭐ Experto",
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
```

---

## ✅ Paso 3 — Conversaciones multi-turno con sesión (`main.py` final)

**Conceptos:** `agent.create_session()`, `session=session` en cada `run()`

```python
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

    print("=== ChefBot — Modo conversación (escribe 'salir' para terminar) ===")

    while True:
        user_input = input("\n👤 Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            break
        resultado = await agent.run(user_input, session=session)
        print(f"\n🤖 ChefBot: {resultado}")

asyncio.run(main())
```

> **Cómo funciona la sesión:**
> Sin sesión → el LLM recibe solo `[system] + [user actual]`
> Con sesión → el LLM recibe `[system] + [historial completo] + [user actual]`

---

## ✅ Paso 4A — MenuBot (`menu_planner.py`)

**Conceptos:** flujo orquestado de 9 pasos, herramientas con efectos reales (guardar JSON), lista de compras generada automáticamente

```python
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

PLATILLOS = {
    "desayuno": {
        "mexicano":      ["Chilaquiles", "Huevos rancheros", "Tamales", "Atole con pan dulce", "Enfrijoladas"],
        "internacional": ["Avena", "Hotcakes", "Omelette", "Yogur con fruta", "Tostadas con aguacate"],
        "vegetariano":   ["Smoothie bowl", "Quesadillas de champiñones", "Fruta con granola"],
    },
    "comida": {
        "mexicano":      ["Pozole", "Tacos de guisado", "Enchiladas", "Mole", "Caldo de res"],
        "internacional": ["Pasta", "Arroz frito", "Hamburguesa", "Ensalada César"],
        "vegetariano":   ["Lentejas", "Sopa de champiñones", "Tacos de nopales"],
    },
    "cena": {
        "mexicano":      ["Quesadillas", "Sopa de lima", "Molletes", "Tostadas"],
        "internacional": ["Sándwich", "Pizza", "Wrap", "Ensalada mixta"],
        "vegetariano":   ["Verduras al vapor", "Sopa de tomate", "Ensalada de quinoa"],
    },
}

@tool
def obtener_opciones_platillos(tiempo_del_dia: str, tipo_cocina: str) -> str:
    """Obtiene opciones de platillos según el tiempo del día y tipo de cocina.
    tiempo_del_dia: 'desayuno', 'comida' o 'cena'.
    tipo_cocina: 'mexicano', 'internacional' o 'vegetariano'.
    """
    tiempo = tiempo_del_dia.lower()
    tipo = tipo_cocina.lower()
    if tiempo not in PLATILLOS:
        return f"Tiempo '{tiempo}' no válido. Usa: desayuno, comida o cena."
    if tipo not in PLATILLOS[tiempo]:
        return f"Tipo '{tipo}' no válido. Usa: mexicano, internacional o vegetariano."
    opciones = PLATILLOS[tiempo][tipo]
    return f"Opciones de {tiempo} ({tipo}): {', '.join(opciones)}"

@tool
def guardar_menu(menu_json: str) -> str:
    """Guarda el menú semanal en un archivo JSON.
    Formato: {dia: {desayuno: str, comida: str, cena: str}}
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
    """Genera una lista de compras basada en el menú semanal."""
    ingredientes_base = {
        "Chilaquiles":      ["tortillas", "salsa roja", "crema", "queso", "cebolla"],
        "Huevos rancheros": ["huevos", "salsa", "tortillas", "frijoles"],
        "Pozole":           ["maíz cacahuazintle", "cerdo", "chile guajillo", "lechuga", "rábano"],
        "Enchiladas":       ["tortillas", "chile ancho", "pollo", "crema", "queso"],
        "Quesadillas":      ["tortillas de harina", "queso Oaxaca", "chile"],
        "Lentejas":         ["lentejas", "jitomate", "cebolla", "ajo", "zanahoria"],
        "Pasta":            ["pasta", "jitomate", "ajo", "albahaca", "queso parmesano"],
        "Avena":            ["avena", "leche", "miel", "fruta"],
        "Hotcakes":         ["harina", "huevo", "leche", "mantequilla", "miel"],
    }
    try:
        menu = json.loads(menu_json)
        compras = set()
        sin_mapa = []
        for dia, tiempos in menu.items():
            for _, platillo in tiempos.items():
                encontrado = False
                for nombre, ingredientes in ingredientes_base.items():
                    if nombre.lower() in platillo.lower():
                        compras.update(ingredientes)
                        encontrado = True
                        break
                if not encontrado:
                    sin_mapa.append(platillo)
        lista = sorted(compras)
        resultado = "Lista de compras:\n" + "\n".join(f"  • {i}" for i in lista)
        if sin_mapa:
            resultado += f"\n\nAgrega ingredientes para: {', '.join(set(sin_mapa))}"
        return resultado
    except json.JSONDecodeError:
        return "Error: formato de menú inválido."

async def main():
    client = get_client()
    agent = Agent(
        client=client,
        name="MenuBot",
        instructions="""
        Eres un nutricionista y chef experto llamado MenuBot.
        Tu tarea es crear un menú semanal personalizado (7 días, desayuno/comida/cena).
        Flujo: 1) saluda y pregunta nombre, 2) cuántas personas, 3) preferencias de cocina,
        4) restricciones alimentarias, 5) genera el menú usando las herramientas,
        6) presenta día por día, 7) guarda con guardar_menu,
        8) genera lista de compras, 9) pregunta si ajustar algo.
        JSON para guardar: {"Lunes": {"desayuno":"...","comida":"...","cena":"..."}, ...}
        """,
        tools=[obtener_opciones_platillos, guardar_menu, generar_lista_compras],
    )
    session = agent.create_session()

    print("=" * 60)
    print("🥗 MenuBot — Planificador de Menú Semanal")
    print("=" * 60)

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
            break
        respuesta = await agent.run(user_input, session=session)
        print(f"\n🤖 MenuBot: {respuesta}\n")

asyncio.run(main())
```

---

## ✅ Paso 4B — GymBot (`gym_assistant.py`)

**Conceptos:** herramientas con múltiples parámetros, flujo orquestado de 12 pasos, distribución por días

```python
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

EJERCICIOS = {
    "pecho":   {"hombre": ["Press de banca", "Aperturas con mancuernas", "Fondos en paralelas", "Press inclinado"],
                "mujer":  ["Press con mancuernas", "Flexiones", "Aperturas en máquina", "Press en máquina"]},
    "espalda": {"hombre": ["Dominadas", "Remo con barra", "Jalón al pecho", "Peso muerto"],
                "mujer":  ["Jalón al pecho", "Remo en máquina", "Peso muerto rumano", "Pullover en polea"]},
    "piernas": {"hombre": ["Sentadilla", "Prensa de piernas", "Curl femoral", "Pantorrillas de pie"],
                "mujer":  ["Sentadilla sumo", "Hip thrust", "Peso muerto rumano", "Curl femoral"]},
    "hombros": {"hombre": ["Press militar", "Elevaciones laterales", "Press Arnold"],
                "mujer":  ["Press con mancuernas", "Elevaciones laterales", "Face pull"]},
    "brazos":  {"hombre": ["Curl con barra", "Extensión en polea", "Curl martillo"],
                "mujer":  ["Curl con mancuernas", "Extensión de tríceps", "Kickback de tríceps"]},
    "abdomen": {"hombre": ["Crunch", "Plancha", "Elevación de piernas", "Rueda abdominal"],
                "mujer":  ["Crunch", "Plancha", "Tijeras", "Mountain climbers"]},
    "gluteos": {"hombre": ["Sentadilla profunda", "Hip thrust", "Estocadas"],
                "mujer":  ["Hip thrust", "Sentadilla búlgara", "Patada de glúteo"]},
    "cardio":  {"hombre": ["Caminadora 20 min", "Bicicleta estática 15 min", "Elíptica 20 min"],
                "mujer":  ["Caminadora inclinada 20 min", "Bicicleta estática 20 min", "Elíptica 20 min"]},
}

SERIES_POR_TIEMPO = {
    30:  {"series": 2, "repeticiones": 10, "descanso": "45 seg"},
    45:  {"series": 3, "repeticiones": 12, "descanso": "60 seg"},
    60:  {"series": 3, "repeticiones": 12, "descanso": "75 seg"},
    90:  {"series": 4, "repeticiones": 15, "descanso": "90 seg"},
    120: {"series": 4, "repeticiones": 15, "descanso": "90 seg"},
}

@tool
def obtener_ejercicios(area: str, genero: str) -> str:
    """Obtiene ejercicios para un área muscular y género.
    area: pecho, espalda, piernas, hombros, brazos, abdomen, gluteos, cardio.
    genero: hombre o mujer.
    """
    area = area.lower().replace("é","e").replace("ó","o")
    genero = genero.lower()
    if area not in EJERCICIOS:
        return f"Área '{area}' no válida. Disponibles: {', '.join(EJERCICIOS.keys())}"
    if genero not in ["hombre", "mujer"]:
        return "Género no válido. Usa 'hombre' o 'mujer'."
    ejercicios = EJERCICIOS[area][genero]
    return f"Ejercicios de {area} para {genero}: {', '.join(ejercicios)}"

@tool
def obtener_config_series(tiempo_disponible_minutos: int) -> str:
    """Devuelve series, repeticiones y descanso según el tiempo disponible."""
    tiempos = sorted(SERIES_POR_TIEMPO.keys())
    tiempo_ajustado = min(tiempos, key=lambda t: abs(t - tiempo_disponible_minutos))
    config = SERIES_POR_TIEMPO[tiempo_ajustado]
    return (f"Con {tiempo_disponible_minutos} min: {config['series']} series × "
            f"{config['repeticiones']} reps, descanso {config['descanso']}.")

@tool
def guardar_rutina(rutina_json: str) -> str:
    """Guarda la rutina semanal en un archivo JSON."""
    try:
        rutina = json.loads(rutina_json)
        with open("rutina_semanal.json", "w", encoding="utf-8") as f:
            json.dump(rutina, f, ensure_ascii=False, indent=2)
        return "Rutina guardada en 'rutina_semanal.json'."
    except json.JSONDecodeError:
        return "Error: formato JSON inválido."

@tool
def calcular_distribucion_dias(dias_por_semana: int, areas_objetivo: str) -> str:
    """Sugiere cómo distribuir los grupos musculares en los días disponibles."""
    distribuciones = {
        1: ["Full body (todo el cuerpo)"],
        2: ["Día 1: tren superior", "Día 2: tren inferior"],
        3: ["Día 1: pecho + tríceps", "Día 2: espalda + bíceps", "Día 3: piernas + hombros"],
        4: ["Día 1: pecho + hombros", "Día 2: piernas", "Día 3: espalda + bíceps", "Día 4: brazos + abdomen"],
        5: ["Día 1: pecho", "Día 2: espalda", "Día 3: piernas", "Día 4: hombros + brazos", "Día 5: cardio + abdomen"],
        6: ["Día 1: pecho", "Día 2: espalda", "Día 3: piernas", "Día 4: hombros", "Día 5: brazos + abdomen", "Día 6: cardio + glúteos"],
    }
    if dias_por_semana not in distribuciones:
        return "Elige entre 1 y 6 días."
    dist = distribuciones[dias_por_semana]
    resultado = f"Distribución para {dias_por_semana} días/semana:\n"
    resultado += "\n".join(f"  • {d}" for d in dist)
    resultado += f"\n\nÁreas objetivo: {areas_objetivo}"
    return resultado

async def main():
    client = get_client()
    agent = Agent(
        client=client,
        name="GymBot",
        instructions="""
        Eres un entrenador personal experto llamado GymBot.
        Flujo: 1) nombre, 2) género, 3) días/semana, 4) minutos/sesión,
        5) áreas a trabajar, 6) nivel (principiante/intermedio/avanzado),
        7) usa calcular_distribucion_dias, 8) usa obtener_ejercicios y
        obtener_config_series por cada día, 9) presenta la rutina completa,
        10) guarda con guardar_rutina, 11) da consejos según nivel,
        12) pregunta si ajustar algo.
        """,
        tools=[obtener_ejercicios, obtener_config_series,
               guardar_rutina, calcular_distribucion_dias],
    )
    session = agent.create_session()

    print("=" * 60)
    print("💪 GymBot — Asistente de Rutinas Personalizadas")
    print("=" * 60)

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
            break
        respuesta = await agent.run(user_input, session=session)
        print(f"\n🤖 GymBot: {respuesta}\n")

asyncio.run(main())
```

---

## ✅ Camino A — Handoff multi-agente (`03_bienestar_agent.py`)

**Conceptos:** `HandoffBuilder`, `client.as_agent()`, `add_handoff()`, `require_per_service_call_history_persistence=True`, `workflow.run(stream=True)`, `HandoffAgentUserRequest`, `_source_executor_id`

```python
import os
import asyncio
from dotenv import load_dotenv
from agent_framework import tool, WorkflowEvent
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework.orchestrations import HandoffBuilder, HandoffAgentUserRequest
from azure.identity import DefaultAzureCredential

load_dotenv()

chat_client = OpenAIChatCompletionClient(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    credential=DefaultAzureCredential(),
    model=os.getenv("AZURE_OPENAI_MODEL"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

@tool
def consultar_calorias(alimento: str) -> str:
    """Consulta las calorías aproximadas de un alimento."""
    calorias = {
        "arroz": "130 kcal/100g", "pollo": "165 kcal/100g",
        "aguacate": "160 kcal/100g", "huevo": "155 kcal/100g",
        "frijoles": "127 kcal/100g", "atún": "116 kcal/100g",
        "plátano": "89 kcal/100g",
    }
    for key, value in calorias.items():
        if key in alimento.lower():
            return f"{alimento}: {value}"
    return f"No tengo datos para '{alimento}'."

@tool
def sugerir_comida_saludable(objetivo: str) -> str:
    """Sugiere opciones de comida según el objetivo del usuario."""
    sugerencias = {
        "bajar peso":    "Ensalada de pollo, verduras al vapor, fruta fresca.",
        "ganar músculo": "Arroz con pollo, huevos, atún, frutos secos.",
        "mantenimiento": "Dieta balanceada: proteínas, carbohidratos y grasas saludables.",
    }
    for key, value in sugerencias.items():
        if key in objetivo.lower():
            return f"Para {key}: {value}"
    return f"Para '{objetivo}': mantén una dieta variada y equilibrada."

@tool
def consultar_calorias_ejercicio(ejercicio: str, minutos: int) -> str:
    """Consulta las calorías quemadas en un ejercicio según el tiempo."""
    calorias_por_minuto = {
        "correr": 10, "caminar": 4, "ciclismo": 8,
        "natación": 9, "pesas": 6, "yoga": 3, "elíptica": 7,
    }
    for key, cal_min in calorias_por_minuto.items():
        if key in ejercicio.lower():
            return f"{ejercicio} por {minutos} min: ~{cal_min * minutos} kcal."
    return f"No tengo datos para '{ejercicio}'."

@tool
def recomendar_ejercicio_por_objetivo(objetivo: str, nivel: str) -> str:
    """Recomienda ejercicio según objetivo y nivel."""
    recomendaciones = {
        ("bajar peso",    "principiante"): "Caminar 30 min, natación suave, yoga.",
        ("bajar peso",    "intermedio"):   "Correr 20 min, HIIT 3x/semana, ciclismo.",
        ("ganar músculo", "principiante"): "Pesas con peso ligero, 3 días/semana.",
        ("ganar músculo", "intermedio"):   "Pesas progresivas, 4 días/semana.",
    }
    key = (objetivo.lower(), nivel.lower())
    if key in recomendaciones:
        return f"Para {objetivo} ({nivel}): {recomendaciones[key]}"
    return f"Para {objetivo} ({nivel}): combina cardio y fuerza progresivamente."

# Agentes con client.as_agent() — requerido para HandoffBuilder
coordinador = chat_client.as_agent(
    name="CoordinadorBot",
    instructions="""
    Eres un coordinador de bienestar. Tienes dos especialistas:
    - NutricionBot: alimentación, dieta, calorías de alimentos.
    - EjercicioBot: ejercicio, rutinas, calorías quemadas.
    Transfiere al especialista correcto según la pregunta del usuario.
    """,
    description="Coordinador que enruta al especialista correcto.",
    require_per_service_call_history_persistence=True,
)

nutricion = chat_client.as_agent(
    name="NutricionBot",
    instructions="""
    Eres un nutricionista experto. Usa tus herramientas para información precisa.
    Si preguntan sobre ejercicio, transfiere al CoordinadorBot.
    """,
    description="Especialista en nutrición y alimentación.",
    tools=[consultar_calorias, sugerir_comida_saludable],
    require_per_service_call_history_persistence=True,
)

ejercicio = chat_client.as_agent(
    name="EjercicioBot",
    instructions="""
    Eres un entrenador personal experto. Usa tus herramientas para recomendaciones precisas.
    Si preguntan sobre nutrición, transfiere al CoordinadorBot.
    """,
    description="Especialista en rutinas de ejercicio.",
    tools=[consultar_calorias_ejercicio, recomendar_ejercicio_por_objetivo],
    require_per_service_call_history_persistence=True,
)

# Construcción del workflow con topología de handoffs
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

async def main():
    print("=" * 60)
    print("🌟 BienestarBot — Nutrición + Ejercicio")
    print("=" * 60)

    pending_requests: list[WorkflowEvent] = []

    # Mensaje inicial
    async for event in workflow.run(
        "El usuario acaba de entrar. Salúdalo y preséntate.",
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
```

---

## ✅ Camino B — Sequential y Concurrent (`04_workflows.py`)

**Conceptos:** `SequentialBuilder` (pipeline en cadena), `ConcurrentBuilder` (ejecución paralela), `result.get_outputs()`

```python
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

async def demo_sequential():
    client = get_client()

    analizador = Agent(
        client=client, name="AnalizadorBot",
        instructions="Dado un platillo identifica: ingredientes principales (máx 5), técnica de cocción y tiempo estimado. Sé conciso.",
    )
    nutricionista = Agent(
        client=client, name="NutricionistaBot",
        instructions="Basándote en el análisis anterior: estima calorías por porción, macronutrientes y da una calificación de salud del 1 al 10. No repitas lo anterior.",
    )
    presentador = Agent(
        client=client, name="PresentadorBot",
        instructions="Toma el análisis completo anterior y crea una ficha de receta atractiva con: nombre+emoji, resumen, ingredientes, técnica+tiempo, info nutricional y puntuación. Usa emojis.",
    )

    # La salida de cada agente alimenta al siguiente automáticamente
    workflow = SequentialBuilder(
        participants=[analizador, nutricionista, presentador],
        intermediate_output_from=[analizador, nutricionista],
    ).build()

    print("=" * 60)
    print("🔄 SEQUENTIAL — Pipeline de análisis de recetas")
    print("=" * 60)

    result = await workflow.run("Analiza este platillo: Tacos al pastor")
    for output in result.get_outputs():
        for msg in output.messages:
            print(f"\n[{msg.author_name}]:\n{msg.text}\n")
            print("-" * 60)

async def demo_concurrent():
    client = get_client()

    chef = Agent(
        client=client, name="ChefBot",
        instructions="Dado un platillo, describe en 3-4 líneas: técnica de preparación, secreto para hacerlo bien y un consejo profesional.",
    )
    nutricionista = Agent(
        client=client, name="NutricionistaBot",
        instructions="Dado un platillo, describe en 3-4 líneas: perfil nutricional, beneficios y a quién se lo recomendarías.",
    )
    historiador = Agent(
        client=client, name="HistoriadorBot",
        instructions="Dado un platillo, describe en 3-4 líneas: origen e historia, importancia cultural y una curiosidad interesante.",
    )

    # Los tres agentes se ejecutan en paralelo con el mismo input
    workflow = ConcurrentBuilder(
        participants=[chef, nutricionista, historiador],
    ).build()

    print("\n" + "=" * 60)
    print("⚡ CONCURRENT — Análisis paralelo de un platillo")
    print("=" * 60)

    result = await workflow.run("Analiza este platillo: Pozole rojo")
    for output in result.get_outputs():
        for msg in output.messages:
            print(f"\n[{msg.author_name}]:\n{msg.text}\n")
            print("-" * 60)

async def main():
    await demo_sequential()
    await demo_concurrent()

asyncio.run(main())
```

---

## ✅ Camino C — Datos reales (`05_datos_reales.py`)

**Conceptos:** lectura de CSV, escritura de JSON, API externa con fallback local, cruce de fuentes de datos

### Archivos de datos necesarios

**`data/alimentos.csv`:**
```csv
alimento,calorias_por_100g,proteinas_g,carbohidratos_g,grasas_g,categoria
pollo a la plancha,165,31,0,3.6,proteina
arroz blanco cocido,130,2.7,28,0.3,carbohidrato
aguacate,160,2,9,15,grasa saludable
huevo entero,155,13,1.1,11,proteina
tortilla de maiz,218,5.7,46,2.5,carbohidrato
frijoles negros cocidos,127,8.9,23,0.5,proteina vegetal
atun en agua,116,26,0,1,proteina
platano,89,1.1,23,0.3,carbohidrato
brocoli,34,2.8,7,0.4,verdura
salmon,208,20,0,13,proteina
quinoa cocida,120,4.4,22,1.9,carbohidrato
almendras,579,21,22,50,grasa saludable
espinaca,23,2.9,3.6,0.4,verdura
papa cocida,87,1.9,20,0.1,carbohidrato
leche entera,61,3.2,4.8,3.3,lacteo
```

**`data/progreso.json`:**
```json
{
  "usuario": "Francisco",
  "objetivo": "bajar peso",
  "registros": []
}
```

### Código principal

```python
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
                        f"Grasas: {row['grasas_g']}g"
                    )
            return "\n".join(resultados) if resultados else f"No encontré '{nombre}'."
    except FileNotFoundError:
        return "Error: no se encontró data/alimentos.csv"

@tool
def listar_alimentos_por_categoria(categoria: str) -> str:
    """Lista todos los alimentos de una categoría del CSV.
    Categorías: proteina, carbohidrato, grasa saludable, proteina vegetal, verdura, lacteo.
    """
    try:
        with open("data/alimentos.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            resultados = [
                f"  • {row['alimento']}: {row['calorias_por_100g']} kcal/100g"
                for row in reader if categoria.lower() in row["categoria"].lower()
            ]
            return f"Alimentos en '{categoria}':\n" + "\n".join(resultados) if resultados \
                   else f"No encontré alimentos en '{categoria}'."
    except FileNotFoundError:
        return "Error: no se encontró data/alimentos.csv"

@tool
def buscar_ejercicio_en_api(musculo: str) -> str:
    """Busca ejercicios para un músculo. Si la API no responde, usa datos locales."""
    try:
        req = urllib.request.Request(
            "https://api.wger.de/api/v2/exercise/?format=json&language=2&category=10&limit=4",
            headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
        ejercicios = data.get("results", [])
        if ejercicios:
            resultado = f"Ejercicios para '{musculo}':\n"
            for ej in ejercicios[:4]:
                resultado += f"  • {ej.get('name', ej.get('uuid', 'Sin nombre'))}\n"
            return resultado.strip()
    except Exception:
        pass

    fallback = {
        "pecho":   ["Press de banca", "Aperturas", "Fondos en paralelas"],
        "espalda": ["Dominadas", "Remo con barra", "Jalón al pecho"],
        "piernas": ["Sentadilla", "Prensa", "Peso muerto"],
        "hombros": ["Press militar", "Elevaciones laterales"],
        "brazos":  ["Curl con barra", "Extensión en polea"],
    }
    for key, ejercicios in fallback.items():
        if key in musculo.lower():
            return f"Ejercicios para {musculo}:\n" + "\n".join(f"  • {e}" for e in ejercicios)
    return f"No hay datos disponibles para '{musculo}'."

@tool
def registrar_comida(alimento: str, cantidad_gramos: int) -> str:
    """Registra una comida en el archivo de progreso con calorías calculadas del CSV."""
    try:
        with open("data/progreso.json", "r", encoding="utf-8") as f:
            progreso = json.load(f)

        calorias_total = None
        with open("data/alimentos.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if alimento.lower() in row["alimento"].lower():
                    calorias_total = round(
                        float(row["calorias_por_100g"]) * cantidad_gramos / 100, 1
                    )
                    break

        progreso["registros"].append({
            "fecha":    str(date.today()),
            "alimento": alimento,
            "gramos":   cantidad_gramos,
            "calorias": calorias_total or "desconocido",
        })

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

async def main():
    client = get_client()
    agent = Agent(
        client=client,
        name="NutriFitBot",
        instructions="""
        Eres NutriFitBot, asistente de nutrición y fitness con acceso a datos reales.
        Capacidades: consultar CSV de alimentos, buscar ejercicios por músculo,
        registrar comidas con calorías calculadas automáticamente, y mostrar resumen diario.
        Cuando el usuario mencione un alimento, búscalo en el CSV.
        Si dice que comió algo, ofrece registrarlo.
        """,
        tools=[buscar_alimento_en_csv, listar_alimentos_por_categoria,
               buscar_ejercicio_en_api, registrar_comida, ver_resumen_progreso],
    )
    session = agent.create_session()

    print("=" * 60)
    print("🥗💪 NutriFitBot — Datos Reales")
    print("=" * 60)

    inicio = await agent.run(
        "El usuario acaba de entrar. Salúdalo y explica qué puedes hacer.",
        session=session,
    )
    print(f"🤖 NutriFitBot: {inicio}\n")

    while True:
        user_input = input("👤 Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "salir":
            break
        respuesta = await agent.run(user_input, session=session)
        print(f"\n🤖 NutriFitBot: {respuesta}\n")

asyncio.run(main())
```

---

## 📊 Tabla resumen de patrones

| Patrón | Builder | Cuándo usarlo |
|---|---|---|
| Agente simple | `Agent()` | Una sola responsabilidad |
| Multi-turno | `Agent()` + `session` | Conversación con memoria |
| Handoff | `HandoffBuilder` | Enrutamiento dinámico entre especialistas |
| Sequential | `SequentialBuilder` | Pipeline donde cada agente enriquece al anterior |
| Concurrent | `ConcurrentBuilder` | Múltiples perspectivas independientes en paralelo |

## 📦 Estructura final del proyecto

Organizado por módulos progresivos para facilitar el aprendizaje y la navegación en el repositorio:

```
microsoft-agent-framework-learning/
├── README.md                              ← Portada del repositorio
├── .env.example                           ← Plantilla de variables de entorno
├── .gitignore
├── pyproject.toml                         ← Dependencias Python (uv)
├── uv.lock
│
├── docs/
│   └── MAF_Resumen_Aprendizaje.md        ← Este documento
│
├── 01-fundamentos/                        ← Conceptos base paso a paso
│   ├── README.md
│   ├── main_paso1_primer_agente.py        ← Agent + agent.run()
│   ├── main_paso2_herramientas.py         ← @tool + invocación paralela
│   └── main_paso3_sesiones.py             ← create_session() + memoria
│
├── 02-aplicaciones/                       ← Apps conversacionales completas
│   ├── README.md
│   ├── menu_planner.py                    ← MenuBot (flujo 9 pasos)
│   └── gym_assistant.py                   ← GymBot (flujo 12 pasos)
│
├── 03-multi-agente/                       ← Patrón Handoff
│   ├── README.md
│   └── bienestar_agent.py                 ← CoordinadorBot + 2 especialistas
│
├── 04-workflows/                          ← Sequential y Concurrent
│   ├── README.md
│   └── workflows.py                       ← Pipeline + análisis paralelo
│
└── 05-datos-reales/                       ← Integración con datos reales
    ├── README.md
    ├── nutrifit_bot.py                    ← CSV + JSON + API externa
    └── data/
        ├── alimentos.csv                  ← Base de datos nutricional
        └── progreso.json                  ← Registro persistente del usuario
```

### Ejecución de cada módulo

```bash
# Fundamentos
uv run 01-fundamentos/main_paso1_primer_agente.py
uv run 01-fundamentos/main_paso2_herramientas.py
uv run 01-fundamentos/main_paso3_sesiones.py

# Aplicaciones
uv run 02-aplicaciones/menu_planner.py
uv run 02-aplicaciones/gym_assistant.py

# Multi-agente
uv run 03-multi-agente/bienestar_agent.py

# Workflows
uv run 04-workflows/workflows.py

# Datos reales
uv run 05-datos-reales/nutrifit_bot.py
```