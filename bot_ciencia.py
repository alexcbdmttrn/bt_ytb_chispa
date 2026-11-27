# -*- coding: utf-8 -*-
import asyncio, bisect, json, os, random, re, sys, time, traceback, unicodedata, ssl, socket
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import edge_tts, numpy as np, requests, urllib3
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from moviepy.editor import AudioFileClip, CompositeAudioClip, VideoClip, VideoFileClip, concatenate_audioclips
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
try: import json5
except ImportError: json5 = None
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= CONFIGURACIÓN =================
TZ = ZoneInfo("America/Mexico_City")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_MODEL = "@cf/black-forest-labs/flux-1-schnell"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_USER_TOKEN = json.loads(os.getenv("YOUTUBE_USER_TOKEN") or "{}")
PLAYLIST_ID = os.getenv("YOUTUBE_PLAYLIST_ID", "")
CANAL_LINK = "https://www.youtube.com/@cienciaweirdoficial"
FACEBOOK_LINK = os.getenv("FACEBOOK_LINK", "")
ESTADO_FILE = "estado_musica.json"
TITULOS_FILE = "titulos_publicados.json"
TEMAS_FILE = "temas_shorts.json"
CATEGORY_ID = "28"
DURACION_MINIMA_SEGUNDOS = 480
DURACION_MAXIMA_SEGUNDOS = 720
NUM_PUNTOS = 5
MAX_INTENTOS_EXPANSION = 1
SEG_MAX_PALABRAS = 45
SEG_ESCENA = 18.0
W, H, FPS = 1920, 1080, 24
VOL_FONDO = 0.10
USAR_IMAGENES_IA = os.getenv("USAR_IMAGENES_IA", "true").lower() == "true"
GENERAR_SHORT = os.getenv("GENERAR_SHORT", "true").lower() == "true"
PROGRAMAR_PICO = os.getenv("PROGRAMAR_PICO", "true").lower() == "true"
HORA_LARGO = int(os.getenv("HORA_LARGO", "18"))
VARIACION_MINUTOS_LARGO = int(os.getenv("VARIACION_MINUTOS_LARGO", "30"))
HORA_SHORT_1 = int(os.getenv("HORA_SHORT_1", "11"))
VARIACION_MINUTOS_SHORT_1 = int(os.getenv("VARIACION_MINUTOS_SHORT_1", "45"))
HORA_SHORT_2 = int(os.getenv("HORA_SHORT_2", "21"))
VARIACION_MINUTOS_SHORT_2 = int(os.getenv("VARIACION_MINUTOS_SHORT_2", "60"))
INTERVALO_MIN_HORAS = float(os.getenv("INTERVALO_MIN_HORAS", "48"))
ACTIVAR_DISCLOSURE_IA = True
OUTLIERS_FILE = "outliers_cache.json"
OUTLIER_MAX_SUBS = int(os.getenv("OUTLIER_MAX_SUBS", "50000"))
OUTLIER_MIN_RATIO = float(os.getenv("OUTLIER_MIN_RATIO", "3.5"))
OUTLIER_CACHE_HORAS = int(os.getenv("OUTLIER_CACHE_HORAS", "24"))

IDENTIDAD_VISUAL = {"estilos_rotacion": ["miedo_rojo", "advertencia_amarillo", "misterio_blanco", "shock_cyan", "secreto_naranja"]}
DISCLOSURE_TEXT = "\n\n⚠️ Este contenido es un documental científico elaborado con asistencia de Inteligencia Artificial para la narración y visualizaciones. La información está basada en fuentes científicas y tiene fines exclusivamente educativos."

VOCES_ROTACION = [
    {"voz": "es-MX-JorgeNeural", "estilo": "narrativo_masculino"}, {"voz": "es-MX-DaliaNeural", "estilo": "narrativo_femenino"},
    {"voz": "es-ES-AlvaroNeural", "estilo": "dramatico_es"}, {"voz": "es-MX-ManuelNeural", "estilo": "conversacional"},
    {"voz": "es-CO-GonzaloNeural", "estilo": "suspenso_colombiano"}, {"voz": "es-US-AlonsoNeural", "estilo": "rapido_neutro"},
    {"voz": "es-AR-TomasNeural", "estilo": "argentino_intenso"}, {"voz": "es-MX-DaliaNeural", "estilo": "susurro_femenino"},
    {"voz": "es-ES-ElviraNeural", "estilo": "femenino_es"}, {"voz": "es-CL-LorenzoNeural", "estilo": "chileno_narrador"}
]
VOZ_CANAL = {"voz": "es-MX-JorgeNeural", "tono": "-2Hz", "rate": "+5%"}
VOCES_RESPALDO = ["es-MX-JorgeNeural", "es-US-AlonsoNeural", "es-ES-AlvaroNeural", "es-CO-GonzaloNeural", "es-MX-DaliaNeural"]
RATE_ETAPA = {"gancho": "+6%", "contexto": "+4%", "desarrollo": "+3%", "conclusion": "+1%"}
PAUSA_ETAPA = {"gancho": 0.4, "contexto": 0.5, "desarrollo": 0.45, "conclusion": 0.7}
FONDOS_DISPONIBLES = ["Binary Pulse.mp3", "Forward Momentum.mp3", "Peak Momentum.mp3", "The Ascent.mp3"]

# ================= TEMAS (20) =================
TEMAS = [
    {"tema": "flema_sistema_inmune", "seed": "flema sistema inmune ciencia", "angulo": "Lo que la flema y los mocos realmente revelan sobre tu sistema inmune y por qué son tu primera línea de defensa.", "keywords": ["flema", "sistema inmune", "mucosidad", "defensas", "biologia"], "contextos": ["cuerpo humano", "microscopio", "laboratorio", "sistema inmune"], "hashtags": ["#SistemaInmune", "#Biologia", "#Ciencia"]},
    {"tema": "estornudo_peligro", "seed": "qué pasa si aguantas un estornudo", "angulo": "Por qué aguantarte un estornudo puede romperte un vaso sanguíneo, el tímpano o algo peor.", "keywords": ["estornudo", "presion", "cuerpo humano", "reflejo", "peligro"], "contextos": ["cuerpo humano", "anatomia abstracta", "laboratorio"], "hashtags": ["#Estornudo", "#CuerpoHumano", "#Ciencia"]},
    {"tema": "sudor_quimica", "seed": "por qué suda el cuerpo química", "angulo": "La química oculta del sudor: por qué tu cuerpo produce dos tipos distintos y qué revelan de tu estado emocional.", "keywords": ["sudor", "glándulas", "quimica", "cuerpo", "temperatura"], "contextos": ["cuerpo humano", "piel abstracta", "microscopio"], "hashtags": ["#Sudor", "#Biologia", "#Ciencia"]},
    {"tema": "bacterias_intestino", "seed": "bacterias intestino cerebro", "angulo": "Tienes más bacterias que células humanas: cómo tu intestino controla tu estado de ánimo y tus antojos.", "keywords": ["microbioma", "intestino", "bacterias", "cerebro", "digestion"], "contextos": ["intestino abstracto", "microscopio", "cerebro", "laboratorio"], "hashtags": ["#Microbioma", "#Intestino", "#Ciencia"]},
    {"tema": "lagrimas_tipos", "seed": "tipos de lágrimas ciencia", "angulo": "No todas las lágrimas son iguales: la ciencia descubrió que tu cuerpo produce 3 tipos distintos con funciones diferentes.", "keywords": ["lagrimas", "emociones", "ojos", "quimica", "cerebro"], "contextos": ["ojos abstractos", "microscopio", "cerebro"], "hashtags": ["#Lagrimas", "#Biologia", "#Ciencia"]},
    {"tema": "adn_neandertal", "seed": "adn neandertal humanos modernos", "angulo": "El 2% de tu ADN no es humano: los rasgos que heredaste de los neandertales y que aún hoy te afectan.", "keywords": ["adn", "neandertal", "genetica", "evolucion", "humanos"], "contextos": ["adn abstracto", "cadena de ADN", "evolucion humana abstracta"], "hashtags": ["#ADN", "#Genetica", "#Evolucion"]},
    {"tema": "vestigios_evolutivos", "seed": "vestigios evolutivos cuerpo humano", "angulo": "Las partes de tu cuerpo que ya no necesitas: los vestigios evolutivos que la evolución olvidó eliminar.", "keywords": ["vestigios", "evolucion", "cuerpo", "organos", "vestigial"], "contextos": ["cuerpo humano abstracto", "anatomia simplificada", "evolucion"], "hashtags": ["#Evolucion", "#CuerpoHumano", "#Ciencia"]},
    {"tema": "sentido_extra", "seed": "sexto sentido humano ciencia", "angulo": "El 'sexto sentido' que sí existe: la interocepcion, el sentido que tu cerebro usa para leer tu propio cuerpo.", "keywords": ["sexto sentido", "interocepcion", "cerebro", "sentidos", "percepcion"], "contextos": ["cerebro abstracto", "neuronas", "cuerpo simplificado"], "hashtags": ["#SextoSentido", "#Neurociencia", "#Ciencia"]},
    {"tema": "sangre_azul", "seed": "sangre azul personas raras", "angulo": "La condición genética que hace que tu sangre sea azul: por qué existe y quiénes la tienen.", "keywords": ["sangre", "genetica", "hemoglobina", "raro", "cuerpo"], "contextos": ["sangre abstracta", "microscopio", "adn abstracto"], "hashtags": ["#Genetica", "#Sangre", "#Ciencia"]},
    {"tema": "sin_huesos", "seed": "personas sin huesos condición rara", "angulo": "Las personas que nacen sin huesos: la rara condición que convierte el cuerpo en una máquina flexible.", "keywords": ["huesos", "genetica", "condicion rara", "cuerpo", "esqueleto"], "contextos": ["esqueleto abstracto", "cuerpo simplificado", "adn"], "hashtags": ["#Genetica", "#CuerpoHumano", "#Ciencia"]},
    {"tema": "casi_moriste", "seed": "veces que casi moriste sin darte cuenta", "angulo": "Las veces que casi moriste sin darte cuenta: los mecanismos de tu cuerpo que te salvan todos los días.", "keywords": ["supervivencia", "casi muerte", "cuerpo", "instinto", "peligro"], "contextos": ["cuerpo simplificado", "cerebro abstracto", "atmosfera oscura"], "hashtags": ["#Supervivencia", "#CuerpoHumano", "#Ciencia"]},
    {"tema": "cerebro_miente", "seed": "cerebro te miente ilusiones", "angulo": "Tu cerebro te miente 80 veces al día: las ilusiones perceptivas que te hacen ver cosas que no están ahí.", "keywords": ["cerebro", "ilusiones", "percepcion", "sesgos", "vision"], "contextos": ["cerebro abstracto", "neuronas", "patrones visuales"], "hashtags": ["#Cerebro", "#Neurociencia", "#Ciencia"]},
    {"tema": "veneno_cotidiano", "seed": "venenos cotidianos casa", "angulo": "Los venenos invisibles que tocas todos los días: sustancias comunes que tu cuerpo procesa sin que lo sepas.", "keywords": ["veneno", "quimica", "cotidiano", "toxinas", "cuerpo"], "contextos": ["laboratorio abstracto", "quimica", "casa simplificada"], "hashtags": ["#Quimica", "#Ciencia", "#Venenos"]},
    {"tema": "parasitos_cuerpo", "seed": "parásitos cuerpo humano ciencia", "angulo": "Los parásitos que viven en tu cuerpo sin que lo notes: el ecosistema oculto que llevas encima.", "keywords": ["parasitos", "microbios", "cuerpo", "biologia", "ecosistema"], "contextos": ["microscopio", "cuerpo abstracto", "laboratorio"], "hashtags": ["#Parasitos", "#Biologia", "#Ciencia"]},
    {"tema": "radiacion_cotidiana", "seed": "radiación cotidiana cuerpo", "angulo": "La radiación invisible que recibes todos los días: por qué tu cuerpo está diseñado para sobrevivirla.", "keywords": ["radiacion", "atomo", "cuerpo", "fisica", "energia"], "contextos": ["atomo abstracto", "radiacion", "laboratorio"], "hashtags": ["#Fisica", "#Radiacion", "#Ciencia"]},
    {"tema": "tierra_se_detiene", "seed": "qué pasaría si la tierra deja de girar", "angulo": "Qué pasaría si la Tierra dejara de girar mañana: los efectos en cadena sobre el clima, los océanos y tu cuerpo.", "keywords": ["tierra", "rotacion", "gravedad", "catastrofe", "fisica"], "contextos": ["planeta tierra abstracto", "espacio", "atmosfera"], "hashtags": ["#Tierra", "#Fisica", "#Ciencia"]},
    {"tema": "sol_se_apaga", "seed": "qué pasaría si el sol se apaga", "angulo": "Qué pasaría si el Sol se apagara por 24 horas: el efecto dominó que congelaría la Tierra en horas.", "keywords": ["sol", "energia", "tierra", "frio", "espacio"], "contextos": ["sol abstracto", "espacio profundo", "planeta congelado"], "hashtags": ["#Sol", "#Espacio", "#Ciencia"]},
    {"tema": "agujero_negro_sonido", "seed": "sonido agujero negro ciencia", "angulo": "El sonido que emite un agujero negro: por qué el universo tiene una 'banda sonora' que no deberías escuchar.", "keywords": ["agujero negro", "sonido", "universo", "espacio", "fisica"], "contextos": ["agujero negro abstracto", "espacio profundo", "ondas"], "hashtags": ["#AgujeroNegro", "#Espacio", "#Fisica"]},
    {"tema": "universo_infinito", "seed": "universo infinito o finito ciencia", "angulo": "¿El universo es infinito? Lo que la física moderna realmente sabe (y lo que no puede responder).", "keywords": ["universo", "infinito", "cosmologia", "espacio", "fisica"], "contextos": ["espacio profundo", "galaxias", "cosmos abstracto"], "hashtags": ["#Universo", "#Cosmologia", "#Ciencia"]},
    {"tema": "materia_oscura", "seed": "materia oscura que es ciencia", "angulo": "La materia oscura: el 27% del universo que no podemos ver y que sostiene toda la estructura cósmica.", "keywords": ["materia oscura", "universo", "galaxias", "fisica", "cosmologia"], "contextos": ["galaxias abstractas", "espacio profundo", "particulas"], "hashtags": ["#MateriaOscura", "#Universo", "#Fisica"]},
]

FORMATOS_NARRACION = [
    {"nombre": "lista_explicativa_weird", "instruccion": "Formato LISTA DE ASOMBRO CIENTÍFICO. Presenta 5 micro-revelaciones con un dato contraintuitivo, un ejemplo cotidiano y una explicación breve."},
    {"nombre": "que_pasaria_si", "instruccion": "Formato ESCENARIO HIPOTÉTICO ('¿Qué pasaría si...?'). Desarrolla un escenario imposible pero científicamente fundamentado. Estructura: 1) premisa, 2) consecuencias, 3) lo que dice la ciencia."},
    {"nombre": "mito_vs_ciencia", "instruccion": "Formato MITO VS EVIDENCIA. Empieza con una creencia popular. Luego revela lo que la ciencia realmente dice, con estudios y mecanismos concretos."},
    {"nombre": "anatomia_del_asombro", "instruccion": "Formato ANATOMÍA DEL ASOMBRO. Explora un solo fenómeno desde múltiples ángulos: qué es, cómo funciona, por qué es más extraño de lo que parece."},
    {"nombre": "experimento_mental", "instruccion": "Formato EXPERIMENTO MENTAL. Plantea un escenario contraintuitivo y guía al espectador paso a paso por lo que la ciencia predice."},
]

PERFILES_NARRADOR = ["divulgador científico con formación en biología", "astrofísico divulgador especializado en cosmología", "neurocientífico especializado en percepción", "microbiólogo con experiencia en divulgación", "físico teórico especializado en escenarios hipotéticos", "biólogo evolutivo especializado en comportamiento humano", "químico divulgador con enfoque en fenómenos cotidianos", "documentalista científico de estilo BBC"]

# ================= UTILIDADES =================
def cargar_json(ruta, default):
    try:
        with open(ruta, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def guardar_json(ruta, data):
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ruta)

def cargar_estado():
    estado = cargar_json(ESTADO_FILE, {})
    estado.setdefault("ultimos_fondos", []); estado.setdefault("videos", []); estado.setdefault("temas_recientes", []); estado.setdefault("layouts_usados", [])
    return estado

def parsear_json(texto):
    if not texto: raise ValueError("respuesta vacía")
    t = re.sub(r"```(?:json)?", " ", texto, flags=re.I)
    i, j = t.find("{"), t.rfind("}")
    if i == -1 or j == -1: raise ValueError("sin JSON")
    t = re.sub(r",\s*([}\]])", r"\1", t[i:j + 1])
    if json5:
        try: return json5.loads(t)
        except Exception: pass
    return json.loads(t, strict=False)

def llm(prompt, temperature=0.8, max_tokens=1500, json_mode=False, system=None, intentos=3):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    payload = {"model": DEEPSEEK_MODEL, "messages": msgs, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode: payload["response_format"] = {"type": "json_object"}
    for i in range(intentos):
        try:
            r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=150)
            r.raise_for_status(); return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"⚠️ LLM intento {i+1}/{intentos}: {e}"); time.sleep(5 * (i + 1))
    return None

def descargar(url, ruta, max_bytes=20 * 1024 * 1024):
    try:
        with requests.get(url, stream=True, timeout=40) as r:
            r.raise_for_status(); total = 0
            with open(ruta, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    total += len(chunk)
                    if total > max_bytes: raise ValueError("archivo demasiado grande")
                    f.write(chunk)
            return os.path.getsize(ruta) > 1000
    except Exception as e:
        print(f"⚠️ Descarga fallida: {e}")
        if os.path.exists(ruta): os.remove(ruta)
        return False

def fmt_ts(seg):
    seg = int(seg); h, m, s = seg // 3600, seg % 3600 // 60, seg % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

# ================= HISTORIAL Y YOUTUBE =================
def titulo_ya_publicado(titulo):
    data = cargar_json(TITULOS_FILE, {"titulos": []})
    n = titulo.lower().strip(); p1 = set(re.findall(r"\w+", n))
    for t in data["titulos"]:
        tn = t.lower().strip(); p2 = set(re.findall(r"\w+", tn))
        if n == tn or (len(p1) > 3 and len(p2) > 3 and len(p1 & p2) / min(len(p1), len(p2)) > 0.7): return True
    return False

def titulo_empieza_igual(titulo):
    # POLICÍA DE TÍTULOS: Bloquea prefijos repetitivos
    data = cargar_json(TITULOS_FILE, {"titulos": []})
    primeras3 = titulo.lower().split()[:3]
    for t in data["titulos"][-15:]:
        if t.lower().split()[:3] == primeras3: return True
    
    # Bloqueo duro de fórmulas de la captura
    tl = titulo.lower()
    if tl.startswith("5 cosas") or tl.startswith("lo que tu") or tl.startswith("por qué nunca") or tl.startswith("si la tierra"):
        return True
    return False

def guardar_titulo(titulo):
    data = cargar_json(TITULOS_FILE, {"titulos": []})
    if titulo not in data["titulos"]: data["titulos"].append(titulo)
    data["titulos"] = data["titulos"][-100:]; guardar_json(TITULOS_FILE, data)

def tema_ya_usado(tema, umbral=0.5):
    data = cargar_json(TEMAS_FILE, {"temas": []})
    nuevas = set(re.findall(r"\w+", str(tema).lower()))
    for antiguo in data["temas"][-20:]:
        if isinstance(antiguo, dict): antiguo = antiguo.get("tema", "")
        if not isinstance(antiguo, str) or len(antiguo) > 80: continue
        viejas = set(re.findall(r"\w+", antiguo.lower())); union = nuevas | viejas
        if union and len(nuevas & viejas) / len(union) > umbral: return True
    return False

def guardar_tema(tema):
    data = cargar_json(TEMAS_FILE, {"temas": []})
    data["temas"] = [t for t in data["temas"] if isinstance(t, str) and len(t) < 80]
    if isinstance(tema, str) and len(tema) < 80 and tema not in data["temas"]: data["temas"].append(tema)
    data["temas"] = data["temas"][-20:]; guardar_json(TEMAS_FILE, data)

def crear_cliente_youtube():
    try: return build("youtube", "v3", credentials=Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN))
    except Exception as e: print(f"⚠️ YouTube cliente: {e}"); return None

def sugerencias_youtube(seed):
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search", timeout=10, params={"client": "firefox", "ds": "yt", "hl": "es", "gl": "mx", "q": seed})
        return [s for s in r.json()[1] if isinstance(s, str)][:8]
    except Exception: return []

def actualizar_rendimiento(youtube, estado):
    ids = [v["id"] for v in estado["videos"][-30:] if v.get("id")]
    if not ids or youtube is None: return
    try:
        r = youtube.videos().list(part="statistics", id=",".join(ids)).execute()
        vistas = {i["id"]: int(i["statistics"].get("viewCount", 0)) for i in r.get("items", [])}
        for v in estado["videos"]:
            if v.get("id") in vistas: v["vistas"] = vistas[v["id"]]
    except Exception: pass

def detectar_outliers(youtube, keyword, max_subs=OUTLIER_MAX_SUBS, min_ratio=OUTLIER_MIN_RATIO, days=180, cache_h=OUTLIER_CACHE_HORAS):
    if youtube is None: return []
    cache = cargar_json(OUTLIERS_FILE, {})
    key = f"{keyword}|{max_subs}|{min_ratio}"
    if key in cache and (time.time() - cache[key].get("ts", 0)) < cache_h * 3600: return cache[key]["items"]
    try:
        desde = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        s = youtube.search().list(part="id,snippet", q=keyword, type="video", order="viewCount", publishedAfter=desde, relevanceLanguage="es", regionCode="MX", maxResults=25).execute()
        vids = [i["id"]["videoId"] for i in s.get("items", [])]
        if not vids: return []
        v_resp = youtube.videos().list(part="statistics,snippet", id=",".join(vids)).execute()
        ch_ids, rows = set(), []
        for v in v_resp.get("items", []):
            ch = v["snippet"]["channelId"]; ch_ids.add(ch)
            vistas = int(v["statistics"].get("viewCount", 0)); likes = int(v["statistics"].get("likeCount", 0))
            if vistas > 1000 and (likes / vistas) < 0.01: continue # ENGAGED VIEWS FILTER
            rows.append({"video_id": v["id"], "title": v["snippet"]["title"], "channel_id": ch, "channel_title": v["snippet"]["channelTitle"], "views": vistas})
        subs_map = {}
        for chunk in _chunks(list(ch_ids), 50):
            c = youtube.channels().list(part="statistics", id=",".join(chunk)).execute()
            for item in c.get("items", []): subs_map[item["id"]] = int(item["statistics"].get("subscriberCount", 0))
        out = []
        for r in rows:
            subs = subs_map.get(r["channel_id"], 0)
            if subs == 0 or subs > max_subs: continue
            ratio = r["views"] / max(subs, 1)
            if ratio >= min_ratio: out.append({**r, "subs": subs, "ratio": round(ratio, 1)})
        out.sort(key=lambda x: x["ratio"], reverse=True); out = out[:8]
        cache[key] = {"ts": time.time(), "items": out}; guardar_json(OUTLIERS_FILE, cache)
        return out
    except Exception: return []

def elegir_tema(estado, youtube):
    recientes = estado["temas_recientes"][-10:] # MEMORIA MÁS LARGA (antes 6)
    pool = [t for t in TEMAS if t["tema"] not in recientes] or TEMAS[:]
    candidatos = random.sample(pool, min(5, len(pool)))
    return random.choice(candidatos)

# ================= TÍTULOS Y PLAN =================
GANCHOS = ["nunca", "nadie", "jamás", "solo", "prohibido", "secreto", "escuché", "vi ", "descubrí", "encontré", "sobreviví", "trabajé", "entré", "confieso", "recuerdo", "desapareció", "apareció", "cambió", "por qué", "cómo", "noche", "oscuridad"]
PROHIBIDAS = ["testimonio real", "caso real", "100% real", "verídico", "evidencia", "pruebas", "autoridades", "filtrado"]
GENERICAS = ["misterio", "leyenda", "relato", "caso", "historia de terror", "5 cosas", "por qué nunca"]
SIGLAS_INTOCABLES = {"ADN", "ARN", "NASA", "ONU", "IA", "EEUU", "COVID", "VIH", "SIDA", "OVNI", "PIB", "UE", "OMS", "POV", "TDAH", "OCD", "IQ", "CI", "FGR", "CIA", "FBI", "DEA", "DNI", "GPS", "CCTV", "USB", "LED", "RIP"}

def limpiar_titulo(t):
    t = t.strip().strip('"').strip("'"); t = re.sub(r"\s+", " ", t); t = re.sub(r"\s*[-|–]\s*relato de terror\s*$", "", t, flags=re.I).rstrip(".")
    palabras = t.split(); caps = [w for w in palabras if len(re.sub(r"\W", " ", w)) >= 3 and w.isupper() and w not in SIGLAS_INTOCABLES]
    if len(caps) > 3:
        keep = set(caps[:2]) | SIGLAS_INTOCABLES; palabras = [w if (not w.isupper() or w in keep or len(w) < 3) else w.capitalize() for w in palabras]
    return " ".join(palabras)

def puntuar_titulo(t):
    s, n, tl = 0, len(t), t.lower()
    if 45 <= n <= 68: s += 6
    elif 40 <= n < 45 or 68 < n <= 75: s += 4
    elif 30 <= n < 40 or 75 < n <= 80: s += 2
    elif n > 95 or n < 25: s -= 8
    else: s -= 2
    s += min(8, sum(1 for g in GANCHOS if g in tl) * 2)
    if re.search(r"\d", t): s += 3
    if any(p in tl for p in PROHIBIDAS): s -= 8
    if any(tl.startswith(g) for g in GENERICAS): s -= 20
    return s

def elegir_titulo(candidatos):
    puntuados = []
    for c in candidatos:
        if not isinstance(c, str): continue
        base = limpiar_titulo(c)
        if len(base) < 25 or titulo_ya_publicado(base) or titulo_empieza_igual(base): continue
        puntuados.append((puntuar_titulo(base), base))
    if not puntuados: return None
    puntuados.sort(reverse=True); return puntuados[0][1][:100]

def elegir_texto_portada(opciones, titulo):
    pt = set(re.findall(r"\w+", titulo.lower())); mejor = None
    fallbacks = ["NO SUBAS", "PROHIBIDO", "EL SECRETO", "NO ENTRES", "OCULTAN", "NO MIRES", "PELIGRO", "CUIDADO", "ALERTA"]
    for o in opciones or []:
        if not isinstance(o, str): continue
        o = re.sub(r"[^\w¿?¡! ]", "", o).strip().upper(); w = o.split()
        if not 1 <= len(w) <= 4: continue
        solape = len({x.lower() for x in w} & pt) / len(w)
        sc = (3 if len(w) in (2, 3) else 1) - 2 * solape + (1 if "?" in o else 0)
        if any(x in o for x in ["SECRETO", "PROHIBIDO", "NADIE", "OCULTAN"]): sc += 5
        if mejor is None or sc > mejor[0]: mejor = (sc, o)
    return mejor[1] if mejor else random.choice(fallbacks)

ESQUEMA_PLAN = "{\n \"titulos\": [\"8 títulos de 45-68 caracteres. CADA TÍTULO DEBE TENER UNA ESTRUCTURA SINTÁCTICA COMPLETAMENTE DISTINTA.\"],\n \"tema_central\": \"descripción breve\", \"dato_weird\": \"dato más extraño\", \"gancho\": \"1-2 frases\",\n \"resumen\": \"sinopsis\", \"palabras_clave\": [\"5 keywords SEO\"], \"palabras_portada\": [\"3 opciones MAYÚSCULAS\"],\n \"miniatura_escena\": \"4-6 palabras inglés\", \"descripcion_gancho\": \"2 líneas\", \"titulo_short\": \"máx 55 caracteres\",\n \"pregunta_comentario\": \"pregunta\", \"tags\": [\"15 tags\"], \"puntos\": [{\"titulo\": \"2-4 palabras\", \"resumen\": \"qué pasa\"}]\n}"

def generar_plan(tema, contexto, sugerencias, titulos_previos, formato, perfil):
    prev = "\n".join(f"- {t}" for t in titulos_previos) or "Ninguno"; sug  = "\n".join(f"- {s}" for s in sugerencias) or "Ninguna"
    prompt = f"Eres showrunner de un canal de DIVULGACIÓN CIENTÍFICA. Diseña el PLAN de un video de ~9-11 minutos, con {NUM_PUNTOS} puntos.\nTEMA: {tema['tema']} | ÁNGULO: {tema['angulo']} | CONTEXTO: {contexto}\nFORMATO: {formato['nombre'].upper()} {formato['instruccion']}\nPERFIL: {perfil}\nBÚSQUEDAS: {sug}\nTÍTULOS YA PUBLICADOS: {prev}\nREGLA ESTRICTA: Genera 8 títulos. NO REPITAS ESTRUCTURAS. Si usas 'Por qué', el siguiente debe ser una afirmación, etc. NO USES '5 cosas' ni 'Lo que tu cuerpo'.\nSOLO JSON: {ESQUEMA_PLAN}"
    txt = llm(prompt, temperature=0.9, max_tokens=2800, json_mode=True); plan = parsear_json(txt)
    if not (isinstance(plan.get("titulos"), list) and len(plan["titulos"]) >= 3 and isinstance(plan.get("puntos"), list) and len(plan["puntos"]) >= NUM_PUNTOS and plan.get("gancho") and plan.get("palabras_portada") and plan.get("dato_weird")): raise ValueError("plan incompleto")
    return plan

def limpiar_texto_narracion(t):
    t = re.sub(r"[\U00010000-\U0010ffff]", " ", t); t = re.sub(r"(?im)^\s*(punto|cap[ií]tulo|parte)\s*\d+.\s*$", " ", t); t = re.sub(r"\[[^\]]*\]", " ", t); t = re.sub(r"[*_#>`~]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def generar_puntos(plan, tema, contexto):
    puntos = plan["puntos"][:NUM_PUNTOS]; indice = "\n".join(f"{i+1}. {p.get('titulo','')}: {p.get('resumen','')}" for i, p in enumerate(puntos)); textos = []
    formato = plan.get("_formato_instruccion", "Explicación directa."); perfil = plan.get("_perfil_narrador", "divulgador"); nombre_fmt = plan.get("_nombre_formato", "lista"); dato_w = plan.get("dato_weird", "dato")
    for i, punto in enumerate(puntos):
        previo = textos[-1][-600:] if textos else ""
        extra = f"Empieza EXACTAMENTE con: \"{plan['gancho']}\" e INTEGRA el dato '{dato_w}'." if i == 0 else (f"Cierra con una síntesis. Menciona '{dato_w}'." if i == len(puntos) - 1 else f"Cliffhanger. Menciona '{dato_w}'.")
        prompt = f"Escribe el PUNTO {i+1} de {len(puntos)} de un documental científico.\nFORMATO: {nombre_fmt.upper()} {formato}\nNARRADOR: {perfil} | TEMA: {tema['angulo']} | DATO: {dato_w}\nÍNDICE: {indice}\nESTE PUNTO: {punto.get('titulo', '')}\n{extra}\nFINAL ANTERIOR: {previo}\nREGLAS: 320-400 palabras. Español neutro. METÁFORA COTIDIANA. ASOMBRO + CERCANÍA. SOLO texto."
        texto = None
        for intento in range(3):
            t = llm(prompt, temperature=0.85, max_tokens=1000); t = limpiar_texto_narracion(t) if t else ""
            if len(t.split()) >= 280: texto = t; break
        if not texto: raise RuntimeError(f"Error punto {i+1}")
        textos.append(texto); print(f"   ✅ Punto {i+1}/{len(puntos)}: {len(texto.split())} pal.")
    return textos

def expandir_texto(titulo, texto_actual):
    prompt = f'Relato: "{titulo}". Final:\n"""\n{texto_actual[-500:]}\n"""\nAñade 200-300 palabras. SOLO texto.'
    for _ in range(2):
        t = llm(prompt, temperature=0.8, max_tokens=900); t = limpiar_texto_narracion(t) if t else ""
        if len(t.split()) > 150: return t
    return ""

OUTROS = ["Y hasta aquí llega el video de hoy. Si aprendiste algo nuevo, suscríbete y activa la campanita. Cuéntame en los comentarios: ¿cuál de estos datos te sorprendió más?", "Eso fue todo por hoy. Si llegaste hasta el final, déjame un like y suscríbete para no perderte el siguiente. ¿Tú ya sabías alguno de estos datos? Te leo abajo."]

# ================= SEGMENTOS Y AUDIO =================
def dividir_en_segmentos(texto, max_palabras=SEG_MAX_PALABRAS):
    oraciones = [o.strip() for o in re.split(r"(?<=[.!?…])\s+", texto) if o.strip()]
    if not oraciones: return [texto]
    segs, actual, cuenta = [], [], 0
    for o in oraciones:
        n = len(o.split())
        if cuenta + n > max_palabras and actual: segs.append(" ".join(actual)); actual, cuenta = [o], n
        else: actual.append(o); cuenta += n
    if actual: segs.append(" ".join(actual))
    if len(segs) > 1 and len(segs[-1].split()) < 12: segs[-2] += " " + segs.pop()
    return segs

def crear_segmentos(puntos_txt):
    segs = []
    for pi, txt in enumerate(puntos_txt):
        for k, p in enumerate(dividir_en_segmentos(txt)): segs.append({"punto": pi, "texto": p, "punto_ini": k == 0})
    n = len(segs)
    for i, s in enumerate(segs):
        p = i / max(n - 1, 1)
        s["etapa"] = ("gancho" if p < 0.12 else "contexto" if p < 0.30 else "desarrollo" if p < 0.85 else "conclusion")
    return segs

def duracion_audio(ruta):
    a = AudioFileClip(ruta); d = a.duration; a.close(); return d

def generar_audio(texto, nombre, etapa):
    limpio = re.sub(r'[{}[\]"]', " ", texto); limpio = re.sub(r"\s+", " ", limpio).strip()
    if len(limpio) < 10: return None
    ruta = f"temp_audio_{nombre}.mp3"; rate = RATE_ETAPA.get(etapa, "+4%"); pitch = VOZ_CANAL.get("tono", "-4Hz")
    voces = [VOZ_CANAL["voz"]] + [v for v in VOCES_RESPALDO if v != VOZ_CANAL["voz"]]
    for voz in voces:
        for intento in range(2):
            async def _go():
                communicate = edge_tts.Communicate(limpio, voz, rate=rate, pitch=pitch); await communicate.save(ruta)
            try:
                asyncio.run(_go())
                if os.path.exists(ruta) and os.path.getsize(ruta) > 500: return ruta
            except Exception: time.sleep(2)
    try:
        from gtts import gTTS
        gTTS(text=limpio, lang="es", slow=False).save(ruta)
        if os.path.exists(ruta) and os.path.getsize(ruta) > 500: return ruta
    except Exception: pass
    return None

def sintetizar(segs):
    ok = []
    for i, s in enumerate(segs):
        ruta = generar_audio(s["texto"], s.get("id", i), s["etapa"])
        if not ruta: print(f"⚠️ Seg {i} sin audio"); continue
        s["audio"] = ruta; s["dur_audio"] = duracion_audio(ruta); ok.append(s); time.sleep(0.2)
    if len(ok) < len(segs) * 0.9: raise RuntimeError("Faltan audios")
    return ok

def construir_timeline(segs):
    t = 0.0
    for s in segs: s["inicio"] = t; s["dur"] = s["dur_audio"] + PAUSA_ETAPA.get(s["etapa"], 0.5); t += s["dur"]
    return t

# ================= PEXELS Y CLOUDFLARE =================
POOL_FLUX, POOL_FLUX_INDEX, USADOS_PEXELS = [], 0, set()
def registrar_imagen_flux(ruta):
    if ruta and os.path.exists(ruta) and ruta not in POOL_FLUX: POOL_FLUX.append(ruta)
def reutilizar_imagen_flux(idx):
    global POOL_FLUX_INDEX
    if not POOL_FLUX: return None
    original = POOL_FLUX[POOL_FLUX_INDEX % len(POOL_FLUX)]; POOL_FLUX_INDEX += 1
    if not os.path.exists(original): return None
    try:
        ruta = f"temp_img_{idx}_reused.jpg"; 
        with open(original, "rb") as src, open(ruta, "wb") as dst: dst.write(src.read())
        return ruta
    except Exception: return None

ANTI_DEFORM = ", cinematic wide shot, professional science documentary style, 8k, abstract scientific visualization, glowing bioluminescent elements, minimalist dark aesthetic, highly detailed, safe to show: human silhouette from behind, hands touching objects, eyes close-up, skin texture macro, single body part close-up, no text, no words, clean and futuristic"
def generar_imagen_cloudflare(prompt_en, idx, intentos=3):
    if not USAR_IMAGENES_IA or not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN: return None
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}; payload = {"prompt": prompt_en.strip() + ANTI_DEFORM}
    for i in range(intentos):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 200:
                ruta = f"temp_img_{idx}.jpg"
                if r.headers.get("Content-Type", "").startswith("image"):
                    with open(ruta, "wb") as f: f.write(r.content)
                else:
                    import base64
                    data = r.json()
                    if "result" in data and "image" in data["result"]:
                        with open(ruta, "wb") as f: f.write(base64.b64decode(data["result"]["image"]))
                    else: continue
                if os.path.exists(ruta) and os.path.getsize(ruta) > 1000: registrar_imagen_flux(ruta); return ruta
            time.sleep(3 * (i + 1))
        except Exception: time.sleep(3)
    return None

def pexels_get(url, params, intentos=3):
    for i in range(intentos):
        try:
            r = requests.get(url, headers={"Authorization": PEXELS_API_KEY}, params=params, timeout=25)
            if r.status_code == 200: time.sleep(0.5); return r.json()
            if r.status_code == 429: time.sleep(20 * (i + 1))
        except Exception: time.sleep(2)
    return None

def buscar_fotos_pexels(query, cantidad=1):
    for pagina in (random.randint(1, 2), 1):
        data = pexels_get("https://api.pexels.com/v1/search", {"query": query, "orientation": "landscape", "size": "large", "per_page": 10, "page": pagina})
        fotos = [f["src"]["large2x"] for f in (data or {}).get("photos", [])]; random.shuffle(fotos); fotos = [u for u in fotos if u not in USADOS_PEXELS]
        if fotos: return fotos[:cantidad]
    return []

def imagen_fallback_pexels(prompt_en, idx):
    if not PEXELS_API_KEY: return None
    query = " ".join(prompt_en.split()[:5]); urls = buscar_fotos_pexels(query, 1)
    if urls:
        ruta = f"temp_img_{idx}_pexels.jpg"
        if descargar(urls[0], ruta, 15 * 1024 * 1024): USADOS_PEXELS.add(urls[0]); return ruta
    return None

def imagen_fallback(idx):
    img = Image.new("RGB", (W, H), (10, 15, 25)); draw = ImageDraw.Draw(img)
    for y in range(H): draw.line([(0, y), (W, y)], fill=(int(10 + 30 * y / H), int(15 + 20 * y / H), int(25 + 40 * y / H)))
    ruta = f"temp_img_{idx}_gradient.jpg"; img.save(ruta, "JPEG", quality=85); return ruta

def planificar_visuales(segs, tema):
    out = [None] * len(segs)
    for ini in range(0, len(segs), 15):
        lote = segs[ini:ini + 15]; listado = "\n".join(f"{j+1}. {s['texto'][:250]}" for j, s in enumerate(lote))
        prompt = f"Eres director de fotografía de ciencia. Para CADA fragmento devuelve DOS prompts EN INGLÉS:\n1. 'flux': 5-8 palabras abstractas (ej: glowing cells macro).\n2. 'pexels': 3-5 palabras concretas (ej: person shivering cold dark).\nTema: {tema['tema']}\nFragmentos:\n{listado}\nSOLO JSON: {{\"consultas\": [{{\"flux\": \"...\", \"pexels\": \"...\"}}]}} con {len(lote)} elementos."
        lista = []
        try: lista = parsear_json(llm(prompt, 0.5, 1200, json_mode=True)).get("consultas", [])
        except Exception: pass
        for j, s in enumerate(lote):
            item = lista[j] if j < len(lista) and isinstance(lista[j], dict) else {}
            q_flux = " ".join(re.sub(r"[^a-zA-Z ]", " ", str(item.get("flux", ""))).split()[:8])
            q_pex = " ".join(re.sub(r"[^a-zA-Z ]", " ", str(item.get("pexels", ""))).split()[:5])
            out[ini + j] = {"flux": q_flux if len(q_flux) > 10 else "abstract scientific visualization glowing cells dark", "pexels": q_pex if len(q_pex) > 6 else "person dark night cold"}
    return out

# ================= RENDER Y MINIATURAS =================
_VIG = {}
def vignette(size, base=1.0, fuerza=0.55):
    k = (size, base)
    if k not in _VIG:
        w, h = size; y, x = np.ogrid[-1:1:h * 1j, -1:1:w * 1j]; d = np.clip(np.sqrt(x ** 2 + y ** 2) / 1.414, 0, 1)
        _VIG[k] = ((1 - fuerza * d ** 2.2) * base).astype(np.float32)[..., None]
    return _VIG[k]

def grade(img, etapa):
    img = ImageEnhance.Color(img).enhance(0.92); img = ImageEnhance.Contrast(img).enhance({"gancho": 1.10, "conclusion": 1.05}.get(etapa, 1.08)); img = ImageEnhance.Brightness(img).enhance({"gancho": 1.02, "conclusion": 1.02}.get(etapa, 1.02))
    return Image.blend(img, Image.new("RGB", img.size, (12, 18, 32)), 0.03)

class RenderEscenas:
    def __init__(self, escenas, size, total):
        self.esc, self.size, self.total = escenas, size, total; self.starts = [e["inicio"] for e in escenas]
        self._ikey = self._img = None; self.vig_img = vignette(size, 1.0, 0.30)
    def cerrar(self): pass
    def _base(self, e):
        key = (e["path"], e["etapa"])
        if self._ikey != key:
            sz = (int(self.size[0] * 1.2), int(self.size[1] * 1.2)); im = ImageOps.fit(Image.open(e["path"]).convert("RGB"), sz, Image.LANCZOS)
            arr = np.asarray(grade(im, e["etapa"]), dtype=np.float32) * vignette(sz, 1.0, 0.30); self._img, self._ikey = Image.fromarray(arr.astype(np.uint8)), key
        return self._img
    def _frame_img(self, e, lt):
        base = self._base(e); bw, bh = base.size; p = min(max(lt / e["dur"], 0), 1) if e["dur"] > 0 else 0
        if not e["zin"]: p = 1 - p
        cw = bw / (1 + 0.08 * p); ch = cw * bh / bw; mx, my = bw - cw, bh - ch
        x0 = min(max(mx / 2 + e["ax"] * mx / 2 * 0.8, 0), mx); y0 = min(max(my / 2 + e["ay"] * my / 2 * 0.8, 0), my)
        return np.asarray(base.resize(self.size, Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)))
    def frame(self, t):
        i = max(0, bisect.bisect_right(self.starts, t) - 1); e = self.esc[i]; lt = t - e["inicio"]
        fr = self._frame_img(e, lt); f = 1.0
        if e.get("fade") and lt < 0.6: f = lt / 0.6
        if t > self.total - 1.5: f = min(f, max(0.0, (self.total - t) / 1.5))
        if f < 1.0: fr = (fr.astype(np.float32) * f).astype(np.uint8)
        return fr

def construir_escenas(segs):
    esc = []
    for s in segs:
        n_imgs = max(1, round(s["dur_audio"] / SEG_ESCENA)); dur_por_img = s["dur"] / n_imgs
        for k in range(n_imgs):
            esc.append({"path": s["medios"][k % len(s["medios"])], "inicio": s["inicio"] + k * dur_por_img, "dur": dur_por_img, "etapa": s["etapa"], "fade": bool(k == 0 and s.get("punto_ini")), "zin": random.random() < 0.65, "ax": random.uniform(-1, 1), "ay": random.uniform(-1, 1)})
    return esc

def mezclar_audio(segs, total, fondo, extras=()):
    clips = [AudioFileClip(s["audio"]).set_start(s["inicio"]) for s in segs] + list(extras); narr = CompositeAudioClip(clips); capas = [narr]
    if fondo and os.path.exists(fondo):
        try:
            bg = AudioFileClip(fondo); bg = concatenate_audioclips([bg] * (int(total / bg.duration) + 1)) if bg.duration < total else bg
            capas.append(bg.subclip(0, total).volumex(VOL_FONDO).audio_fadein(2).audio_fadeout(3))
        except Exception: pass
    return CompositeAudioClip(capas).set_duration(total), clips

def renderizar(escenas, total, audio, size, salida, sufijo=""):
    render = RenderEscenas(escenas, size, total); video = VideoClip(render.frame, duration=total).set_audio(audio)
    temp_audio = f"temp_audio_final{sufijo}.m4a"
    video.write_videofile(salida, fps=FPS, codec="libx264", audio_codec="aac", audio_bitrate="192k", threads=4, preset="veryfast", temp_audiofile=temp_audio, ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart"], logger=None)
    render.cerrar(); video.close()
    try:
        if os.path.exists(temp_audio): os.remove(temp_audio)
    except Exception: pass
    return salida

def obtener_fuente(size, font_idx=0):
    os.makedirs("fonts", exist_ok=True)
    urls = ["https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf", "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald-Bold.ttf", "https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf"]
    ruta = f"fonts/font_{font_idx}.ttf"
    if not os.path.exists(ruta):
        try:
            r = requests.get(urls[font_idx % len(urls)], timeout=20)
            if r.status_code == 200: 
                with open(ruta, "wb") as f: f.write(r.content)
        except Exception: pass
    for p in [ruta, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        try: return ImageFont.truetype(p, size)
        except Exception: continue
    return ImageFont.load_default()

def buscar_rostro_terror_pexels(query_base=""):
    if not PEXELS_API_KEY: return None
    queries = ["shocked man face dark", "surprised woman portrait dark", "scared face low light", "person looking amazed", "confused face portrait", "curious person face dark"]
    random.shuffle(queries)
    for q in queries[:4]:
        try:
            data = pexels_get("https://api.pexels.com/v1/search", {"query": q, "orientation": "portrait", "size": "large", "per_page": 8, "page": 1}); fotos = (data or {}).get("photos", [])
            if not fotos: continue
            foto = random.choice([f for f in fotos if f["src"]["large2x"] not in USADOS_PEXELS][:4])
            ruta = f"temp_thumb_rostro_{random.randint(1000,9999)}.jpg"
            if descargar(foto["src"]["large2x"], ruta, 15 * 1024 * 1024): USADOS_PEXELS.add(foto["src"]["large2x"]); return ruta
        except Exception: pass
    return None

def buscar_cuerpo_terror_pexels(query_base=""):
    if not PEXELS_API_KEY: return None
    queries = ["person touching head stressed", "hands touching skin dramatic", "silhouette person standing dark", "body closeup skin texture", "hand touching cold ice"]
    random.shuffle(queries)
    for q in queries[:4]:
        try:
            data = pexels_get("https://api.pexels.com/v1/search", {"query": q, "orientation": "landscape", "size": "large", "per_page": 8, "page": 1}); fotos = (data or {}).get("photos", [])
            if not fotos: continue
            foto = random.choice([f for f in fotos if f["src"]["large2x"] not in USADOS_PEXELS][:4])
            ruta = f"temp_thumb_cuerpo_{random.randint(1000,9999)}.jpg"
            if descargar(foto["src"]["large2x"], ruta, 15 * 1024 * 1024): USADOS_PEXELS.add(foto["src"]["large2x"]); return ruta
        except Exception: pass
    return None

def dividir_lineas(palabras):
    if len(palabras) <= 2: return palabras[:]
    mejor = None
    for i in range(1, len(palabras)):
        a, b = " ".join(palabras[:i]), " ".join(palabras[i:]); m = max(len(a), len(b))
        if mejor is None or m < mejor[0]: mejor = (m, [a, b])
    return mejor[1]

def crear_miniatura_ciencia(img_path, texto, salida, font_idx, forzar_layout=None):
    TW, TH = 1280, 720
    # POLICÍA DE LAYOUTS: Forzamos variedad. Si no se fuerza, elegimos uno.
    layout = forzar_layout if forzar_layout else random.choice([1, 2, 3, 4])
    try:
        if img_path and os.path.exists(img_path):
            img = Image.open(img_path).convert("RGB"); img = ImageOps.fit(img, (TW, TH), Image.LANCZOS)
        else:
            img = Image.new("RGB", (TW, TH), (8, 10, 20))
            for y in range(TH): ImageDraw.Draw(img).line([(0, y), (TW, y)], fill=(int(5 + 20 * y / TH), int(10 + 25 * y / TH), int(20 + 35 * y / TH)))
        
        img = ImageEnhance.Contrast(img).enhance(1.35); img = ImageEnhance.Color(img).enhance(1.25); img = ImageEnhance.Sharpness(img).enhance(2.3); img = ImageEnhance.Brightness(img).enhance(1.15)
        grad = Image.new("L", (TW, TH), 0); gd = ImageDraw.Draw(grad)
        
        if layout == 1: # Texto Derecha
            for x in range(TW): gd.line([(x, 0), (x, TH)], fill=int(200 * max(0, min(1, (x / TW - 0.40) / 0.60))))
        elif layout == 2: # Texto Izquierda
            for x in range(TW): gd.line([(x, 0), (x, TH)], fill=int(200 * max(0, min(1, ((TW-x) / TW - 0.40) / 0.60))))
        elif layout == 3: # Texto Abajo
            for y in range(TH): gd.line([(0, y), (TW, y)], fill=int(200 * max(0, min(1, (y / TH - 0.35) / 0.65))))
        else: # Texto Arriba
            for y in range(TH): gd.line([(0, y), (TW, y)], fill=int(200 * max(0, min(1, ((TH-y) / TH - 0.35) / 0.65))))
            
        img = Image.composite(Image.new("RGB", (TW, TH), (0, 0, 0)), img, grad)
        arr = np.asarray(img, dtype=np.float32) * vignette((TW, TH), 1.0, 0.25); img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
        
        texto_upper = texto.upper(); palabras = texto_upper.split()[:4]; lineas = dividir_lineas(palabras)
        if layout == 1: x_inicio, max_w = int(TW * 0.55), TW - int(TW * 0.55) - 40
        elif layout == 2: x_inicio, max_w = 40, int(TW * 0.45) - 40
        else: x_inicio, max_w = 60, TW - 120
        
        max_h = int(TH * 0.75); size_final = 60
        for size in range(140, 55, -6):
            font = obtener_fuente(size, font_idx); cajas = [font.getbbox(l) for l in lineas]; ancho_max = max(b[2] - b[0] for b in cajas); alto_total = sum(b[3] - b[1] for b in cajas) + 18 * (len(lineas) - 1)
            if ancho_max <= max_w and alto_total <= max_h: size_final = size; break
        
        font = obtener_fuente(size_final, font_idx); cajas = [font.getbbox(l) for l in lineas]; alto_total = sum(b[3] - b[1] for b in cajas) + 18 * (len(lineas) - 1)
        if layout in [1, 2]: y = (TH - alto_total) // 2
        elif layout == 3: y = TH - alto_total - 60
        else: y = 60
        
        pos_lineas = []
        for l, b in zip(lineas, cajas):
            ancho_l = b[2] - b[0]; x = x_inicio + (max_w - ancho_l) // 2; pos_lineas.append((l, x, y - b[1])); y += (b[3] - b[1]) + 18
            
        overlay_bg = Image.new("RGBA", (TW, TH), (0,0,0,0)); bg_draw = ImageDraw.Draw(overlay_bg)
        for l, x, yy in pos_lineas:
            bbox = font.getbbox(l); bg_draw.rectangle([x - 15, yy - 10, x + (bbox[2]-bbox[0]) + 15, yy + (bbox[3]-bbox[1]) + 10], fill=(0,0,0,160))
        img = Image.alpha_composite(img, overlay_bg)
        
        estilo = random.choice([{"color_texto": (255, 255, 255), "color_acento": (0, 255, 255), "stroke": (0, 0, 0), "elemento": "circulo"}, {"color_texto": (255, 220, 0), "color_acento": (255, 255, 255), "stroke": (0, 0, 0), "elemento": "triangulo"}])
        
        glow = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); gdraw = ImageDraw.Draw(glow)
        for l, x, yy in pos_lineas: gdraw.text((x, yy), l, font=font, fill=estilo["color_acento"] + (255,), stroke_width=14, stroke_fill=estilo["color_acento"] + (255,))
        img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(24)))
        
        draw = ImageDraw.Draw(img); borde = max(8, size_final // 14)
        for i, (l, x, yy) in enumerate(pos_lineas): draw.text((x, yy), l, font=font, fill=(estilo["color_acento"] if (i == len(pos_lineas) - 1) else estilo["color_texto"]) + (255,), stroke_width=borde, stroke_fill=estilo["stroke"] + (255,))
        
        rgb = img.convert("RGB")
        for q in (92, 87, 82, 76, 70):
            rgb.save(salida, "JPEG", quality=q, optimize=True)
            if os.path.getsize(salida) < 1_900_000: break
        print(f"✅ Miniatura [Layout {layout}] [Font {font_idx}]")
        return True
    except Exception as e: print(f"❌ Error miniatura: {e}"); return False

# ================= SEO Y TAGS =================
def _ascii_tag_yt(t):
    nfd = unicodedata.normalize('NFD', str(t)); sin_acentos = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', '', sin_acentos.lower())).strip()

def _sanitizar_tags(tags, max_tags=35, max_chars_tag=45, max_words=6):
    limpios, vistos = [], set()
    for t in tags or []:
        if not isinstance(t, str): continue
        t = _ascii_tag_yt(t)
        if not t or t in vistos or len(t) < 3: continue
        if len(t.split()) > max_words: t = " ".join(t.split()[:max_words])
        vistos.add(t); limpios.append(t)
        if len(limpios) >= max_tags: break
    random.shuffle(limpios); return limpios

def construir_tags(plan, tema, sugerencias):
    nombre_tema = _ascii_tag_yt(tema["tema"].replace("_", " "))
    exactos = list(plan.get("tags", []))[:15]
    broad = ["ciencia", "divulgacion cientifica", "datos curiosos", "ciencia weird", "cuerpo humano", "universo", "neurociencia"]
    long_tail = [f"que hay en {nombre_tema}", f"como funciona {nombre_tema}", f"el secreto de {nombre_tema}", f"la ciencia de {nombre_tema}"]
    todos = exactos + broad + long_tail + list(sugerencias)[:10] + list(tema["keywords"])[:5]
    return _sanitizar_tags(todos, max_tags=35, max_chars_tag=45, max_words=6)

def construir_hashtags(tema, plan):
    hs = ["#Ciencia", "#DivulgacionCientifica"] + tema.get("hashtags", [])[:2] + ["#DatosCuriosos"]
    return " ".join(list(dict.fromkeys(hs))[:5])

def construir_descripcion(plan, tema, caps_ts, sugerencias, hashtags):
    kws = plan.get("palabras_clave", []); kw1 = kws[0] if kws else tema["tema"].replace("_", " ")
    dato = plan.get("dato_weird", ""); resumen = plan.get("resumen", "")
    linea1 = f"🎯 {kw1.title()}: {dato}." if dato else f"🎯 {kw1.title()}: {resumen[:120]}"
    linea2 = f"En este video te explico {plan.get('gancho', '')[:180]}"
    capitulos = "\n".join(f"{ts} {t}" for ts, t in caps_ts); rel = ", ".join(sugerencias[:5])
    partes = [linea1, linea2, "", f"🔔 SUSCRÍBETE: {CANAL_LINK}?sub_confirmation=1", "", f"⏰ CAPÍTULOS\n{capitulos}", "", f"📖 SOBRE ESTE VIDEO\n{resumen}", "", (f"🔎 BÚSQUEDAS RELACIONADAS: {rel}" if rel else "")]
    if ACTIVAR_DISCLOSURE_IA: partes.append(DISCLOSURE_TEXT.strip())
    partes.append(hashtags); return "\n\n".join(p for p in partes if p)[:4900]

def generar_srt(segs, ruta):
    def ts(x):
        h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"
    lineas, n = [], 1
    for s in segs:
        pal = s["texto"].split()
        if not pal: continue
        t = s["inicio"]
        for i in range(0, len(pal), 9):
            tr = pal[i:i + 9]; d = s["dur_audio"] * len(tr) / len(pal); lineas.append(f"{n}\n{ts(t)} --> {ts(t + d)}\n{' '.join(tr)}\n"); n, t = n + 1, t + d
    with open(ruta, "w", encoding="utf-8") as f: f.write("\n".join(lineas))
    return ruta

def seleccionar_voz_semana(estado):
    v = random.choice(VOCES_ROTACION)
    return {"voz": v["voz"], "tono": f"{random.randint(-5, 2)}Hz", "rate": f"+{random.randint(5, 15)}%"}

def generar_comentario_fijado(plan, tema):
    pregunta = plan.get("pregunta_comentario") or random.choice([f"¿Ustedes qué harían si les pasara algo así en {random.choice(tema['contextos'])}?", "¿Creen que estas leyendas tienen algo de real?", "¿Cuál es la historia más extraña que les ha pasado?"])
    return f"📖 Este relato fue adaptado con asistencia de IA para narrar una leyenda compartida por la comunidad.\n\n{pregunta} Los leo 👇\n\n— El equipo de Sombras 🌙"

# ================= PUBLICACIÓN =================
def deberia_publicar(estado):
    ult = estado.get("ultima_publicacion")
    if not ult: return True
    try:
        dt = datetime.fromisoformat(ult)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=TZ)
        horas = (datetime.now(TZ) - dt).total_seconds() / 3600; min_horas = INTERVALO_MIN_HORAS * random.uniform(0.85, 1.15)
        if horas < min_horas: print(f"⏸️ Han pasado {horas:.1f}h (mínimo {min_horas:.1f}h)."); return False
    except ValueError: pass
    return True

def proximo_slot_batch():
    ahora = datetime.now(TZ); slot_mas_temprano_hoy = ahora.replace(hour=HORA_LARGO, minute=0, second=0, microsecond=0) - timedelta(minutes=VARIACION_MINUTOS_LARGO)
    dia_base = (ahora + timedelta(days=1)).date() if slot_mas_temprano_hoy - ahora < timedelta(minutes=10) else ahora.date()
    dia_dt = datetime.combine(dia_base, datetime.min.time()).replace(tzinfo=TZ)
    def slot(hora, variacion, offset=0): return dia_dt.replace(hour=hora, minute=0) + timedelta(minutes=random.randint(-variacion, variacion) + offset)
    slot_largo = slot(HORA_LARGO, VARIACION_MINUTOS_LARGO); slot_short1 = slot(HORA_SHORT_1, VARIACION_MINUTOS_SHORT_1, offset=15); slot_short2 = slot(HORA_SHORT_2, VARIACION_MINUTOS_SHORT_2, offset=15)
    ahora_min = ahora + timedelta(minutes=15)
    if slot_largo < ahora_min: slot_largo = ahora_min + timedelta(minutes=30)
    if slot_short1 < ahora_min: slot_short1 = ahora_min + timedelta(minutes=45)
    if slot_short2 < ahora_min: slot_short2 = ahora_min + timedelta(minutes=60)
    return slot_largo, slot_short1, slot_short2

def utc_iso(dt): return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def subir_video(youtube, ruta, titulo, descripcion, tags, publish_at=None):
    status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    if publish_at: status.update({"privacyStatus": "private", "publishAt": publish_at})
    tags = _sanitizar_tags(tags, max_tags=35, max_chars_tag=45, max_words=6)
    body = {"snippet": {"title": titulo[:100], "description": descripcion[:5000], "tags": tags, "categoryId": CATEGORY_ID, "defaultLanguage": "es", "defaultAudioLanguage": "es"}, "status": status}
    media = MediaFileUpload(ruta, chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4"); req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp, reintentos = None, 0
    while resp is None:
        try:
            st, resp = req.next_chunk()
            if st: print(f"   ⬆️ {int(st.progress() * 100)}%")
        except (HttpError, ssl.SSLEOFError, ConnectionError, socket.timeout, OSError) as e:
            if isinstance(e, HttpError) and e.resp.status == 400 and "invalidTags" in str(e):
                print(f"⚠️ invalidTags. Reintentando con tags seguros...")
                body["snippet"]["tags"] = _sanitizar_tags(tags, max_tags=15, max_chars_tag=20, max_words=3)
                req = youtube.videos().insert(part="snippet,status", body=body, media_body=media); continue
            es_reintento = (isinstance(e, HttpError) and e.resp.status in (429, 500, 502, 503, 504)) or isinstance(e, (ssl.SSLEOFError, ConnectionError, socket.timeout, OSError))
            if es_reintento and reintentos < 8: reintentos += 1; time.sleep(2 ** reintentos); continue
            raise
    print(f"✅ Video subido: https://youtu.be/{resp['id']}" + (f" (programado {publish_at})" if publish_at else "")); return resp["id"]

def extras_post_subida(youtube, vid, miniatura, srt, comentario):
    if miniatura and os.path.exists(miniatura):
        try: youtube.thumbnails().set(videoId=vid, media_body=MediaFileUpload(miniatura, mimetype="image/jpeg")).execute(); print("✅ Miniatura subida")
        except Exception: pass
    if srt and os.path.exists(srt):
        try: youtube.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": "es", "name": "Español", "isDraft": False}}, media_body=MediaFileUpload(srt, mimetype="application/octet-stream")).execute(); print("✅ Subtítulos subidos")
        except Exception: pass
    if PLAYLIST_ID:
        try: youtube.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": PLAYLIST_ID, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute(); print("✅ Añadido a playlist")
        except Exception: pass
    if comentario:
        try: youtube.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": comentario}}}}).execute(); print("✅ Comentario publicado")
        except Exception: pass

def crear_short_con_guion(guion_texto, titulo_short, hashtags_short, fondo, indice, salida):
    print(f"   📱 Short {indice} guion: {len(guion_texto.split())} palabras")
    textos = dividir_en_segmentos(guion_texto)
    if not textos: return None, 0
    segs = [{"texto": txt, "etapa": "gancho" if i == 0 else ("conclusion" if i == len(textos) - 1 else "desarrollo"), "id": f"sh{indice}_{i}"} for i, txt in enumerate(textos)]
    segs = sintetizar(segs)
    if not segs: return None, 0
    total = construir_timeline(segs)
    prompts_short = planificar_visuales(segs, {"tema": "short", "angulo": titulo_short})
    for i, s in enumerate(segs):
        n_imgs = max(1, round(s["dur_audio"] / SEG_ESCENA)); medios = []
        for k in range(n_imgs):
            img_id = f"sh{indice}_{i}_{k}"; pv = prompts_short[i] if i < len(prompts_short) else {"flux": "abstract science", "pexels": "person dark"}
            ruta = generar_imagen_cloudflare(pv["flux"], img_id) or reutilizar_imagen_flux(img_id) or imagen_fallback_pexels(pv["pexels"], img_id) or imagen_fallback(img_id)
            medios.append(ruta)
        s["medios"] = medios
    
    fallback_count = sum(1 for s in segs for m in s["medios"] if "gradient" in m); total_imgs = sum(len(s["medios"]) for s in segs)
    if total_imgs > 0 and (fallback_count / total_imgs) > 0.5: return None, 0

    cta_texto = random.choice(["El video completo con todas las revelaciones está en el canal.", "Esto es solo una parte. La explicación científica completa te espera en el canal."])
    cta = generar_audio(cta_texto, f"cta_{indice}", "conclusion")
    escenas = construir_escenas(segs); extras, total_final = [], total
    if cta:
        d = duracion_audio(cta); extras.append(AudioFileClip(cta).set_start(total)); ult = escenas[-1]; escenas.append({**ult, "inicio": total, "dur": d + 0.6, "fade": False}); total_final = total + d + 0.6
    audio, _ = mezclar_audio(segs, total_final, fondo, extras); renderizar(escenas, total_final, audio, (1080, 1920), salida, sufijo=f"_s{indice}"); return salida, total_final

# ================= MAIN =================
def buscar_archivo(nombre):
    for root, _, files in os.walk("."):
        if "/." in root or "\\." in root: continue
        if nombre in files: return os.path.join(root, nombre)
    return None

def seleccionar_fondo(estado):
    ultimos = estado["ultimos_fondos"]; disp = [f for f in FONDOS_DISPONIBLES if f not in ultimos[-3:]] or FONDOS_DISPONIBLES[:]
    random.shuffle(disp)
    for f in disp + FONDOS_DISPONIBLES:
        ruta = buscar_archivo(f)
        if ruta: estado["ultimos_fondos"] = (ultimos + [f])[-10:]; print(f"🎵 Fondo: {ruta}"); return ruta
    return None

def limpiar_temporales():
    for f in os.listdir("."):
        if f.startswith("temp_") or f in ("video_final.mp4", "short_1.mp4", "short_2.mp4", "miniatura.jpg", "subtitulos.srt"):
            try: os.remove(f)
            except OSError: pass

def verificar_envs():
    faltan = [v for v in ("DEEPSEEK_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "YOUTUBE_USER_TOKEN") if not os.getenv(v)]
    if faltan: print(f"❌ Faltan variables: {', '.join(faltan)}"); sys.exit(1)
    yt = crear_cliente_youtube()
    if yt is None: sys.exit(1)
    return yt

def main():
    global NUM_PUNTOS, VOZ_CANAL
    youtube = verificar_envs(); limpiar_temporales(); estado = cargar_estado()
    if os.getenv("FORCE_PUBLISH") == "true": print("⚡ FORCE_PUBLISH activo")
    elif not deberia_publicar(estado): sys.exit(0)

    VOZ_CANAL = seleccionar_voz_semana(estado); estilo_semana = random.choice(IDENTIDAD_VISUAL["estilos_rotacion"])
    
    print("=" * 70)
    print("🧬 CHISPAS INQUIETAS - BOT v1.9 ANTI-LOOP")
    print(f"📅 {datetime.now(TZ):%Y-%m-%d %H:%M} | 🎤 {VOZ_CANAL['voz']} ({VOZ_CANAL['rate']}, {VOZ_CANAL['tono']}) | 🎬 videos: {USAR_IMAGENES_IA}")
    print("=" * 70)

    actualizar_rendimiento(youtube, estado)
    tema = elegir_tema(estado, youtube); contexto = random.choice(tema["contextos"])
    formato = random.choice(FORMATOS_NARRACION); perfil = random.choice(PERFILES_NARRADOR)
    print(f"🎭 Formato: {formato['nombre']} | Narrador: {perfil}")

    sugerencias = list(dict.fromkeys(sugerencias_youtube(tema["seed"]) + sugerencias_youtube("ciencia " + tema["keywords"][0])))[:10]
    fondo = seleccionar_fondo(estado); titulos_previos = cargar_json(TITULOS_FILE, {"titulos": []})["titulos"][-20:]

    plan = titulo = None
    for intento in range(6):
        try:
            plan = generar_plan(tema, contexto, sugerencias, titulos_previos, formato, perfil)
            if plan.get("palabras_clave") and tema_ya_usado(" ".join(map(str, plan["palabras_clave"]))): raise ValueError("tema repetido")
            titulo = elegir_titulo(plan["titulos"])
            if not titulo: raise ValueError("sin título válido")
            plan["_formato_instruccion"] = formato["instruccion"]; plan["_perfil_narrador"] = perfil; plan["_nombre_formato"] = formato["nombre"]
            break
        except Exception as e:
            print(f"⚠️ Plan intento {intento+1}/6: {e}"); plan = None; time.sleep(5)
    if not plan: print("❌ No se pudo generar un plan válido."); sys.exit(1)

    print(f"📌 Título: {titulo}"); print(f"🎯 Dato weird: {plan.get('dato_weird', 'N/A')}")

    puntos_txt = generar_puntos(plan, tema, contexto); n_puntos = len(puntos_txt); segs = crear_segmentos(puntos_txt)
    segs = sintetizar(segs); total = construir_timeline(segs); intentos = 0
    while total < DURACION_MINIMA_SEGUNDOS and intentos < MAX_INTENTOS_EXPANSION:
        extra = expandir_texto(titulo, " ".join(s["texto"] for s in segs)); intentos += 1
        if not extra: break
        nuevos = [{"punto": n_puntos - 1, "texto": p, "punto_ini": False, "etapa": "conclusion", "id": f"x{intentos}_{k}"} for k, p in enumerate(dividir_en_segmentos(extra))]
        segs += sintetizar(nuevos); total = construir_timeline(segs)
    if total > DURACION_MAXIMA_SEGUNDOS:
        while total > DURACION_MAXIMA_SEGUNDOS:
            idx = next((i for i in range(len(segs) - 1, -1, -1) if segs[i].get("expansion")), None)
            if idx is None: break
            segs.pop(idx); total = construir_timeline(segs)
    if total < DURACION_MINIMA_SEGUNDOS: print("❌ Duración insuficiente."); sys.exit(1)

    outro = [{"punto": n_puntos - 1, "texto": random.choice(OUTROS), "punto_ini": False, "etapa": "conclusion", "id": "outro"}]
    segs += sintetizar(outro); total = construir_timeline(segs); print(f"⏱️ Duración final: {total/60:.1f} min")

    prompts_visuales = planificar_visuales(segs, tema); stats = {"flux": 0, "pool": 0, "pexels": 0, "gradient": 0}
    for i, s in enumerate(segs):
        n_imgs = max(1, round(s["dur_audio"] / SEG_ESCENA)); pv = prompts_visuales[i] if i < len(prompts_visuales) else {"flux": "abstract science", "pexels": "person dark"}; medios = []
        for k in range(n_imgs):
            img_id = f"{i}_{k}"; ruta = generar_imagen_cloudflare(pv["flux"], img_id)
            if ruta: stats["flux"] += 1
            else:
                ruta = reutilizar_imagen_flux(img_id)
                if ruta: stats["pool"] += 1
                else:
                    ruta = imagen_fallback_pexels(pv["pexels"], img_id)
                    if ruta: stats["pexels"] += 1
                    else: ruta = imagen_fallback(img_id); stats["gradient"] += 1
            medios.append(ruta)
        s["medios"] = medios

    caps_ts = []
    for p in range(n_puntos):
        primero = next((s for s in segs if s["punto"] == p), None)
        nombre = (str(plan["puntos"][p].get("titulo", f"Punto {p+1}"))[:50] if p < len(plan["puntos"]) else f"Punto {p+1}")
        if primero: caps_ts.append((fmt_ts(primero["inicio"]), nombre))
    if caps_ts: caps_ts[0] = ("00:00", caps_ts[0][1])

    hashtags = construir_hashtags(tema, plan); descripcion = construir_descripcion(plan, tema, caps_ts, sugerencias, hashtags); tags = construir_tags(plan, tema, sugerencias); srt = generar_srt(segs, "subtitulos.srt")
    print(f"🏷️  Tags ({len(tags)}): {', '.join(tags[:6])}...")

    # ================= POLICÍA DE LAYOUTS =================
    # Forzamos a que la miniatura cambie de layout comparado con las ultimas 3 subidas
    layouts_recientes = estado.get("layouts_usados", [])[-3:]
    posibles_layouts = [1, 2, 3, 4]
    for l in layouts_recientes:
        if l in posibles_layouts and len(posibles_layouts) > 1: posibles_layouts.remove(l)
    layout_elegido = random.choice(posibles_layouts)
    
    print(f"🖼️  Generando miniatura forzada a Layout {layout_elegido}...")
    portada = elegir_texto_portada(plan.get("palabras_portada"), titulo)
    
    # 70% de las veces usamos escena (sin cara) para no ser repetitivos
    if random.random() < 0.7:
        img_mini = buscar_cuerpo_terror_pexels(tema["tema"]) or buscar_rostro_terror_pexels(tema["tema"] + " scared")
    else:
        img_mini = buscar_rostro_terror_pexels(tema["tema"] + " scared") or buscar_cuerpo_terror_pexels(tema["tema"])
        
    font_idx = random.randint(0, 2)
    miniatura_ok = crear_miniatura_ciencia(img_mini, portada, "miniatura.jpg", font_idx, forzar_layout=layout_elegido)
    miniatura = "miniatura.jpg" if miniatura_ok else None
    if miniatura_ok:
        estado["layouts_usados"] = (estado.get("layouts_usados", []) + [layout_elegido])[-10:]

    escenas = construir_escenas(segs); audio, _ = mezclar_audio(segs, total, fondo)
    print("🎬 Renderizando video largo..."); renderizar(escenas, total, audio, (W, H), "video_final.mp4", sufijo="_largo")

    slot_largo, slot_short1, slot_short2 = proximo_slot_batch() if PROGRAMAR_PICO else (None, None, None)
    if slot_largo: print(f"🕖 Programado: {slot_largo:%Y-%m-%d %H:%M} CDMX")

    vid = subir_video(youtube, "video_final.mp4", titulo, descripcion, tags, utc_iso(slot_largo) if slot_largo else None)
    comentario = str(plan.get("pregunta_comentario") or "¿Qué opinas? Te leo 👇")
    extras_post_subida(youtube, vid, miniatura, srt, comentario)

    if GENERAR_SHORT:
        print("📱 Generando shorts...")
        shorts_data = generar_short_scripts(plan, tema)
        if shorts_data:
            for idx, key in enumerate(("short1", "short2"), start=1):
                sd = shorts_data.get(key, {})
                if not sd: continue
                try:
                    resultado = crear_short_con_guion(sd["guion"], sd["titulo"], sd.get("hashtags", ""), fondo, idx, f"short_{idx}.mp4")
                    if resultado and resultado[0]:
                        t_short = sd["titulo"][:88] + " #Shorts"
                        d_short = f"{sd['titulo']}\n\n📺 Video completo 👉 https://youtu.be/{vid}\n\n🔔 Suscríbete: {CANAL_LINK}?sub_confirmation=1\n\n#Shorts {sd.get('hashtags', '')}" + (DISCLOSURE_TEXT if ACTIVAR_DISCLOSURE_IA else "")
                        tags_short = _sanitizar_tags([t.strip().lstrip("#") for t in sd.get("hashtags", "").split() if t.startswith("#")] + ["shorts"])
                        slot_s = slot_short1 if idx == 1 else slot_short2
                        vid_short = subir_video(youtube, f"short_{idx}.mp4", t_short, d_short, tags_short, utc_iso(slot_s) if slot_s else None)
                        if vid_short: print(f"✅ Short {idx}: https://youtu.be/{vid_short}")
                except Exception as e: print(f"⚠️ Error short {idx}: {e}")

    ahora = datetime.now(TZ).isoformat(); guardar_titulo(titulo); guardar_tema(tema["tema"])
    estado["videos"].append({"id": vid, "titulo": titulo, "tema": tema["tema"], "formato": formato["nombre"], "perfil": perfil, "duracion_min": round(total / 60, 1), "fecha": ahora})
    estado["videos"] = estado["videos"][-60:]; estado["temas_recientes"] = (estado["temas_recientes"] + [tema["tema"]])[-15:]; estado["ultima_publicacion"] = ahora
    
    guardar_json(ESTADO_FILE, estado); limpiar_temporales(); print("🎉 Proceso completo.")

if __name__ == "__main__":
    try: main()
    except SystemExit: raise
    except Exception as e: print(f"❌ Error fatal: {e}"); traceback.print_exc(); sys.exit(1)
