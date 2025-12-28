from sqlalchemy import text
from core.database import SessionLocal
from utils.text_normalizer import extraer_palabras_clave

def recomendar_precio(nombre: str, precio_ingresado: float):
    db = SessionLocal()
    try:
        palabras = extraer_palabras_clave(nombre)

        if not palabras:
            return {
                "similar_found": False,
                "message": "Nombre de producto demasiado ambiguo.",
                "precio_ingresado": precio_ingresado
            }

        # 🔹 construir condiciones LIKE dinámicas (todas las palabras deben coincidir)
        condiciones = " AND ".join(
            [f"LOWER(nombre_producto) LIKE :p{i}" for i in range(len(palabras))]
        )

        sql = text(f"""
            SELECT nombre_producto, precio_producto
            FROM productos
            WHERE {condiciones}
              AND estado = 'ACTIVO'
            LIMIT 10
        """)

        params = {
            f"p{i}": f"%{palabras[i]}%"
            for i in range(len(palabras))
        }

        rows = db.execute(sql, params).fetchall()

        if not rows:
            return {
                "similar_found": False,
                "message": "No se encontraron productos similares.",
                "precio_ingresado": precio_ingresado
            }

        # 🔹 precios reales
        precios = sorted(float(r[1]) for r in rows)

        # 🔹 usar mediana si hay muchos valores (más robusto)
        if len(precios) >= 5:
            medio = len(precios) // 2
            promedio = precios[medio]
        else:
            promedio = sum(precios) / len(precios)

        diferencia = precio_ingresado - promedio
        porcentaje = diferencia / promedio

        if porcentaje <= -0.15:
            estado = "BAJO"
        elif porcentaje >= 0.15:
            estado = "ALTO"
        else:
            estado = "ADECUADO"

        return {
            "similar_found": True,
            "productos_similares": [
                {
                    "nombre": r[0],
                    "precio": round(float(r[1]), 2)
                }
                for r in rows
            ],
            "precio_referencia": round(promedio, 2),
            "precio_ingresado": round(precio_ingresado, 2),
            "estado": estado,
            "recomendado": round(promedio, 2),
            "criterio": "comparación con productos similares del mercado"
        }

    finally:
        db.close()
