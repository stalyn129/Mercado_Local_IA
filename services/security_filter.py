import unicodedata
import re

# 🔒 Palabras realmente sensibles (internas)
FORBIDDEN_KEYWORDS = {
    "credenciales": [
        "contraseña", "password", "token", "jwt", "api key", "clave"
    ],
    "datos_internos": [
        "ganancia", "margen", "proveedor", "costo interno",
        "correo interno", "email interno", "id interno"
    ],
    "seguridad": [
        "hackear", "bypass", "vulnerabilidad", "inyeccion"
    ]
}

# Expresiones permitidas (evita falsos positivos)
ALLOWED_CONTEXTS = [
    "costo de envio",
    "precio de envio",
    "correo de contacto"
]


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def evaluar_peligrosidad(mensaje: str):
    """
    Retorna:
    - None → seguro
    - dict → bloqueo con razón
    """
    mensaje = _normalizar(mensaje)

    # permitir contextos legítimos
    for permitido in ALLOWED_CONTEXTS:
        if permitido in mensaje:
            return None

    for categoria, palabras in FORBIDDEN_KEYWORDS.items():
        for p in palabras:
            if re.search(rf"\b{p}\b", mensaje):
                return {
                    "bloqueado": True,
                    "categoria": categoria,
                    "mensaje": "Solicitud no permitida por razones de seguridad."
                }

    return None
