from sqlalchemy import text
from core.database import SessionLocal
from utils.text_normalizer import extraer_palabras_clave
import unicodedata


# 🔹 Normaliza texto: sin acentos, minúsculas
def normalizar(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()


def recomendar_precio(nombre: str, precio_ingresado: float):
    db = SessionLocal()
    try:
        # 🔹 extraer y normalizar palabras clave
        palabras_raw = extraer_palabras_clave(nombre)
        palabras = [normalizar(p) for p in palabras_raw if len(p) >= 3]

        if not palabras:
            return {
                "similar_found": False,
                "message": "Nombre de producto demasiado ambiguo.",
                "precio_ingresado": round(precio_ingresado, 2)
            }

        # 🔹 condiciones OR (flexible)
        condiciones = " OR ".join(
            [f"LOWER(nombre_producto) LIKE :p{i}" for i in range(len(palabras))]
        )

        sql = text(f"""
            SELECT nombre_producto, precio_producto
            FROM productos
            WHERE ({condiciones})
              AND estado = 'Disponible'
            LIMIT 20
        """)

        params = {
            f"p{i}": f"%{palabras[i]}%"
            for i in range(len(palabras))
        }

        rows = db.execute(sql, params).fetchall()

        # 🔹 si no hubo match directo → fallback más amplio
        if not rows:
            sql_fallback = text("""
                SELECT nombre_producto, precio_producto
                FROM productos
                WHERE estado = 'ACTIVO'
                LIMIT 10
            """)
            rows = db.execute(sql_fallback).fetchall()

            if not rows:
                return {
                    "similar_found": False,
                    "message": "No se encontraron productos similares.",
                    "precio_ingresado": round(precio_ingresado, 2)
                }

        # 🔹 ranking por cantidad de palabras coincidentes
        def score(nombre_producto):
            nombre_norm = normalizar(nombre_producto)
            return sum(1 for p in palabras if p in nombre_norm)

        rows = sorted(rows, key=lambda r: score(r[0]), reverse=True)

        # 🔹 tomar los mejores
        top_rows = rows[:10]

        precios = sorted(float(r[1]) for r in top_rows if r[1] is not None)

        if not precios:
            return {
                "similar_found": False,
                "message": "Productos encontrados sin precio válido.",
                "precio_ingresado": round(precio_ingresado, 2)
            }

        # 🔹 mediana si hay suficientes datos
        if len(precios) >= 5:
            mid = len(precios) // 2
            precio_referencia = precios[mid]
        else:
            precio_referencia = sum(precios) / len(precios)

        diferencia = precio_ingresado - precio_referencia
        porcentaje = diferencia / precio_referencia

        if porcentaje <= -0.15:
            estado = "bajo"
        elif porcentaje >= 0.15:
            estado = "alto"
        else:
            estado = "adecuado"

        return {
            "similar_found": True,
            "productos_similares": [
                {
                    "nombre": r[0],
                    "precio": round(float(r[1]), 2)
                }
                for r in top_rows
            ],
            "precio_promedio": round(precio_referencia, 2),
            "precio_ingresado": round(precio_ingresado, 2),
            "estado": estado,
            "recomendado": round(precio_referencia, 2)
        }

    finally:
        db.close()
