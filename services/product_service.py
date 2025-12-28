from sqlalchemy import text
from core.database import SessionLocal
from utils.text_normalizer import extraer_palabras_clave

FRONT_BASE = "http://localhost:5173/producto/"

def buscar_producto_seguro(nombre: str):
    db = SessionLocal()
    try:
        palabras = extraer_palabras_clave(nombre)

        if not palabras:
            return []

        # construir condiciones dinámicas
        condiciones = " AND ".join(
            [f"LOWER(nombre_producto) LIKE :p{i}" for i in range(len(palabras))]
        )

        sql = text(f"""
            SELECT 
                id_producto,
                nombre_producto,
                precio_producto,
                stock_producto
            FROM productos
            WHERE {condiciones}
              AND estado = 'ACTIVO'
              AND stock_producto > 0
            LIMIT 5
        """)

        params = {
            f"p{i}": f"%{palabras[i]}%"
            for i in range(len(palabras))
        }

        rows = db.execute(sql, params).fetchall()

        return [
            {
                "nombre": r.nombre_producto,
                "precio": round(float(r.precio_producto), 2),
                "stock": r.stock_producto,
                "link": FRONT_BASE + str(r.id_producto)
            }
            for r in rows
        ]

    finally:
        db.close()
