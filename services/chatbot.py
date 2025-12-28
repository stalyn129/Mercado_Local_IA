import os
import requests

from services.chat_session import save_message, get_history
from services.product_service import buscar_producto_seguro
from services.intent_detector import detectar_intencion
from services.security_filter import evaluar_peligrosidad

# ===============================
# ⚙️ CONFIGURACIÓN
# ===============================
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# ===============================
# 🤖 CHATBOT IA FINAL
# ===============================
def ask_chatbot(user_id: int, rol: str, mensaje: str):

    # =====================================================
    # 1️⃣ FILTRO DE SEGURIDAD
    # =====================================================
    bloqueo = evaluar_peligrosidad(mensaje)
    if bloqueo:
        return {
            "respuesta": "Lo siento, no puedo proporcionar ese tipo de información."
        }

    # =====================================================
    # 2️⃣ DETECTAR INTENCIÓN
    # =====================================================
    intent = detectar_intencion(mensaje)

    # =====================================================
    # 3️⃣ BUSCAR PRODUCTOS (SI APLICA)
    # =====================================================
    contexto = ""
    productos_encontrados = []

    if intent in ["precio", "stock", "producto", "recomendacion"]:
        productos_encontrados = buscar_producto_seguro(mensaje)

        if productos_encontrados:
            contexto += "🛒 **Productos disponibles:**\n\n"
            for p in productos_encontrados:
                contexto += (
                    f"- **{p['nombre']}**\n"
                    f"  💰 Precio: ${p['precio']}\n"
                    f"  📦 Stock: {p['stock']}\n"
                    f"  👉 Ver producto: {p['link']}\n\n"
                )

    # =====================================================
    # 4️⃣ PROMPT CONTROLADO (ANTI-ALUCINACIÓN)
    # =====================================================
    prompt = f"""
Eres un asistente virtual de MercadoLocal-IA.

REGLAS ESTRICTAS:
- NO inventes datos
- SOLO usa la información del CONTEXTO
- NO muestres información interna
- Si no tienes datos suficientes, dilo claramente
- Si hay productos, menciona SIEMPRE el link para ver/comprar

ROL DEL USUARIO: {rol}

CONTEXTO:
{contexto if contexto else "No hay productos relacionados."}

PREGUNTA DEL USUARIO:
{mensaje}

Responde de forma clara, breve, amigable y orientada a ayudar a comprar.
"""

    # =====================================================
    # 5️⃣ HISTORIAL
    # =====================================================
    historial = get_history(user_id)

    messages = (
        [{"role": "system", "content": "Asistente de comercio local seguro"}]
        + historial
        + [{"role": "user", "content": prompt}]
    )

    # =====================================================
    # 6️⃣ LLAMADA A OLLAMA
    # =====================================================
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": messages,
                "stream": False
            },
            timeout=30
        )
        response.raise_for_status()

        texto_respuesta = response.json()["message"]["content"]

        # =====================================================
        # 7️⃣ GUARDAR HISTORIAL
        # =====================================================
        save_message(user_id, rol, mensaje, texto_respuesta)

        return {
            "respuesta": texto_respuesta,
            "productos": productos_encontrados  # 👈 útil para frontend
        }

    except Exception as e:
        return {
            "respuesta": "Lo siento, ocurrió un error al procesar tu mensaje.",
            "error": str(e)
        }
