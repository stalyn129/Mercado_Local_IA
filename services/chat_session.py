from sqlalchemy import text
from core.database import SessionLocal

MAX_MSG_LENGTH = 500     # seguridad básica
MAX_HISTORY_PAIRS = 6   # 6 preguntas + 6 respuestas = buen contexto


def _limpiar_texto(texto: str) -> str:
    """Limpieza básica para evitar basura"""
    if not texto:
        return ""
    return texto.strip()[:MAX_MSG_LENGTH]


def save_message(user_id: int, rol: str, mensaje: str, respuesta: str):
    db = SessionLocal()
    try:
        sql = text("""
            INSERT INTO chat_historial (
                id_usuario,
                rol,
                mensaje_usuario,
                respuesta_ia
            )
            VALUES (:uid, :rol, :msg, :resp)
        """)

        db.execute(sql, {
            "uid": user_id,
            "rol": rol,
            "msg": _limpiar_texto(mensaje),
            "resp": _limpiar_texto(respuesta)
        })

        db.commit()

    finally:
        db.close()


def get_history(user_id: int):
    """
    Devuelve historial listo para Ollama/OpenAI:
    [
      {role: user, content: ...},
      {role: assistant, content: ...}
    ]
    """

    db = SessionLocal()
    try:
        sql = text("""
            SELECT mensaje_usuario, respuesta_ia
            FROM chat_historial
            WHERE id_usuario = :uid
            ORDER BY fecha DESC
            LIMIT :lim
        """)

        rows = db.execute(sql, {
            "uid": user_id,
            "lim": MAX_HISTORY_PAIRS
        }).fetchall()

        # invertir para mantener orden cronológico
        rows.reverse()

        history = []
        for m, r in rows:
            history.append({
                "role": "user",
                "content": m
            })
            history.append({
                "role": "assistant",
                "content": r
            })

        return history

    finally:
        db.close()
