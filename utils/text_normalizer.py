import unicodedata
import re

STOPWORDS = {"de", "la", "el", "los", "las", "un", "una"}

def normalizar_texto(texto: str) -> str:
    texto = texto.lower()

    # quitar acentos
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")

    # quitar caracteres raros
    texto = re.sub(r"[^a-z0-9\s]", "", texto)

    return texto.strip()

def extraer_palabras_clave(texto: str):
    texto = normalizar_texto(texto)
    palabras = texto.split()
    return [p for p in palabras if p not in STOPWORDS and len(p) > 2]
