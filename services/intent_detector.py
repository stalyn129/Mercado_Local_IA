import re
import unicodedata

INTENTS = {
    "precio": [
        "precio", "cuesta", "vale", "costo",
        "cuanto", "cuanto cuesta", "precio de"
    ],
    "stock": [
        "stock", "disponible", "hay", "queda",
        "tiene", "tienen"
    ],
    "producto": [
        "producto", "buscar", "ver", "comprar",
        "mostrar", "ver producto"
    ],
    "saludo": [
        "hola", "buenas", "hey", "saludos"
    ],
    "recomendacion": [
        "recomienda", "sugiere", "que compro",
        "que me recomiendas"
    ]
}

def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def detectar_intencion(mensaje: str) -> str:
    mensaje = _normalizar(mensaje)

    scores = {}

    for intent, expresiones in INTENTS.items():
        scores[intent] = 0
        for exp in expresiones:
            if exp in mensaje:
                scores[intent] += 1

    # intención con mayor score
    mejor_intent = max(scores, key=scores.get)

    # si no detecta nada con peso
    if scores[mejor_intent] == 0:
        return "chat"

    return mejor_intent
