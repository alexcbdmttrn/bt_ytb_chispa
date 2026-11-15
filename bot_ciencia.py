# -*- coding: utf-8 -*-
"""
CIENCIA WEIRD - Bot v1.1
Canal de divulgación científica con estética "weird" (curiosidades del cuerpo y el universo).
Genera 1 video largo + 2 shorts diarios en una sola ejecución.

Basado en la arquitectura de Código Mental v3.0 (Sayayin Pro Max Elite).
"""
import asyncio
import bisect
import gc
import json
import os
import random
import re
import sys
import time
import traceback
import unicodedata
import ssl
import socket
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import edge_tts
import numpy as np
import requests
import urllib3
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from moviepy.editor import (
    AudioFileClip, CompositeAudioClip, VideoClip, VideoFileClip,
    concatenate_audioclips,
)
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

try:
    import json5
except ImportError:
    json5 = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =================================================================
# CONFIGURACIÓN
# =================================================================
TZ = ZoneInfo("America/Mexico_City")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL   = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
DEEPSEEK_URL     = "https://api.deepseek.com/v1/chat/completions"

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN  = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_MODEL      = "@cf/black-forest-labs/flux-1-schnell"

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

YOUTUBE_USER_TOKEN = json.loads(os.getenv("YOUTUBE_USER_TOKEN") or "{}")
PLAYLIST_ID        = os.getenv("YOUTUBE_PLAYLIST_ID", "")

CANAL_LINK    = "https://www.youtube.com/@cienciaweirdoficial"
FACEBOOK_LINK = os.getenv("FACEBOOK_LINK", "")

# ⚡ CORREGIDO: Nombres de archivos para coincidir con el repositorio
ESTADO_FILE  = "estado_musica.json"
TITULOS_FILE = "titulos_publicados.json"
TEMAS_FILE   = "temas_shorts.json"

CATEGORY_ID = "28"  # Ciencia y Tecnología

DURACION_MINIMA_SEGUNDOS = 480
DURACION_MAXIMA_SEGUNDOS = 720
NUM_PUNTOS               = 5
MAX_INTENTOS_EXPANSION   = 1

SHORT_CONTENT_MIN = 28
SHORT_CONTENT_MAX = 36

SEG_MAX_PALABRAS = 45
SEG_ESCENA       = 14.0
W, H, FPS        = 1920, 1080, 24
VOL_FONDO        = 0.10
USAR_IMAGENES_IA = os.getenv("USAR_IMAGENES_IA", "true").lower() == "true"
GENERAR_SHORT    = os.getenv("GENERAR_SHORT", "true").lower() == "true"
PROGRAMAR_PICO   = os.getenv("PROGRAMAR_PICO", "true").lower() == "true"

HORA_LARGO                = int(os.getenv("HORA_LARGO", "18"))
VARIACION_MINUTOS_LARGO   = int(os.getenv("VARIACION_MINUTOS_LARGO", "30"))
HORA_SHORT_1              = int(os.getenv("HORA_SHORT_1", "11"))
VARIACION_MINUTOS_SHORT_1 = int(os.getenv("VARIACION_MINUTOS_SHORT_1", "45"))
HORA_SHORT_2              = int(os.getenv("HORA_SHORT_2", "21"))
VARIACION_MINUTOS_SHORT_2 = int(os.getenv("VARIACION_MINUTOS_SHORT_2", "60"))
INTERVALO_MIN_HORAS       = float(os.getenv("INTERVALO_MIN_HORAS", "20"))
ACTIVAR_DISCLOSURE_IA     = True

DISCLOSURE_TEXT = (
    "\n\n⚠️ Este contenido es un documental científico elaborado con asistencia de "
    "Inteligencia Artificial para la narración y visualizaciones. La información "
    "está basada en fuentes científicas y tiene fines exclusivamente educativos."
)

VOZ_CANAL = {"voz": "es-MX-JorgeNeural", "tono": "-2Hz"}
VOCES_RESPALDO = ["es-MX-JorgeNeural", "es-US-AlonsoNeural", "es-ES-AlvaroNeural",
                  "es-CO-GonzaloNeural", "es-MX-DaliaNeural"]
RATE_ETAPA  = {"gancho": "+6%", "contexto": "+4%", "desarrollo": "+3%", "conclusion": "+1%"}
PAUSA_ETAPA = {"gancho": 0.4,   "contexto": 0.5,  "desarrollo": 0.45, "conclusion": 0.7}

FONDOS_DISPONIBLES = [
    "Binary Pulse.mp3", "Forward Momentum.mp3",
    "Peak Momentum.mp3", "The Ascent.mp3",
]
FUENTE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf"

CTA_SHORTS = [
    "El video completo con todas las revelaciones está en el canal. Suscríbete para verlo.",
    "Esto es solo una parte. La explicación científica completa te espera en el canal.",
    "Si esto te sorprendió, el video completo te va a volar la cabeza. Está en el canal.",
    "No te quedes con la duda. El análisis completo ya está disponible en el canal.",
]

OUTROS = [
    "Y hasta aquí llega el video de hoy. Si aprendiste algo nuevo, suscríbete y activa "
    "la campanita. Cuéntame en los comentarios: ¿cuál de estos datos te sorprendió más?",
    "Eso fue todo por hoy. Si llegaste hasta el final, déjame un like y suscríbete para "
    "no perderte el siguiente. ¿Tú ya sabías alguno de estos datos? Te leo abajo.",
]

# =================================================================
# TEMAS — CIENCIA WEIRD (20 TEMAS EN 4 SUB-NICHOS)
# =================================================================
TEMAS = [
    {"tema": "flema_sistema_inmune", "seed": "flema sistema inmune ciencia",
     "angulo": "Lo que la flema y los mocos realmente revelan sobre tu sistema inmune y por qué son tu primera línea de defensa.",
     "keywords": ["flema", "sistema inmune", "mucosidad", "defensas", "biologia"],
     "contextos": ["cuerpo humano", "microscopio", "laboratorio", "sistema inmune"],
     "hashtags": ["#SistemaInmune", "#Biologia", "#Ciencia"]},

    {"tema": "estornudo_peligro", "seed": "qué pasa si aguantas un estornudo",
     "angulo": "Por qué aguantarte un estornudo puede romperte un vaso sanguíneo, el tímpano o algo peor.",
     "keywords": ["estornudo", "presion", "cuerpo humano", "reflejo", "peligro"],
     "contextos": ["cuerpo humano", "anatomia abstracta", "laboratorio"],
     "hashtags": ["#Estornudo", "#CuerpoHumano", "#Ciencia"]},

    {"tema": "sudor_quimica", "seed": "por qué suda el cuerpo química",
     "angulo": "La química oculta del sudor: por qué tu cuerpo produce dos tipos distintos y qué revelan de tu estado emocional.",
     "keywords": ["sudor", "glándulas", "quimica", "cuerpo", "temperatura"],
     "contextos": ["cuerpo humano", "piel abstracta", "microscopio"],
     "hashtags": ["#Sudor", "#Biologia", "#Ciencia"]},

    {"tema": "bacterias_intestino", "seed": "bacterias intestino cerebro",
     "angulo": "Tienes más bacterias que células humanas: cómo tu intestino controla tu estado de ánimo y tus antojos.",
     "keywords": ["microbioma", "intestino", "bacterias", "cerebro", "digestion"],
     "contextos": ["intestino abstracto", "microscopio", "cerebro", "laboratorio"],
     "hashtags": ["#Microbioma", "#Intestino", "#Ciencia"]},

    {"tema": "lagrimas_tipos", "seed": "tipos de lágrimas ciencia",
     "angulo": "No todas las lágrimas son iguales: la ciencia descubrió que tu cuerpo produce 3 tipos distintos con funciones diferentes.",
     "keywords": ["lagrimas", "emociones", "ojos", "quimica", "cerebro"],
     "contextos": ["ojos abstractos", "microscopio", "cerebro"],
     "hashtags": ["#Lagrimas", "#Biologia", "#Ciencia"]},

    {"tema": "adn_neandertal", "seed": "adn neandertal humanos modernos",
     "angulo": "El 2% de tu ADN no es humano: los rasgos que heredaste de los neandertales y que aún hoy te afectan.",
     "keywords": ["adn", "neandertal", "genetica", "evolucion", "humanos"],
     "contextos": ["adn abstracto", "cadena de ADN", "evolucion humana abstracta"],
     "hashtags": ["#ADN", "#Genetica", "#Evolucion"]},

    {"tema": "vestigios_evolutivos", "seed": "vestigios evolutivos cuerpo humano",
     "angulo": "Las partes de tu cuerpo que ya no necesitas: los vestigios evolutivos que la evolución olvidó eliminar.",
     "keywords": ["vestigios", "evolucion", "cuerpo", "organos", "vestigial"],
     "contextos": ["cuerpo humano abstracto", "anatomia simplificada", "evolucion"],
     "hashtags": ["#Evolucion", "#CuerpoHumano", "#Ciencia"]},

    {"tema": "sentido_extra", "seed": "sexto sentido humano ciencia",
     "angulo": "El 'sexto sentido' que sí existe: la interocepcion, el sentido que tu cerebro usa para leer tu propio cuerpo.",
     "keywords": ["sexto sentido", "interocepcion", "cerebro", "sentidos", "percepcion"],
     "contextos": ["cerebro abstracto", "neuronas", "cuerpo simplificado"],
     "hashtags": ["#SextoSentido", "#Neurociencia", "#Ciencia"]},

    {"tema": "sangre_azul", "seed": "sangre azul personas raras",
     "angulo": "La condición genética que hace que tu sangre sea azul: por qué existe y quiénes la tienen.",
     "keywords": ["sangre", "genetica", "hemoglobina", "raro", "cuerpo"],
     "contextos": ["sangre abstracta", "microscopio", "adn abstracto"],
     "hashtags": ["#Genetica", "#Sangre", "#Ciencia"]},

    {"tema": "sin_huesos", "seed": "personas sin huesos condición rara",
     "angulo": "Las personas que nacen sin huesos: la rara condición que convierte el cuerpo en una máquina flexible.",
     "keywords": ["huesos", "genetica", "condicion rara", "cuerpo", "esqueleto"],
     "contextos": ["esqueleto abstracto", "cuerpo simplificado", "adn"],
     "hashtags": ["#Genetica", "#CuerpoHumano", "#Ciencia"]},

    {"tema": "casi_moriste", "seed": "veces que casi moriste sin darte cuenta",
     "angulo": "Las veces que casi moriste sin darte cuenta: los mecanismos de tu cuerpo que te salvan todos los días.",
     "keywords": ["supervivencia", "casi muerte", "cuerpo", "instinto", "peligro"],
     "contextos": ["cuerpo simplificado", "cerebro abstracto", "atmosfera oscura"],
     "hashtags": ["#Supervivencia", "#CuerpoHumano", "#Ciencia"]},

    {"tema": "cerebro_miente", "seed": "cerebro te miente ilusiones",
     "angulo": "Tu cerebro te miente 80 veces al día: las ilusiones perceptivas que te hacen ver cosas que no están ahí.",
     "keywords": ["cerebro", "ilusiones", "percepcion", "sesgos", "vision"],
     "contextos": ["cerebro abstracto", "neuronas", "patrones visuales"],
     "hashtags": ["#Cerebro", "#Neurociencia", "#Ciencia"]},

    {"tema": "veneno_cotidiano", "seed": "venenos cotidianos casa",
     "angulo": "Los venenos invisibles que tocas todos los días: sustancias comunes que tu cuerpo procesa sin que lo sepas.",
     "keywords": ["veneno", "quimica", "cotidiano", "toxinas", "cuerpo"],
     "contextos": ["laboratorio abstracto", "quimica", "casa simplificada"],
     "hashtags": ["#Quimica", "#Ciencia", "#Venenos"]},

    {"tema": "parasitos_cuerpo", "seed": "parásitos cuerpo humano ciencia",
     "angulo": "Los parásitos que viven en tu cuerpo sin que lo notes: el ecosistema oculto que llevas encima.",
     "keywords": ["parasitos", "microbios", "cuerpo", "biologia", "ecosistema"],
     "contextos": ["microscopio", "cuerpo abstracto", "laboratorio"],
     "hashtags": ["#Parasitos", "#Biologia", "#Ciencia"]},

    {"tema": "radiacion_cotidiana", "seed": "radiación cotidiana cuerpo",
     "angulo": "La radiación invisible que recibes todos los días: por qué tu cuerpo está diseñado para sobrevivirla.",
     "keywords": ["radiacion", "atomo", "cuerpo", "fisica", "energia"],
     "contextos": ["atomo abstracto", "radiacion", "laboratorio"],
     "hashtags": ["#Fisica", "#Radiacion", "#Ciencia"]},

    {"tema": "tierra_se_detiene", "seed": "qué pasaría si la tierra deja de girar",
     "angulo": "Qué pasaría si la Tierra dejara de girar mañana: los efectos en cadena sobre el clima, los océanos y tu cuerpo.",
     "keywords": ["tierra", "rotacion", "gravedad", "catastrofe", "fisica"],
     "contextos": ["planeta tierra abstracto", "espacio", "atmosfera"],
     "hashtags": ["#Tierra", "#Fisica", "#Ciencia"]},

    {"tema": "sol_se_apaga", "seed": "qué pasaría si el sol se apaga",
     "angulo": "Qué pasaría si el Sol se apagara por 24 horas: el efecto dominó que congelaría la Tierra en horas.",
     "keywords": ["sol", "energia", "tierra", "frio", "espacio"],
     "contextos": ["sol abstracto", "espacio profundo", "planeta congelado"],
     "hashtags": ["#Sol", "#Espacio", "#Ciencia"]},

    {"tema": "agujero_negro_sonido", "seed": "sonido agujero negro ciencia",
     "angulo": "El sonido que emite un agujero negro: por qué el universo tiene una 'banda sonora' que no deberías escuchar.",
     "keywords": ["agujero negro", "sonido", "universo", "espacio", "fisica"],
     "contextos": ["agujero negro abstracto", "espacio profundo", "ondas"],
     "hashtags": ["#AgujeroNegro", "#Espacio", "#Fisica"]},

    {"tema": "universo_infinito", "seed": "universo infinito o finito ciencia",
     "angulo": "¿El universo es infinito? Lo que la física moderna realmente sabe (y lo que no puede responder).",
     "keywords": ["universo", "infinito", "cosmologia", "espacio", "fisica"],
     "contextos": ["espacio profundo", "galaxias", "cosmos abstracto"],
     "hashtags": ["#Universo", "#Cosmologia", "#Ciencia"]},

    {"tema": "materia_oscura", "seed": "materia oscura que es ciencia",
     "angulo": "La materia oscura: el 27% del universo que no podemos ver y que sostiene toda la estructura cósmica.",
     "keywords": ["materia oscura", "universo", "galaxias", "fisica", "cosmologia"],
     "contextos": ["galaxias abstractas", "espacio profundo", "particulas"],
     "hashtags": ["#MateriaOscura", "#Universo", "#Fisica"]},
]

# =================================================================
# FORMATOS Y PERFILES
# =================================================================
FORMATOS_NARRACION = [
    {"nombre": "lista_explicativa_weird",
     "instruccion": ("Formato LISTA DE ASOMBRO CIENTÍFICO. El narrador presenta 5 'micro-revelaciones' "
                     "sobre el cuerpo/universo del espectador, cada una con un dato contraintuitivo, "
                     "un ejemplo cotidiano y una explicación científica breve. Tono: asombro documental, "
                     "NO consejo médico. Cada punto termina con un mini-cliffhanger que enlaza al siguiente.")},
    {"nombre": "que_pasaria_si",
     "instruccion": ("Formato ESCENARIO HIPOTÉTICO ('¿Qué pasaría si...?'). Desarrolla un escenario "
                     "imposible pero científicamente fundamentado. Estructura: 1) la premisa, "
                     "2) las consecuencias en cadena, 3) lo que la ciencia dice que pasaría. "
                     "NO des consejos de supervivencia, solo explica la física/biología.")},
    {"nombre": "mito_vs_ciencia",
     "instruccion": ("Formato MITO VS EVIDENCIA. Empieza con una creencia popular sobre el cuerpo o el universo "
                     "('Todos creen que...'). Luego revela lo que la ciencia realmente dice, con estudios "
                     "y mecanismos concretos. Cierra con una pregunta que invite a comentar.")},
    {"nombre": "anatomia_del_asombro",
     "instruccion": ("Formato ANATOMÍA DEL ASOMBRO. Explora un solo fenómeno (ej. la autofagia, "
                     "la gravedad cuántica, el microbioma) desde múltiples ángulos: qué es, "
                     "cómo funciona, por qué es más extraño de lo que parece. Estilo: documental "
                     "científico de alta gama, tipo BBC/Nat Geo.")},
    {"nombre": "experimento_mental",
     "instruccion": ("Formato EXPERIMENTO MENTAL. Plantea un escenario contraintuitivo y guía al "
                     "espectador paso a paso por lo que la ciencia predice. Uso intensivo de "
                     "'imagina que...' y 'esto significa que...'. El espectador debe salir "
                     "sintiendo que aprendió algo que no sabía que no sabía.")},
]

PERFILES_NARRADOR = [
    "divulgador científico con formación en biología",
    "astrofísico divulgador especializado en cosmología",
    "neurocientífico especializado en percepción",
    "microbiólogo con experiencia en divulgación",
    "físico teórico especializado en escenarios hipotéticos",
    "biólogo evolutivo especializado en comportamiento humano",
    "químico divulgador con enfoque en fenómenos cotidianos",
    "documentalista científico de estilo BBC",
]

# =================================================================
# UTILIDADES
# =================================================================
def cargar_json(ruta, default):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def guardar_json(ruta, data):
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ruta)

def cargar_estado():
    estado = cargar_json(ESTADO_FILE, {})
    estado.setdefault("ultimos_fondos", [])
    estado.setdefault("videos", [])
    estado.setdefault("temas_recientes", [])
    return estado

def parsear_json(texto):
    if not texto:
        raise ValueError("respuesta vacía")
    t = re.sub(r"```(?:json)?", " ", texto, flags=re.I)
    i, j = t.find("{"), t.rfind("}")
    if i == -1 or j == -1:
        raise ValueError("sin JSON")
    t = t[i:j + 1]
    t = re.sub(r",\s*([}\]])", r"\1", t)
    if json5:
        try:
            return json5.loads(t)
        except Exception:
            pass
    return json.loads(t, strict=False)

def llm(prompt, temperature=0.8, max_tokens=1500, json_mode=False, system=None, intentos=3):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    payload = {"model": DEEPSEEK_MODEL, "messages": msgs,
               "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    for i in range(intentos):
        try:
            r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=150)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"⚠️ LLM intento {i+1}/{intentos}: {e}")
            time.sleep(5 * (i + 1))
    return None

def descargar(url, ruta, max_bytes=20 * 1024 * 1024):
    try:
        with requests.get(url, stream=True, timeout=40) as r:
            r.raise_for_status()
            total = 0
            with open(ruta, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError("archivo demasiado grande")
                    f.write(chunk)
            return os.path.getsize(ruta) > 1000
    except Exception as e:
        print(f"⚠️ Descarga fallida: {e}")
        if os.path.exists(ruta):
            os.remove(ruta)
        return False

def fmt_ts(seg):
    seg = int(seg)
    h, m, s = seg // 3600, seg % 3600 // 60, seg % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

# =================================================================
# HISTORIAL
# =================================================================
def titulo_ya_publicado(titulo):
    data = cargar_json(TITULOS_FILE, {"titulos": []})
    n = titulo.lower().strip()
    p1 = set(re.findall(r"\w+", n))
    for t in data["titulos"]:
        tn = t.lower().strip()
        if n == tn:
            return True
        p2 = set(re.findall(r"\w+", tn))
        if len(p1) > 3 and len(p2) > 3 and len(p1 & p2) / min(len(p1), len(p2)) > 0.7:
            return True
    return False

def guardar_titulo(titulo):
    data = cargar_json(TITULOS_FILE, {"titulos": []})
    if titulo not in data["titulos"]:
        data["titulos"].append(titulo)
    data["titulos"] = data["titulos"][-100:]
    guardar_json(TITULOS_FILE, data)

def tema_ya_usado(tema, umbral=0.5):
    data = cargar_json(TEMAS_FILE, {"temas": []})
    nuevas = set(re.findall(r"\w+", str(tema).lower()))
    for antiguo in data["temas"][-20:]:
        if not isinstance(antiguo, str) or len(antiguo) > 80:
            continue
        viejas = set(re.findall(r"\w+", antiguo.lower()))
        union = nuevas | viejas
        if union and len(nuevas & viejas) / len(union) > umbral:
            return True
    return False

def guardar_tema(tema):
    data = cargar_json(TEMAS_FILE, {"temas": []})
    data["temas"] = [t for t in data["temas"] if isinstance(t, str) and len(t) < 80]
    if isinstance(tema, str) and len(tema) < 80 and tema not in data["temas"]:
        data["temas"].append(tema)
    data["temas"] = data["temas"][-20:]
    guardar_json(TEMAS_FILE, data)

# =================================================================
# YOUTUBE
# =================================================================
def crear_cliente_youtube():
    try:
        creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"⚠️ YouTube cliente: {e}")
        return None

def sugerencias_youtube(seed):
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search", timeout=10,
                         params={"client": "firefox", "ds": "yt", "hl": "es", "gl": "mx", "q": seed})
        return [s for s in r.json()[1] if isinstance(s, str)][:8]
    except Exception:
        return []

def puntuar_demanda(youtube, consulta):
    if youtube is None:
        return None
    try:
        desde = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
        q = f"ciencia {consulta}"
        r = youtube.search().list(part="id", q=q, type="video", order="viewCount",
                                  publishedAfter=desde, relevanceLanguage="es",
                                  regionCode="MX", maxResults=8).execute()
        ids = [i["id"]["videoId"] for i in r.get("items", [])]
        if not ids:
            return 0
        s = youtube.videos().list(part="statistics", id=", ".join(ids)).execute()
        vistas = [int(i["statistics"].get("viewCount", 0)) for i in s.get("items", [])]
        return sum(vistas) / len(vistas) if vistas else 0
    except Exception:
        return None

def actualizar_rendimiento(youtube, estado):
    ids = [v["id"] for v in estado["videos"][-30:] if v.get("id")]
    if not ids or youtube is None:
        return
    try:
        r = youtube.videos().list(part="statistics", id=", ".join(ids)).execute()
        vistas = {i["id"]: int(i["statistics"].get("viewCount", 0)) for i in r.get("items", [])}
        for v in estado["videos"]:
            if v.get("id") in vistas:
                v["vistas"] = vistas[v["id"]]
    except Exception:
        pass

def elegir_tema(estado, youtube):
    recientes = estado["temas_recientes"][-6:]
    pool = [t for t in TEMAS if t["tema"] not in recientes] or TEMAS[:]
    candidatos = random.sample(pool, min(5, len(pool)))
    acum = {}
    for v in estado["videos"]:
        if "vistas" in v:
            acum.setdefault(v["tema"], []).append(v["vistas"])
    rend = {k: sum(x) / len(x) for k, x in acum.items()}
    max_r = max(rend.values()) if rend else 1
    demandas = {t["tema"]: puntuar_demanda(youtube, t["seed"]) for t in candidatos}
    max_d = max([d for d in demandas.values() if d] or [1])

    def score(t):
        d = demandas[t["tema"]]
        sd = d / max_d if d else 0.4
        sr = rend[t["tema"]] / max_r if t["tema"] in rend and max_r else 0.6
        return 0.5 * sd + 0.5 * sr + random.uniform(0, 0.2)

    elegido = max(candidatos, key=score)
    print(f"🎯 Tema elegido: {elegido['tema']}")
    return elegido

# =================================================================
# TÍTULOS Y MINIATURAS (ESTRATEGIA WEIRD SCIENCE)
# =================================================================
GANCHOS = [
    "nunca", "nadie", "jamás", "prohibido", "secreto", "verdad",
    "ocultan", "te miente", "tu cuerpo", "tu cerebro", "tu adn",
    "lo que pasa", "qué pasaría", "por qué", "cómo", "si ",
    "cuando", "5 ", "7 ", "3 ", "?", "!",
    "lo que tu cuerpo", "lo que tu cerebro", "lo que nadie te dice",
    "el error de tu cuerpo", "la mentira de tu cerebro", "señales de que",
    "el dato que", "la ciencia revela", "lo que ocultan los estudios",
    "no deberías", "nunca hagas", "nadie sabe por qué",
]
PROHIBIDAS = [
    "testimonio real", "caso real", "100% real", "verídico", "comprobado",
    "garantizado", "secreto revelado", "hack", "truco", "trucos",
    "cura", "curar", "remedio", "milagro", "adelgaza", "engorda",
    "peligroso para tu salud", "mata", "muerte segura",
]
GENERICAS = ["ciencia", "datos curiosos", "sabias que", "curiosidades", "top 10", "lista de"]

def limpiar_titulo(t):
    t = t.strip().strip('"').strip("'")
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*[-|–]\s*ciencia.*$", "", t, flags=re.I)
    t = t.rstrip(".")
    palabras = t.split()
    caps = [w for w in palabras if len(re.sub(r"\W", " ", w)) >= 3 and w.isupper()]
    if len(caps) > 3:
        keep = set(caps[:2])
        palabras = [w if (not w.isupper() or w in keep or len(w) < 3) else w.capitalize()
                    for w in palabras]
    return " ".join(palabras)

def puntuar_titulo(t, dato_weird=""):
    s, n, tl = 0, len(t), t.lower()
    if 45 <= n <= 68:
        s += 4
    elif 30 <= n < 45 or 68 < n <= 80:
        s += 2
    elif n > 95 or n < 25:
        s -= 6
    if re.search(r"\d", t):
        s += 2
    s += min(3, sum(1 for g in GANCHOS if g in tl))

    if re.search(r'\bsi\b.{1,60}(nunca|no\s)', tl, re.I | re.S):
        s += 6
    if re.search(r'\b\d{1,2}\s+(señales|datos|claves|formas|maneras|razones|cosas)', tl):
        s += 4

    if re.search(r'\b(la trampa|el error|la mentira|tu cerebro|tu cuerpo|te miente|ocultan|lo que callan|nadie sabe|nunca hagas)\b', tl):
        s += 10

    if dato_weird:
        dc_words = set(re.findall(r"\w+", dato_weird.lower())) - {
            "de", "la", "el", "que", "y", "en", "un", "una", "por", "para", "con", "los", "las"}
        tit_words = set(re.findall(r"\w+", tl))
        if len(dc_words & tit_words) >= 2:
            s += 5

    if re.search(r'\b(menos|peor|nunca|deja de|evita|no hagas|no debes)\b', tl):
        s += 3

    caps = re.findall(r"\b[A-ZÁÉÍÓÚÑ]{4,}\b", t)
    s += 2 if 1 <= len(caps) <= 2 else (-3 if len(caps) > 3 else 0)
    if any(p in tl for p in PROHIBIDAS):
        s -= 8
    if any(tl.startswith(g) for g in GENERICAS):
        s -= 6
    if "!" in t:
        s -= 1
    return s

def elegir_titulo(candidatos, dato_weird=""):
    puntuados = []
    for c in candidatos:
        if not isinstance(c, str):
            continue
        base = limpiar_titulo(c)
        if len(base) < 25 or titulo_ya_publicado(base):
            continue
        puntuados.append((puntuar_titulo(base, dato_weird), base))
    if not puntuados:
        return None
    puntuados.sort(reverse=True)
    for sc, t in puntuados[:4]:
        print(f"   📝 [{sc:>2}] {t}")
    return puntuados[0][1][:100]

def elegir_texto_portada(opciones, titulo):
    pt = set(re.findall(r"\w+", titulo.lower()))
    mejor = None
    fallbacks_virales = ["TU CUERPO", "TU CEREBRO", "TE MIENTEN", "NUNCA HAGAS",
                         "EL ERROR", "OCULTAN", "¿QUÉ PASARÍA?"]
    for o in opciones or []:
        if not isinstance(o, str):
            continue
        o = re.sub(r"[^\w¿?¡! ]", "", o).strip().upper()
        w = o.split()
        if not 1 <= len(w) <= 4:
            continue
        solape = len({x.lower() for x in w} & pt) / len(w)
        sc = (3 if len(w) in (2, 3) else 1) - 2 * solape + (1 if "?" in o else 0)
        if any(x in o for x in ["CUERPO", "CEREBRO", "MIENTEN", "OCULTAN",
                                 "NUNCA", "ERROR", "ADN", "PASARÍA"]):
            sc += 5
        if mejor is None or sc > mejor[0]:
            mejor = (sc, o)
    if not mejor:
        return random.choice(fallbacks_virales)
    return mejor[1]

# =================================================================
# GENERACIÓN DE CONTENIDO
# =================================================================
ESQUEMA_PLAN = """{
 "titulos": ["6 títulos de 45-68 caracteres con ESTRUCTURA DISTINTA. NUNCA termines con '| Ciencia'. AL MENOS 3 DEBEN usar la fórmula 'Weird Science': 'Lo que TU [parte del cuerpo] hace cuando...', 'Por qué NUNCA debes [acción cotidiana]', 'El [dato] que la ciencia oculta sobre...', 'Tu [órgano] te está mintiendo...'. Combina con el dato_weird"],
 "tema_central": "descripción breve del tema",
 "dato_weird": "CRÍTICO: el dato más contraintuitivo, extraño o perturbador del video. Ej: 'tu cuerpo produce electricidad para encender un LED', 'tienes 39 billones de bacterias y solo 30 billones de células humanas', 'tu cerebro te miente 80 veces al día', 'el 2% de tu ADN es neandertal'. Debe aparecer en AL MENOS 3 de los 6 títulos",
 "gancho": "1-2 frases (máx 35 palabras) que abren el video con el dato_weird en segunda persona ('TU cuerpo...', 'TU cerebro...'). DEBE generar asombro inmediato, NO miedo",
 "resumen": "sinopsis de 2-3 oraciones sin spoilers",
 "palabras_clave": ["5 keywords SEO en español, la primera es el keyword principal del video"],
 "palabras_portada": ["3 opciones de 2-3 palabras EN MAYÚSCULAS (ej: TU CUERPO, NUNCA HAGAS, TE MIENTEN, EL ERROR, OCULTAN, TU CEREBRO)"],
 "miniatura_escena": "4-6 palabras en inglés para imagen abstracta científica (ej: glowing cells macro, abstract brain neurons, cosmic nebula dark, microscope bacteria)",
 "descripcion_gancho": "2 líneas: la primera con el keyword principal y una promesa concreta; la segunda invita a suscribirse",
 "titulo_short": "gancho de máx 55 caracteres para un YouTube Short",
 "pregunta_comentario": "pregunta corta que invite a comentar basada en el dato (ej: '¿tú ya sabías esto de tu cuerpo?')",
 "tags": ["10 tags ULTRA-ESPECÍFICOS: 2-3 del tema científico, 2-3 del mecanismo biológico/físico, 1-2 preguntas de audiencia, 1-2 'ciencia + elemento', 1-2 'datos curiosos + elemento'"],
 "puntos": [{"titulo": "2-4 palabras con intriga", "resumen": "qué se explica y qué micro-revelación deja"}]
}"""

def generar_plan(tema, contexto, sugerencias, titulos_previos, formato, perfil):
    prev = "\n".join(f"- {t}" for t in titulos_previos) or "Ninguno"
    sug  = "\n".join(f"- {s}" for s in sugerencias) or "Ninguna"

    prompt = f"""Eres showrunner de un canal de DIVULGACIÓN CIENTÍFICA "WEIRD" en español (México/Latam).
Diseña el PLAN de un video de ~9-11 minutos, con {NUM_PUNTOS} "micro-revelaciones" científicas.

TEMA: {tema['tema']} | ÁNGULO: {tema['angulo']}
CONTEXTO: {contexto}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATO OBLIGATORIO: {formato['nombre'].upper()}
{formato['instruccion']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERFIL DEL NARRADOR: {perfil}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BÚSQUEDAS REALES YOUTUBE: {sug}
TÍTULOS YA PUBLICADOS (no repetir): {prev}

━━━ REGLA CRÍTICA: TÍTULO "WEIRD SCIENCE" (CURIOSIDAD + ASOMBRO) ━━━
El canal viraliza con títulos que hacen que el espectador piense "no puedo creer que esto sea real". Fórmulas:
  • "Lo que TU [parte del cuerpo] hace cuando [acción cotidiana]"
  • "Por qué NUNCA debes [acción común] (la ciencia lo explica)"
  • "El [dato] que la ciencia oculta sobre [tema]"
  • "Tu [órgano] te está mintiendo: el error de [X]"
El campo 'titulos' debe contener 6 opciones. AL MENOS 3 deben usar esta estructura.

━━━ REGLA CRÍTICA: DATO WEIRD ━━━
El campo 'dato_weird' debe ser un hecho científico real pero tan extraño que parezca mentira.
DEBE ser verificable y aparecer en AL MENOS 3 de los 6 títulos.

━━━ REGLAS DE CONTENIDO ━━━
1. CADA punto debe aportar un DATO CIENTÍFICO CONCRETO (no relleno, no opinión).
2. Cada punto debe tener un mini-cliffhanger al final que conecte con el siguiente.
3. El gancho debe INCLUIR el dato_weird en segunda persona ("TU cuerpo...").
4. Tono: ASOMBRO DOCUMENTAL (estilo BBC / Nat Geo / Veritasium), NUNCA consejo médico.
5. NUNCA uses lenguaje de "debes hacer X para curar Y". Solo "la ciencia dice que...".
6. Los 5 puntos deben ser DIFERENTES entre sí pero conectar con el tema central.

Responde SOLO con este JSON:
{ESQUEMA_PLAN}"""
    txt = llm(prompt, temperature=0.9, max_tokens=2400, json_mode=True)
    plan = parsear_json(txt)
    if not (isinstance(plan.get("titulos"), list) and len(plan["titulos"]) >= 3
            and isinstance(plan.get("puntos"), list) and len(plan["puntos"]) >= NUM_PUNTOS
            and plan.get("gancho") and plan.get("palabras_portada")
            and plan.get("dato_weird")):
        raise ValueError("plan incompleto")
    return plan

def limpiar_texto_narracion(t):
    t = re.sub(r"[\U00010000-\U0010ffff]", " ", t)
    t = re.sub(r"(?im)^\s*(punto|cap[ií]tulo|parte)\s*\d+.\s*$", " ", t)
    t = re.sub(r"\[[^\]]*\]", " ", t)
    t = re.sub(r"[*_#>`~]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def generar_puntos(plan, tema, contexto):
    puntos = plan["puntos"][:NUM_PUNTOS]
    indice = "\n".join(f"{i+1}. {p.get('titulo','')}: {p.get('resumen','')}"
                       for i, p in enumerate(puntos))
    textos = []
    formato    = plan.get("_formato_instruccion", "Explicación directa.")
    perfil     = plan.get("_perfil_narrador", "divulgador científico")
    nombre_fmt = plan.get("_nombre_formato", "lista_explicativa_weird")
    dato_w     = plan.get("dato_weird", "un dato sorprendente")

    for i, punto in enumerate(puntos):
        previo = textos[-1][-600:] if textos else ""
        if i == 0:
            extra = (f"Empieza EXACTAMENTE con: \"{plan['gancho']}\" y enseguida "
                     f"INTEGRA el dato weird '{dato_w}' como la revelación central del video.")
        elif i == len(puntos) - 1:
            extra = ("Cierra con una síntesis que conecte los 5 puntos y deje al espectador "
                     f"con una sensación de asombro. Vuelve a mencionar el dato weird '{dato_w}' "
                     "para reforzarlo, pero con un ángulo nuevo.")
        else:
            extra = (f"Conecta con el punto anterior y menciona el dato weird '{dato_w}' "
                     f"si encaja. AL FINAL DE ESTE PUNTO, usa un OPEN LOOP: deja una frase "
                     f"intrigante que obligue a ver el siguiente punto.")

        prompt = f"""Escribe el PUNTO {i+1} de {len(puntos)} de un documental científico "weird".
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATO: {nombre_fmt.upper()}
{formato}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NARRADOR: {perfil}
TEMA: {tema['angulo']}
DATO WEIRD: "{dato_w}"
SINOPSIS: {plan.get('resumen', '')}
ÍNDICE COMPLETO: {indice}
ESTE PUNTO: {punto.get('titulo', '')} → {punto.get('resumen', '')}
{extra}
{('CIERRE DEL PUNTO ANTERIOR: ' + previo) if previo else ''}

REGLAS:
- 320-400 palabras exactas
- Español neutro-mexicano, tono de documental científico de alta gama
- Cada punto debe tener: UN DATO CIENTÍFICO CONCRETO + UN EJEMPLO COTIDIANO + UNA EXPLICACIÓN BREVE
- NUNCA des consejos médicos. NUNCA uses "debes hacer X". Solo "la ciencia dice que..."
- Estilo narrativo: asombro documental (BBC / Nat Geo / Veritasium)
- SHOWING not telling: describe escenas y mecanismos concretos
- El dato weird debe sentirse como una revelación, no forzado
- Sin listas, emojis, ni acotaciones
- Los 5 puntos deben ser DIFERENTES entre sí

Devuelve SOLO el texto del punto."""
        texto = None
        for intento in range(3):
            t = llm(prompt, temperature=0.85, max_tokens=1000)
            t = limpiar_texto_narracion(t) if t else ""
            if len(t.split()) >= 280:
                texto = t
                break
            print(f"⚠️ Punto {i+1} corto ({len(t.split())} pal.)")
        if not texto:
            raise RuntimeError(f"No se pudo generar el punto {i+1}")
        textos.append(texto)
        print(f"   ✅ Punto {i+1}/{len(puntos)}: {len(texto.split())} palabras")
    return textos

def expandir_texto(titulo, texto_actual):
    prompt = (f'Video: "{titulo}". Final:\n"""\n{texto_actual[-500:]}\n"""\n'
              f"Añade 200-300 palabras profundizando el cierre. Devuelve SOLO el texto.")
    for _ in range(2):
        t = llm(prompt, temperature=0.8, max_tokens=900)
        t = limpiar_texto_narracion(t) if t else ""
        if len(t.split()) > 150:
            return t
    return ""

# =================================================================
# SEGMENTOS
# =================================================================
def dividir_en_segmentos(texto, max_palabras=SEG_MAX_PALABRAS):
    oraciones = [o.strip() for o in re.split(r"(?<=[.!?…])\s+", texto) if o.strip()]
    if not oraciones:
        return [texto]
    segs, actual, cuenta = [], [], 0
    for o in oraciones:
        n = len(o.split())
        if cuenta + n > max_palabras and actual:
            segs.append(" ".join(actual))
            actual, cuenta = [o], n
        else:
            actual.append(o)
            cuenta += n
    if actual:
        segs.append(" ".join(actual))
    if len(segs) > 1 and len(segs[-1].split()) < 12:
        segs[-2] += " " + segs.pop()
    return segs

def crear_segmentos(puntos_txt):
    segs = []
    for pi, txt in enumerate(puntos_txt):
        for k, p in enumerate(dividir_en_segmentos(txt)):
            segs.append({"punto": pi, "texto": p, "punto_ini": k == 0})
    n = len(segs)
    for i, s in enumerate(segs):
        p = i / max(n - 1, 1)
        s["etapa"] = ("gancho" if p < 0.12 else
                      "contexto" if p < 0.30 else
                      "desarrollo" if p < 0.85 else "conclusion")
    return segs

# =================================================================
# VOZ
# =================================================================
def duracion_audio(ruta):
    a = AudioFileClip(ruta)
    d = a.duration
    a.close()
    return d

def generar_audio(texto, nombre, etapa):
    limpio = re.sub(r'[{}[\]"]', " ", texto)
    limpio = re.sub(r"\s+", " ", limpio).strip()
    if len(limpio) < 10:
        return None
    ruta = f"temp_audio_{nombre}.mp3"
    rate = RATE_ETAPA.get(etapa, "+4%")
    pitch = VOZ_CANAL["tono"]
    voces = [VOZ_CANAL["voz"]] + [v for v in VOCES_RESPALDO if v != VOZ_CANAL["voz"]]
    for voz in voces:
        for intento in range(2):
            async def _go():
                communicate = edge_tts.Communicate(limpio, voz, rate=rate, pitch=pitch)
                await communicate.save(ruta)
            try:
                asyncio.run(_go())
                if os.path.exists(ruta) and os.path.getsize(ruta) > 500:
                    return ruta
            except Exception as e:
                print(f"❌ TTS {voz}: {e}")
                time.sleep(2 * (intento + 1))
    return None

def sintetizar(segs):
    ok = []
    for i, s in enumerate(segs):
        ruta = generar_audio(s["texto"], s.get("id", i), s["etapa"])
        if not ruta:
            print(f"⚠️ Segmento {i} sin audio")
            continue
        s["audio"]     = ruta
        s["dur_audio"] = duracion_audio(ruta)
        ok.append(s)
        time.sleep(0.2)
    if len(ok) < len(segs) * 0.9:
        raise RuntimeError("Demasiados segmentos sin audio")
    return ok

def construir_timeline(segs):
    t = 0.0
    for s in segs:
        s["inicio"] = t
        s["dur"]    = s["dur_audio"] + PAUSA_ETAPA.get(s["etapa"], 0.5)
        t += s["dur"]
    return t

# =================================================================
# POOL DE IMÁGENES FLUX
# =================================================================
POOL_FLUX = []
POOL_FLUX_INDEX = 0
USADOS_PEXELS = set()

def registrar_imagen_flux(ruta):
    if ruta and os.path.exists(ruta) and ruta not in POOL_FLUX:
        POOL_FLUX.append(ruta)

def reutilizar_imagen_flux(idx):
    global POOL_FLUX_INDEX
    if not POOL_FLUX:
        return None
    original = POOL_FLUX[POOL_FLUX_INDEX % len(POOL_FLUX)]
    POOL_FLUX_INDEX += 1
    try:
        ruta = f"temp_img_{idx}_reused.jpg"
        with open(original, "rb") as src, open(ruta, "wb") as dst:
            dst.write(src.read())
        print(f"   ♻️ Reutilizando imagen Flux del pool ({len(POOL_FLUX)} disponibles)")
        return ruta
    except Exception as e:
        print(f"   ⚠️ Error reutilizando imagen: {e}")
        return None

# =================================================================
# CLOUDFLARE FLUX
# =================================================================
ANTI_DEFORM = (
    ", cinematic wide shot, abstract scientific visualization, "
    "glowing bioluminescent elements, minimalist dark aesthetic, highly detailed, 8k, "
    "professional science documentary style, no realistic human faces, no realistic human bodies, "
    "no deformed anatomy, no mutated hands, no extra limbs, no text, no words, clean and futuristic"
)

def generar_imagen_cloudflare(prompt_en, idx, intentos=3):
    if not USAR_IMAGENES_IA:
        return None
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        print("⚠️ Sin credenciales Cloudflare")
        return None
    prompt_completo = prompt_en.strip() + ANTI_DEFORM
    url = (f"https://api.cloudflare.com/client/v4/accounts/"
           f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}")
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    payload = {"prompt": prompt_completo}
    for i in range(intentos):
        print(f"   🎨 Cloudflare intento {i+1}/{intentos}")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 200:
                ruta = f"temp_img_{idx}.jpg"
                if r.headers.get("Content-Type", "").startswith("image"):
                    with open(ruta, "wb") as f:
                        f.write(r.content)
                else:
                    import base64
                    data = r.json()
                    if "result" in data and "image" in data["result"]:
                        with open(ruta, "wb") as f:
                            f.write(base64.b64decode(data["result"]["image"]))
                    else:
                        print(f"⚠️ Formato inesperado: {str(data)[:100]}")
                        continue
                if os.path.exists(ruta) and os.path.getsize(ruta) > 1000:
                    print(f"   ✅ Imagen Cloudflare generada")
                    registrar_imagen_flux(ruta)
                    return ruta
            else:
                print(f"   ⚠️ Cloudflare {r.status_code}: {r.text[:150]}")
        except Exception as e:
            print(f"   ❌ Error Cloudflare: {e}")
        time.sleep(3 * (i + 1))
    return None

# =================================================================
# PEXELS
# =================================================================
def pexels_get(url, params, intentos=3):
    for i in range(intentos):
        try:
            r = requests.get(url, headers={"Authorization": PEXELS_API_KEY},
                             params=params, timeout=25)
            if r.status_code == 200:
                time.sleep(0.5)
                return r.json()
            if r.status_code == 429:
                time.sleep(20 * (i + 1))
                continue
            print(f"⚠️ Pexels {r.status_code}")
        except Exception as e:
            print(f"⚠️ Pexels error: {e}")
            time.sleep(2)
    return None

def buscar_fotos_pexels(query, cantidad=1):
    for pagina in (random.randint(1, 2), 1):
        data = pexels_get(
            "https://api.pexels.com/v1/search",
            {"query": query, "orientation": "landscape", "size": "large",
             "per_page": 10, "page": pagina}
        )
        fotos = [f["src"]["large2x"] for f in (data or {}).get("photos", [])]
        random.shuffle(fotos)
        fotos = [u for u in fotos if u not in USADOS_PEXELS]
        if fotos:
            return fotos[:cantidad]
    return []

def imagen_fallback_pexels(prompt_en, idx):
    if not PEXELS_API_KEY:
        return None
    query = " ".join(prompt_en.split()[:4])
    urls = buscar_fotos_pexels(query, 1)
    if urls:
        ruta = f"temp_img_{idx}_pexels.jpg"
        if descargar(urls[0], ruta, 15 * 1024 * 1024):
            USADOS_PEXELS.add(urls[0])
            print(f"   🔄 Fallback Pexels OK: {query}")
            return ruta
    return None

# =================================================================
# GRADIENTE OSCURO (fallback nivel 4)
# =================================================================
def imagen_fallback(idx):
    img = Image.new("RGB", (W, H), (10, 15, 25))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        color = (int(10 + 30 * y / H), int(15 + 20 * y / H), int(25 + 40 * y / H))
        draw.line([(0, y), (W, y)], fill=color)
    ruta = f"temp_img_{idx}_gradient.jpg"
    img.save(ruta, "JPEG", quality=85)
    return ruta

# =================================================================
# PLANIFICACIÓN VISUAL POR IA
# =================================================================
def planificar_visuales(segs, tema):
    out = [None] * len(segs)
    for ini in range(0, len(segs), 15):
        lote = segs[ini:ini + 15]
        listado = "\n".join(f"{j+1}. {s['texto'][:230]}" for j, s in enumerate(lote))
        prompt = f"""Eres director de fotografía de un canal de DIVULGACIÓN CIENTÍFICA de élite
(estilo BBC / Nat Geo / Veritasium).

Para CADA fragmento numerado devuelve UNA consulta corta (4-6 palabras, EN INGLÉS)
para generar una imagen con Flux que ilustre visualmente ese fragmento.

REGLAS CRÍTICAS:
- Estilo: visualización científica abstracta, cinematográfica, oscura-elegante
- Prefiere: células brillantes, neuronas, ADN abstracto, nebulosas, partículas,
  microscopía artística, diagramas conceptuales
- EVITA TOTALMENTE: rostros humanos, cuerpos humanos realistas, anatomía detallada
- Ejemplos: "glowing neuron network dark", "abstract dna helix glowing",
  "microscopic bacteria bioluminescent", "cosmic nebula purple dark",
  "brain neurons firing abstract", "cell division macro glowing"
- NUNCA incluyas: "text", "words", "letters", "person", "face", "human"

Tema: {tema['tema']}
Fragmentos:\n{listado}

Responde SOLO JSON: {{"consultas": ["..."]}} con exactamente {len(lote)} elementos."""
        lista = []
        try:
            lista = parsear_json(llm(prompt, 0.4, 800, json_mode=True)).get("consultas", [])
        except Exception as e:
            print(f"⚠️ Planificación visual: {e}")
        for j, s in enumerate(lote):
            q = lista[j] if j < len(lista) and isinstance(lista[j], str) else ""
            q = " ".join(re.sub(r"[^a-zA-Z ]", " ", q).split()[:7])
            if len(q) < 10:
                q = "abstract scientific visualization glowing cells dark"
            out[ini + j] = q
    return out

# =================================================================
# RENDER
# =================================================================
_VIG = {}

def vignette(size, base=1.0, fuerza=0.55):
    k = (size, base, fuerza)
    if k not in _VIG:
        w, h = size
        y, x = np.ogrid[-1:1:h * 1j, -1:1:w * 1j]
        d = np.clip(np.sqrt(x ** 2 + y ** 2) / 1.414, 0, 1)
        _VIG[k] = ((1 - fuerza * d ** 2.2) * base).astype(np.float32)[..., None]
    return _VIG[k]

def grade(img, etapa):
    img = ImageEnhance.Color(img).enhance(0.92)
    img = ImageEnhance.Contrast(img).enhance({"gancho": 1.10, "conclusion": 1.05}.get(etapa, 1.08))
    img = ImageEnhance.Brightness(img).enhance({"gancho": 1.02, "conclusion": 1.02}.get(etapa, 1.02))
    return Image.blend(img, Image.new("RGB", img.size, (12, 18, 32)), 0.03)

class RenderEscenas:
    def __init__(self, escenas, size, total):
        self.esc, self.size, self.total = escenas, size, total
        self.starts = [e["inicio"] for e in escenas]
        self._ikey = self._img = None
        self.vig_img = vignette(size, 1.0, 0.30)

    def cerrar(self):
        pass

    def _base(self, e):
        key = (e["path"], e["etapa"])
        if self._ikey != key:
            sz = (int(self.size[0] * 1.2), int(self.size[1] * 1.2))
            im = ImageOps.fit(Image.open(e["path"]).convert("RGB"), sz, Image.LANCZOS)
            arr = np.asarray(grade(im, e["etapa"]), dtype=np.float32) * vignette(sz, 1.0, 0.30)
            self._img, self._ikey = Image.fromarray(arr.astype(np.uint8)), key
        return self._img

    def _frame_img(self, e, lt):
        base = self._base(e)
        bw, bh = base.size
        p = min(max(lt / e["dur"], 0), 1) if e["dur"] > 0 else 0
        if not e["zin"]:
            p = 1 - p
        cw = bw / (1 + 0.08 * p)
        ch = cw * bh / bw
        mx, my = bw - cw, bh - ch
        x0 = min(max(mx / 2 + e["ax"] * mx / 2 * 0.8, 0), mx)
        y0 = min(max(my / 2 + e["ay"] * my / 2 * 0.8, 0), my)
        return np.asarray(base.resize(self.size, Image.BILINEAR,
                                      box=(x0, y0, x0 + cw, y0 + ch)))

    def frame(self, t):
        i = max(0, bisect.bisect_right(self.starts, t) - 1)
        e = self.esc[i]
        lt = t - e["inicio"]
        fr = self._frame_img(e, lt)
        f = 1.0
        if e.get("fade") and lt < 0.6:
            f = lt / 0.6
        if t > self.total - 1.5:
            f = min(f, max(0.0, (self.total - t) / 1.5))
        if f < 1.0:
            fr = (fr.astype(np.float32) * f).astype(np.uint8)
        return fr

def construir_escenas(segs):
    esc = []
    for s in segs:
        n_imgs = max(1, round(s["dur_audio"] / SEG_ESCENA))
        dur_por_img = s["dur"] / n_imgs
        for k in range(n_imgs):
            esc.append({
                "path": s["medios"][k % len(s["medios"])],
                "inicio": s["inicio"] + k * dur_por_img,
                "dur": dur_por_img,
                "etapa": s["etapa"],
                "fade": bool(k == 0 and s.get("punto_ini")),
                "zin": random.random() < 0.65,
                "ax": random.uniform(-1, 1),
                "ay": random.uniform(-1, 1),
            })
    return esc

def mezclar_audio(segs, total, fondo, extras=()):
    clips = [AudioFileClip(s["audio"]).set_start(s["inicio"]) for s in segs]
    clips += list(extras)
    narr = CompositeAudioClip(clips)
    capas = [narr]
    if fondo and os.path.exists(fondo):
        try:
            bg = AudioFileClip(fondo)
            if bg.duration < total:
                bg = concatenate_audioclips([bg] * (int(total / bg.duration) + 1))
            capas.append(bg.subclip(0, total).volumex(VOL_FONDO).audio_fadein(2).audio_fadeout(3))
        except Exception as e:
            print(f"⚠️ Fondo: {e}")
    return CompositeAudioClip(capas).set_duration(total), clips

def renderizar(escenas, total, audio, size, salida, sufijo=""):
    render = RenderEscenas(escenas, size, total)
    video = VideoClip(render.frame, duration=total).set_audio(audio)
    temp_audio = f"temp_audio_final{sufijo}.m4a"
    video.write_videofile(salida, fps=FPS, codec="libx264", audio_codec="aac",
                          audio_bitrate="192k", threads=4, preset="veryfast",
                          temp_audiofile=temp_audio,
                          ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p",
                                         "-movflags", "+faststart"],
                          logger=None)
    render.cerrar()
    video.close()
    try:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
    except Exception:
        pass
    return salida

# =================================================================
# MINIATURA
# =================================================================
def obtener_fuente(size):
    os.makedirs("fonts", exist_ok=True)
    ruta = "fonts/Anton-Regular.ttf"
    if not os.path.exists(ruta):
        try:
            r = requests.get(FUENTE_URL, timeout=20)
            if r.status_code == 200 and len(r.content) > 20000:
                with open(ruta, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass
    for p in [ruta, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def dividir_lineas(palabras):
    if len(palabras) <= 2:
        return palabras[:]
    mejor = None
    for i in range(1, len(palabras)):
        a, b = " ".join(palabras[:i]), " ".join(palabras[i:])
        m = max(len(a), len(b))
        if mejor is None or m < mejor[0]:
            mejor = (m, [a, b])
    return mejor[1]

def crear_miniatura(img_path, texto, salida):
    TW, TH = 1280, 720
    try:
        img = Image.open(img_path).convert("RGB") if img_path else Image.new("RGB", (TW, TH), (10, 10, 20))
        img = ImageOps.fit(img, (TW, TH), Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.45)
        img = ImageEnhance.Color(img).enhance(1.35)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = ImageEnhance.Brightness(img).enhance(0.95)

        grad = Image.new("L", (TW, TH), 0)
        gd = ImageDraw.Draw(grad)
        for x in range(TW):
            gd.line([(x, 0), (x, TH)], fill=int(240 * max(0, 1 - x / (TW * 0.65)) ** 1.6))
        img = Image.composite(Image.new("RGB", (TW, TH), (0, 0, 0)), img, grad)
        arr = np.asarray(img, dtype=np.float32) * vignette((TW, TH), 1.0, 0.40)
        img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

        lineas = dividir_lineas(texto.upper().split()[:4])
        max_w, max_h = int(TW * 0.58), int(TH * 0.78)

        for size in range(150, 60, -6):
            font = obtener_fuente(size)
            cajas = [font.getbbox(l) for l in lineas]
            alto = sum(b[3] - b[1] for b in cajas) + 18 * (len(lineas) - 1)
            if max(b[2] - b[0] for b in cajas) <= max_w and alto <= max_h:
                break

        acento = random.choice([(255, 220, 0), (255, 50, 50), (255, 140, 0), (255, 255, 255)])
        y = (TH - alto) // 2 + 10
        pos = []
        for l, b in zip(lineas, cajas):
            pos.append((l, 60, y - b[1]))
            y += (b[3] - b[1]) + 18

        glow = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        for l, x, yy in pos:
            gdraw.text((x, yy), l, font=font, fill=acento + (255,),
                       stroke_width=10, stroke_fill=acento + (255,))
        img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(24)))

        draw = ImageDraw.Draw(img)
        borde = max(7, size // 20)
        for i, (l, x, yy) in enumerate(pos):
            color = acento if (i == len(pos) - 1) else (255, 255, 255)
            draw.text((x, yy), l, font=font, fill=color + (255,),
                      stroke_width=borde, stroke_fill=(0, 0, 0, 255))

        rgb = img.convert("RGB")
        for q in (92, 87, 82, 76, 70):
            rgb.save(salida, "JPEG", quality=q, optimize=True)
            if os.path.getsize(salida) < 1_900_000:
                break
        print(f"✅ Miniatura: '{' / '.join(lineas)}' ({size}px)")
        return True
    except Exception as e:
        print(f"❌ Error miniatura: {e}")
        return False

# =================================================================
# SEO ELITE
# =================================================================
def _ascii_tag_yt(t):
    nfd = unicodedata.normalize('NFD', str(t))
    sin_acentos = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    limpio = re.sub(r'[^a-z0-9 ]', '', sin_acentos.lower())
    return re.sub(r'\s+', ' ', limpio).strip()

def construir_tags(plan, tema, sugerencias):
    nombre_tema = _ascii_tag_yt(tema["tema"].replace("_", " "))

    tags_ia = plan.get("tags", [])
    if isinstance(tags_ia, str):
        tags_ia = [x.strip() for x in tags_ia.split(",")]

    exactos = list(tags_ia)[:5]
    broad = ["ciencia", "divulgacion cientifica", "datos curiosos",
             "curiosidades cientificas", "asombro cientifico"]
    long_tail = [
        f"ciencia {nombre_tema}",
        f"que pasa si {nombre_tema}",
        f"por que {nombre_tema}",
        f"ciencia de {nombre_tema}",
    ]
    preguntas = list(sugerencias)[:3]
    especificos_tema = list(tema["keywords"])[:3]

    todos, vistos = [], set()
    for raw in exactos + broad + long_tail + preguntas + especificos_tema:
        tag = _ascii_tag_yt(raw)
        if not tag or len(tag) < 2 or len(tag) > 40 or tag in vistos:
            continue
        if any(x in tag for x in ("100 real", "veridico", "caso real", "cura", "remedio")):
            continue
        vistos.add(tag)
        todos.append(tag)

    resultado, total_chars = [], 0
    for tag in todos:
        costo = len(tag) + 1
        if total_chars + costo > 460 or len(resultado) >= 20:
            break
        resultado.append(tag)
        total_chars += costo
    print(f"🏷️  Tags ({len(resultado)}): {', '.join(resultado[:6])}...")
    return resultado

def construir_hashtags(tema, plan):
    base = ["#Ciencia", "#DivulgacionCientifica"]
    tema_hs = tema.get("hashtags", [])[:2]
    extra = "#DatosCuriosos"
    hs = base + tema_hs + [extra]
    vistos = []
    for h in hs:
        if h not in vistos:
            vistos.append(h)
    return " ".join(vistos[:5])

def construir_descripcion(plan, tema, caps_ts, sugerencias, hashtags):
    kws = plan.get("palabras_clave", [])
    keyword_principal = kws[0] if kws else tema["tema"].replace("_", " ")
    dato_w = plan.get("dato_weird", "")
    resumen = plan.get("resumen", "")

    linea1 = f"{keyword_principal.title()}: {dato_w}." if dato_w else f"{keyword_principal.title()}: {resumen[:120]}"
    linea2 = f"En este video te explico {plan.get('gancho', '')[:180]}"

    capitulos = "\n".join(f"{ts} {t}" for ts, t in caps_ts)
    rel = ", ".join(sugerencias[:5])

    partes = [
        f"🎯 {linea1}",
        linea2,
        f"",
        f"🔔 SUSCRÍBETE para un video nuevo cada día: {CANAL_LINK}?sub_confirmation=1",
        f"",
        f"⏰ CAPÍTULOS\n{capitulos}",
        f"",
        f"📖 SOBRE ESTE VIDEO\n{resumen}",
        f"",
        (f"🔎 BÚSQUEDAS RELACIONADAS: {rel}" if rel else ""),
        f"",
    ]

    if FACEBOOK_LINK:
        partes.append(f"📱 Sígueme en Facebook: {FACEBOOK_LINK}")
        partes.append(f"")

    partes += [
        f"📚 Otros videos que te pueden interesar:",
        f"• Curiosidades de tu cuerpo → {CANAL_LINK}/videos",
        f"• ¿Qué pasaría si...? → {CANAL_LINK}/videos",
    ]

    if ACTIVAR_DISCLOSURE_IA:
        partes.append(DISCLOSURE_TEXT.strip())

    partes.append("")
    partes.append(hashtags)

    desc = "\n".join(p for p in partes if p is not None)
    return desc[:4900]

def generar_srt(segs, ruta):
    def ts(x):
        h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"
    lineas, n = [], 1
    for s in segs:
        pal = s["texto"].split()
        if not pal:
            continue
        t = s["inicio"]
        for i in range(0, len(pal), 9):
            tr = pal[i:i + 9]
            d = s["dur_audio"] * len(tr) / len(pal)
            lineas.append(f"{n}\n{ts(t)} --> {ts(t + d)}\n{' '.join(tr)}\n")
            n, t = n + 1, t + d
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    return ruta

# =================================================================
# PUBLICACIÓN
# =================================================================
def deberia_publicar(estado):
    ult = estado.get("ultima_publicacion")
    if not ult:
        return True
    try:
        dt = datetime.fromisoformat(ult)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        horas = (datetime.now(TZ) - dt).total_seconds() / 3600
        if horas < INTERVALO_MIN_HORAS:
            print(f"⏸️ Han pasado {horas:.1f}h (mínimo {INTERVALO_MIN_HORAS}h).")
            return False
    except ValueError:
        pass
    return True

def proximo_slot_batch():
    ahora = datetime.now(TZ)
    slot_mas_temprano_hoy = (
        ahora.replace(hour=HORA_LARGO, minute=0, second=0, microsecond=0)
        - timedelta(minutes=VARIACION_MINUTOS_LARGO)
    )
    if slot_mas_temprano_hoy - ahora < timedelta(minutes=10):
        dia_base = (ahora + timedelta(days=1)).date()
    else:
        dia_base = ahora.date()

    dia_dt = datetime.combine(dia_base, datetime.min.time()).replace(tzinfo=TZ)

    def slot(hora, variacion, offset=0):
        s = dia_dt.replace(hour=hora, minute=0)
        s += timedelta(minutes=random.randint(-variacion, variacion) + offset)
        return s

    slot_largo  = slot(HORA_LARGO, VARIACION_MINUTOS_LARGO)
    slot_short1 = slot(HORA_SHORT_1, VARIACION_MINUTOS_SHORT_1, offset=15)
    slot_short2 = slot(HORA_SHORT_2, VARIACION_MINUTOS_SHORT_2, offset=15)
    return slot_largo, slot_short1, slot_short2

def utc_iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def subir_video(youtube, ruta, titulo, descripcion, tags, publish_at=None):
    status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": True}
    if publish_at:
        status.update({"privacyStatus": "private", "publishAt": publish_at})
    body = {"snippet": {"title": titulo[:100], "description": descripcion[:5000],
                        "tags": tags, "categoryId": CATEGORY_ID,
                        "defaultLanguage": "es", "defaultAudioLanguage": "es"},
            "status": status}
    media = MediaFileUpload(ruta, chunksize=8 * 1024 * 1024, resumable=True,
                            mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp, reintentos = None, 0
    while resp is None:
        try:
            st, resp = req.next_chunk()
            if st:
                print(f"   ⬆️ {int(st.progress() * 100)}%")
        except (HttpError, ssl.SSLEOFError, ConnectionError, socket.timeout, OSError) as e:
            es_reintento = (isinstance(e, HttpError) and e.resp.status in (429, 500, 502, 503, 504))
            es_reintento = es_reintento or isinstance(e, (ssl.SSLEOFError, ConnectionError, socket.timeout, OSError))
            if es_reintento and reintentos < 8:
                reintentos += 1
                espera = 2 ** reintentos
                print(f"⚠️ Reintento {reintentos}/8 en {espera}s...")
                time.sleep(espera)
                continue
            print(f"❌ Error fatal subida: {type(e).__name__}: {e}")
            raise
    print(f"✅ Video subido: https://youtu.be/{resp['id']}" +
          (f" (programado {publish_at})" if publish_at else ""))
    return resp["id"]

def extras_post_subida(youtube, vid, miniatura, srt, comentario):
    if miniatura and os.path.exists(miniatura):
        try:
            youtube.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(miniatura, mimetype="image/jpeg")
            ).execute()
            print("✅ Miniatura subida")
        except Exception as e:
            print(f"⚠️ Miniatura: {e}")
    if srt and os.path.exists(srt):
        try:
            youtube.captions().insert(
                part="snippet",
                body={"snippet": {"videoId": vid, "language": "es",
                                  "name": "Español", "isDraft": False}},
                media_body=MediaFileUpload(srt, mimetype="application/octet-stream")
            ).execute()
            print("✅ Subtítulos subidos")
        except Exception as e:
            print(f"⚠️ Subtítulos: {e}")
    if PLAYLIST_ID:
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={"snippet": {"playlistId": PLAYLIST_ID,
                                  "resourceId": {"kind": "youtube#video", "videoId": vid}}}
            ).execute()
            print("✅ Añadido a playlist")
        except Exception as e:
            print(f"⚠️ Playlist: {e}")
    if comentario:
        try:
            youtube.commentThreads().insert(
                part="snippet",
                body={"snippet": {"videoId": vid,
                                  "topLevelComment": {"snippet": {"textOriginal": comentario}}}}
            ).execute()
            print("✅ Comentario publicado")
        except Exception as e:
            print(f"⚠️ Comentario: {e}\n   Para fijar: {comentario}")

# =================================================================
# SHORTS
# =================================================================
def generar_short_scripts(plan, tema):
    puntos_lista = "\n".join(
        f"- {p.get('titulo','')}: {p.get('resumen','')}"
        for p in plan.get("puntos", [])
    )
    prompt = f"""Basándote en este video largo de divulgación científica, escribe 2 GUIONES
para 2 Shorts de YouTube DIFERENTES entre sí. Cada short debe ser un RESUMEN
PARAFRASEADO del video (NO copiar frases literales), cada uno enfocándose en un ÁNGULO DIFERENTE.

VIDEO LARGO:
- Tema: {plan.get('titulo_short', '')[:80]}
- Dato weird: {plan.get('dato_weird', '')}
- Sinopsis: {plan.get('resumen', '')[:250]}
- Puntos clave:
{puntos_lista}

━━━ SHORT 1 (ángulo: PROBLEMA/ADVERTENCIA) ━━━
- Título: máx 55 chars, contiene el dato weird o una advertencia.
- Guion: 80-100 palabras. EMPIEZA CON UN PATTERN INTERRUPT (ej: "Si haces esto, tu cuerpo reacciona así", "El 90% no sabe esto").
- Hashtags: 4-5 hashtags específicos del short.

━━━ SHORT 2 (ángulo: SOLUCIÓN/PARADOJA) ━━━
- Título: DIFERENTE al short 1, máx 55 chars, contiene una PARADOJA o REVELACIÓN.
- Guion: 80-100 palabras. Empieza con la paradoja, cierra con la revelación científica.
- Hashtags: 4-5 hashtags DISTINTOS o parcialmente distintos al short 1.

━━━ REGLAS CRÍTICAS ━━━
1. Los 2 shorts NO deben ser el mismo contenido reformulado.
2. Los 2 títulos deben ser claramente DIFERENTES en estructura y palabras.
3. El guion NO debe incluir CTA de "suscríbete" — el bot lo agrega después.
4. Los hashtags del short 1 y short 2 deben tener al menos 2 diferentes entre sí.
5. NUNCA uses "debes hacer X para curar Y". Solo "la ciencia dice que...".

Responde SOLO JSON:
{{
 "short1": {{
   "titulo": "...",
   "guion": "...",
   "hashtags": "#tag1 #tag2 #tag3 #tag4"
 }},
 "short2": {{
   "titulo": "...",
   "guion": "...",
   "hashtags": "#tag1 #tag2 #tag3 #tag4"
 }}
}}"""
    try:
        txt = llm(prompt, temperature=0.95, max_tokens=1500, json_mode=True)
        data = parsear_json(txt)
        if not (data.get("short1") and data.get("short2")):
            raise ValueError("faltan shorts en respuesta")
        for k in ("short1", "short2"):
            s = data[k]
            if not all(f in s for f in ("titulo", "guion", "hashtags")):
                raise ValueError(f"{k} incompleto")
            if len(s["guion"].split()) < 50:
                raise ValueError(f"{k} guion muy corto ({len(s['guion'].split())} palabras)")
        t1 = data["short1"]["titulo"].lower().strip()
        t2 = data["short2"]["titulo"].lower().strip()
        if t1 == t2:
            raise ValueError("títulos iguales entre shorts")
        print(f"   ✅ Short 1: \"{data['short1']['titulo']}\"")
        print(f"   ✅ Short 2: \"{data['short2']['titulo']}\"")
        return data
    except Exception as e:
        print(f"⚠️ Generación de shorts falló: {e}")
        return None

def crear_short_con_guion(guion_texto, titulo_short, hashtags_short, fondo, indice, salida):
    print(f"   📱 Short {indice} guion: {len(guion_texto.split())} palabras")

    textos = dividir_en_segmentos(guion_texto)
    if not textos:
        return None, 0
    segs = []
    for i, txt in enumerate(textos):
        etapa = "gancho" if i == 0 else ("conclusion" if i == len(textos) - 1 else "desarrollo")
        segs.append({"texto": txt, "etapa": etapa, "id": f"sh{indice}_{i}"})
    segs = sintetizar(segs)
    if not segs:
        print(f"   ❌ Short {indice}: sin audio")
        return None, 0
    total = construir_timeline(segs)
    print(f"   🔊 Short {indice} audio: {total:.1f}s")

    for i, s in enumerate(segs):
        n_imgs = max(1, round(s["dur_audio"] / SEG_ESCENA))
        medios = []
        for k in range(n_imgs):
            img_id = f"sh{indice}_{i}_{k}"
            ruta = reutilizar_imagen_flux(img_id)
            if not ruta:
                ruta = generar_imagen_cloudflare(
                    "cinematic dark science abstract visualization", img_id
                )
            if not ruta:
                ruta = imagen_fallback_pexels(
                    "cinematic dark science abstract", img_id
                )
            if not ruta:
                ruta = imagen_fallback(img_id)
            medios.append(ruta)
        s["medios"] = medios

    fallback_count = 0
    total_imgs = 0
    for s in segs:
        for m in s["medios"]:
            total_imgs += 1
            if "gradient" in m or "fallback" in m:
                fallback_count += 1
    if total_imgs > 0:
        pct = fallback_count / total_imgs
        print(f"   🔍 Short {indice}: {fallback_count}/{total_imgs} gradientes ({pct*100:.0f}%)")
        if pct > 0.4:
            print(f"   ❌ Short {indice} demasiados gradientes. SKIP.")
            return None, 0

    cta_texto = random.choice(CTA_SHORTS)
    cta = generar_audio(cta_texto, f"cta_{indice}", "conclusion")
    escenas = construir_escenas(segs)
    extras, total_final = [], total
    if cta:
        d = duracion_audio(cta)
        extras.append(AudioFileClip(cta).set_start(total))
        ult = escenas[-1]
        escenas.append({**ult, "inicio": total, "dur": d + 0.6, "fade": False})
        total_final = total + d + 0.6
    audio, _ = mezclar_audio(segs, total_final, fondo, extras)
    print(f"   📊 Short {indice} total: {total_final:.1f}s")
    renderizar(escenas, total_final, audio, (1080, 1920), salida, sufijo=f"_s{indice}")
    return salida, total_final

# =================================================================
# MÚSICA
# =================================================================
def buscar_archivo(nombre):
    for root, _, files in os.walk("."):
        if "/." in root or "\\." in root:
            continue
        if nombre in files:
            return os.path.join(root, nombre)
    return None

def seleccionar_fondo(estado):
    ultimos = estado["ultimos_fondos"]
    disp = [f for f in FONDOS_DISPONIBLES if f not in ultimos[-3:]] or FONDOS_DISPONIBLES[:]
    random.shuffle(disp)
    for f in disp + FONDOS_DISPONIBLES:
        ruta = buscar_archivo(f)
        if ruta:
            estado["ultimos_fondos"] = (ultimos + [f])[-10:]
            print(f"🎵 Fondo: {ruta}")
            return ruta
    print("⚠️ Sin música de fondo")
    return None

# =================================================================
# VALIDACIONES
# =================================================================
def limpiar_temporales():
    for f in os.listdir("."):
        if f.startswith("temp_") or f in ("video_final.mp4", "short_1.mp4",
                                          "short_2.mp4", "short_final.mp4",
                                          "miniatura.jpg", "subtitulos.srt"):
            try:
                os.remove(f)
            except OSError:
                pass

def verificar_envs():
    faltan = [v for v in ("DEEPSEEK_API_KEY", "CLOUDFLARE_ACCOUNT_ID",
                          "CLOUDFLARE_API_TOKEN", "YOUTUBE_USER_TOKEN")
              if not os.getenv(v)]
    if faltan:
        print(f"❌ Faltan variables: {', '.join(faltan)}")
        sys.exit(1)

    if not PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY no configurada — sin fallback Pexels")
    else:
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search?query=test&per_page=1",
                headers={"Authorization": PEXELS_API_KEY}, timeout=10
            )
            if r.status_code == 200:
                print("✅ Pexels OK (fallback nivel 3)")
            else:
                print(f"⚠️ Pexels respondió {r.status_code} — fallback deshabilitado")
        except Exception as e:
            print(f"⚠️ Pexels no responde: {e}")

    yt = crear_cliente_youtube()
    if yt is None:
        print("❌ YOUTUBE_USER_TOKEN inválido/expirado")
        sys.exit(1)
    try:
        yt.channels().list(part="id", mine=True).execute()
        print("✅ Credenciales válidas.")
    except HttpError as e:
        err_str = str(e)
        if "insufficientPermissions" in err_str:
            print("⚠️ Token sin permiso de lectura. El bot publica igual.")
        elif "401" in err_str or "invalid_grant" in err_str:
            print(f"❌ YouTube token expirado: {e}")
            sys.exit(1)
        else:
            print(f"❌ Error YouTube: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ YouTube token inválido: {e}")
        sys.exit(1)
    return yt

# =================================================================
# MAIN
# =================================================================
def main():
    youtube = verificar_envs()
    limpiar_temporales()
    estado = cargar_estado()

    if os.getenv("FORCE_PUBLISH") == "true":
        print("⚡ FORCE_PUBLISH activo")
    elif not deberia_publicar(estado):
        sys.exit(0)

    print("=" * 70)
    print("🧬 CIENCIA WEIRD - BOT v1.1")
    print(f"📅 {datetime.now(TZ):%Y-%m-%d %H:%M} | 🎤 {VOZ_CANAL['voz']}")
    print(f"📤 1 Video Largo (8-12 min) + 2 Shorts ÚNICOS (35-42s) | 🎨 Flux SEG_ESCENA={SEG_ESCENA}s")
    print(f"🛡️  Fallback: Cloudflare → Pool Flux → Pexels → Gradiente")
    print(f"📂 Categoría YouTube: Ciencia y Tecnología (28)")
    print("=" * 70)

    actualizar_rendimiento(youtube, estado)
    tema = elegir_tema(estado, youtube)
    contexto = random.choice(tema["contextos"])
    formato = random.choice(FORMATOS_NARRACION)
    perfil = random.choice(PERFILES_NARRADOR)
    print(f"🎭 Formato: {formato['nombre']} | Narrador: {perfil}")

    sugerencias = list(dict.fromkeys(
        sugerencias_youtube(tema["seed"]) +
        sugerencias_youtube("ciencia " + tema["keywords"][0])
    ))[:10]

    fondo = seleccionar_fondo(estado)
    titulos_previos = cargar_json(TITULOS_FILE, {"titulos": []})["titulos"][-20:]

    plan = titulo = None
    for intento in range(4):
        try:
            plan = generar_plan(tema, contexto, sugerencias, titulos_previos, formato, perfil)
            if plan.get("palabras_clave") and tema_ya_usado(" ".join(map(str, plan["palabras_clave"]))):
                raise ValueError("tema repetido")
            titulo = elegir_titulo(plan["titulos"], plan.get("dato_weird", ""))
            if not titulo:
                raise ValueError("sin título válido")
            plan["_formato_instruccion"] = formato["instruccion"]
            plan["_perfil_narrador"]     = perfil
            plan["_nombre_formato"]      = formato["nombre"]
            break
        except Exception as e:
            print(f"⚠️ Plan intento {intento+1}/4: {e}")
            plan = None
            time.sleep(5)
    if not plan:
        print("❌ No se pudo generar plan válido.")
        sys.exit(1)

    print(f"📌 Título: {titulo}")
    print(f"🎯 Dato weird: {plan.get('dato_weird', 'N/A')}")

    puntos_txt = generar_puntos(plan, tema, contexto)
    n_puntos = len(puntos_txt)
    segs = crear_segmentos(puntos_txt)
    print(f"🧩 {len(segs)} segmentos, {sum(len(p.split()) for p in puntos_txt)} palabras")

    segs = sintetizar(segs)
    total = construir_timeline(segs)

    intentos = 0
    while total < DURACION_MINIMA_SEGUNDOS and intentos < MAX_INTENTOS_EXPANSION:
        print(f"⚠️ {total/60:.1f} min < mínimo. Expandiendo ({intentos+1})...")
        extra = expandir_texto(titulo, " ".join(s["texto"] for s in segs))
        intentos += 1
        if not extra:
            break
        nuevos = [{"punto": n_puntos - 1, "texto": p, "punto_ini": False,
                   "etapa": "conclusion", "id": f"x{intentos}_{k}", "expansion": True}
                  for k, p in enumerate(dividir_en_segmentos(extra))]
        segs += sintetizar(nuevos)
        total = construir_timeline(segs)

    if total > DURACION_MAXIMA_SEGUNDOS:
        print(f"⚠️ {total/60:.1f} min > máximo. Recortando...")
        while total > DURACION_MAXIMA_SEGUNDOS:
            idx = next((i for i in range(len(segs) - 1, -1, -1) if segs[i].get("expansion")), None)
            if idx is None:
                break
            segs.pop(idx)
            total = construir_timeline(segs)

    if total < DURACION_MINIMA_SEGUNDOS:
        print("❌ Duración insuficiente. Abortando.")
        sys.exit(1)

    outro = [{"punto": n_puntos - 1, "texto": random.choice(OUTROS), "punto_ini": False,
              "etapa": "conclusion", "id": "outro", "outro": True}]
    segs += sintetizar(outro)
    total = construir_timeline(segs)
    print(f"⏱️ Duración final: {total/60:.1f} min")

    print("🎨 Planificando visuales con IA...")
    prompts_visuales = planificar_visuales(segs, tema)

    stats = {"flux": 0, "pool": 0, "pexels": 0, "gradient": 0}
    for i, s in enumerate(segs):
        n_imgs = max(1, round(s["dur_audio"] / SEG_ESCENA))
        prompt_visual = prompts_visuales[i] if i < len(prompts_visuales) else "abstract scientific visualization glowing cells dark"
        print(f"🖼️ {i+1}/{len(segs)} [{s['etapa']}] '{prompt_visual}' x{n_imgs}")
        medios = []
        for k in range(n_imgs):
            img_id = f"{i}_{k}"
            ruta = generar_imagen_cloudflare(prompt_visual, img_id)
            if ruta:
                stats["flux"] += 1
            else:
                ruta = reutilizar_imagen_flux(img_id)
                if ruta:
                    stats["pool"] += 1
                else:
                    ruta = imagen_fallback_pexels(prompt_visual, img_id)
                    if ruta:
                        stats["pexels"] += 1
                    else:
                        print(f"   ⚠️ Cloudflare+Pool+Pexels fallaron, usando gradiente")
                        ruta = imagen_fallback(img_id)
                        stats["gradient"] += 1
            medios.append(ruta)
        s["medios"] = medios

    print("=" * 70)
    print(f"📊 RESUMEN IMÁGENES:")
    print(f"   🎨 Cloudflare Flux: {stats['flux']}")
    print(f"   ♻️  Pool reciclado:  {stats['pool']}")
    print(f"   🔄 Pexels:          {stats['pexels']}")
    print(f"   ⚠️  Gradientes:      {stats['gradient']}")
    print("=" * 70)

    caps_ts = []
    for p in range(n_puntos):
        primero = next((s for s in segs if s["punto"] == p), None)
        nombre = (str(plan["puntos"][p].get("titulo", f"Punto {p+1}"))[:50]
                  if p < len(plan["puntos"]) else f"Punto {p+1}")
        if primero:
            caps_ts.append((fmt_ts(primero["inicio"]), nombre))
    if caps_ts:
        caps_ts[0] = ("00:00", caps_ts[0][1])

    hashtags = construir_hashtags(tema, plan)
    descripcion = construir_descripcion(plan, tema, caps_ts, sugerencias, hashtags)
    tags = construir_tags(plan, tema, sugerencias)
    srt = generar_srt(segs, "subtitulos.srt")

    print(f"📝 Descripción (primeras 2 líneas):")
    print("   " + "\n   ".join(descripcion.split("\n")[:2]))

    portada = elegir_texto_portada(plan.get("palabras_portada"), titulo)
    escena_mini = str(plan.get("miniatura_escena", "abstract science cinematic dark"))
    base_mini = generar_imagen_cloudflare(escena_mini + " for thumbnail", "thumb")
    if not base_mini:
        base_mini = reutilizar_imagen_flux("thumb_mini")
    if not base_mini:
        base_mini = imagen_fallback_pexels(escena_mini, "thumb_mini")
    if not base_mini:
        base_mini = imagen_fallback("thumb_mini")
    miniatura = "miniatura.jpg" if crear_miniatura(base_mini, portada, "miniatura.jpg") else None

    escenas = construir_escenas(segs)
    audio, _ = mezclar_audio(segs, total, fondo)
    print("🎬 Renderizando video largo...")
    renderizar(escenas, total, audio, (W, H), "video_final.mp4", sufijo="_largo")

    if PROGRAMAR_PICO:
        slot_largo, slot_short1, slot_short2 = proximo_slot_batch()
        print(f"🕖 Video Largo: {slot_largo:%Y-%m-%d %H:%M} CDMX")
        print(f"📱 Short 1:    {slot_short1:%Y-%m-%d %H:%M} CDMX")
        print(f"📱 Short 2:    {slot_short2:%Y-%m-%d %H:%M} CDMX")
    else:
        slot_largo = slot_short1 = slot_short2 = None
        print("📤 Publicación inmediata")

    vid = subir_video(youtube, "video_final.mp4", titulo, descripcion, tags,
                      utc_iso(slot_largo) if slot_largo else None)
    comentario = str(plan.get("pregunta_comentario") or "¿Qué opinas? Te leo 👇")
    extras_post_subida(youtube, vid, miniatura, srt, comentario)

    if GENERAR_SHORT:
        print("📝 Generando 2 guiones ÚNICOS para shorts...")
        shorts_plan = generar_short_scripts(plan, tema)

        if not shorts_plan:
            print("⚠️ No se pudieron generar guiones de shorts. Saltando shorts.")
        else:
            short1_data = shorts_plan["short1"]
            short2_data = shorts_plan["short2"]
            shorts_creados = []

            try:
                print("🎞️ Creando Short 1...")
                s1, dur1 = crear_short_con_guion(
                    short1_data["guion"], short1_data["titulo"], short1_data["hashtags"],
                    fondo, 1, "short_1.mp4"
                )
                if s1 is None:
                    print("   ⏭️ Short 1 fue SKIPeado. No se sube.")
                else:
                    print(f"   ✅ Short 1 renderizado: {os.path.getsize(s1) // 1024} KB")
                    t_short1 = short1_data["titulo"][:88] + " #Shorts"
                    d_short1 = (
                        f"{short1_data['titulo']}\n\n"
                        f"📺 Video completo 👉 https://youtu.be/{vid}\n\n"
                        f"🔔 Suscríbete: {CANAL_LINK}?sub_confirmation=1\n\n"
                        f"#Shorts {short1_data['hashtags']}" +
                        (DISCLOSURE_TEXT if ACTIVAR_DISCLOSURE_IA else "")
                    )
                    vid_s1 = subir_video(
                        youtube, "short_1.mp4", t_short1, d_short1,
                        tags[:15] + ["shorts"],
                        utc_iso(slot_short1) if slot_short1 else None
                    )
                    if vid_s1:
                        print(f"✅ Short 1 subido: https://youtu.be/{vid_s1}")
                        shorts_creados.append(("Short 1", vid_s1))
            except Exception as e:
                print(f"❌ Short 1 FALLÓ: {type(e).__name__}: {e}")
                traceback.print_exc()

            gc.collect()
            time.sleep(3)

            try:
                print("🎞️ Creando Short 2...")
                s2, dur2 = crear_short_con_guion(
                    short2_data["guion"], short2_data["titulo"], short2_data["hashtags"],
                    fondo, 2, "short_2.mp4"
                )
                if s2 is None:
                    print("   ⏭️ Short 2 fue SKIPeado. No se sube.")
                else:
                    print(f"   ✅ Short 2 renderizado: {os.path.getsize(s2) // 1024} KB")
                    t_short2 = short2_data["titulo"][:88] + " #Shorts"
                    d_short2 = (
                        f"{short2_data['titulo']}\n\n"
                        f"📺 Video completo 👉 https://youtu.be/{vid}\n\n"
                        f"🔔 Suscríbete: {CANAL_LINK}?sub_confirmation=1\n\n"
                        f"#Shorts {short2_data['hashtags']}" +
                        (DISCLOSURE_TEXT if ACTIVAR_DISCLOSURE_IA else "")
                    )
                    vid_s2 = subir_video(
                        youtube, "short_2.mp4", t_short2, d_short2,
                        tags[:15] + ["shorts"],
                        utc_iso(slot_short2) if slot_short2 else None
                    )
                    if vid_s2:
                        print(f"✅ Short 2 subido: https://youtu.be/{vid_s2}")
                        shorts_creados.append(("Short 2", vid_s2))
            except Exception as e:
                print(f"❌ Short 2 FALLÓ: {type(e).__name__}: {e}")
                traceback.print_exc()

            print("=" * 70)
            print(f"📊 RESUMEN SHORTS: {len(shorts_creados)}/2 creados")
            for nombre, sid in shorts_creados:
                print(f"   ✅ {nombre}: https://youtu.be/{sid}")
            print("=" * 70)

    ahora = datetime.now(TZ).isoformat()
    guardar_titulo(titulo)
    guardar_tema(tema["tema"])
    estado["videos"].append({
        "id": vid, "titulo": titulo, "tema": tema["tema"],
        "formato": formato["nombre"], "perfil": perfil,
        "dato_weird": plan.get("dato_weird"),
        "duracion_min": round(total / 60, 1),
        "fecha": ahora,
    })
    estado["videos"] = estado["videos"][-60:]
    estado["temas_recientes"] = (estado["temas_recientes"] + [tema["tema"]])[-6:]
    estado["ultima_publicacion"] = ahora
    guardar_json(ESTADO_FILE, estado)

    limpiar_temporales()
    print("🎉 Proceso completado: 1 video largo + 2 shorts únicos programados.")

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        traceback.print_exc()
        sys.exit(1)
