import re

def extraer_palabras_clave(texto: str):
    if not texto:
        return []
    
    # Convertir a minúsculas y quitar caracteres especiales
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    
    # Lista de palabras a ignorar (stopwords)
    ignore = {"de", "con", "el", "la", "los", "las", "un", "una", "y", "para", "fresco", "artesanal"}
    
    # Filtrar palabras cortas o en la lista de ignorar
    palabras = [p for p in texto.split() if p not in ignore and len(p) > 2]
    
    return palabras