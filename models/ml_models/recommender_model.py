from sqlalchemy import text
from datetime import datetime, timedelta
from core.database import SessionLocal

class RecommenderModel:

    def __init__(self):
        print("🛒 RecommenderModel inteligente cargado.")

    def recommend(self, user_id: int):
        """
        Recomendador heurístico:
        - Personalizado si hay historial
        - Pondera recencia
        - Fallback global
        - Solo productos activos y con stock
        """

        db = SessionLocal()
        try:
            hace_30_dias = datetime.now() - timedelta(days=30)

            # =========================
            # 1️⃣ PERSONALIZADO (RECENCIA + FRECUENCIA)
            # =========================
            sql_user = text("""
                SELECT 
                    p.id_producto,
                    p.nombre_producto,
                    COUNT(*) AS frecuencia,
                    MAX(ped.fecha_pedido) AS ultima_compra
                FROM detalles_pedido d
                JOIN pedidos ped ON ped.id_pedido = d.id_pedido
                JOIN productos p ON p.id_producto = d.id_producto
                WHERE ped.id_consumidor = :uid
                  AND p.estado = 'ACTIVO'
                  AND p.stock_producto > 0
                GROUP BY p.id_producto, p.nombre_producto
                ORDER BY ultima_compra DESC, frecuencia DESC
                LIMIT 8
            """)

            rows = db.execute(sql_user, {"uid": user_id}).fetchall()

            if rows:
                recomendaciones = []
                for r in rows:
                    score = r.frecuencia
                    recomendaciones.append({
                        "nombre": r.nombre_producto,
                        "score": score,
                        "motivo": "Basado en tus compras recientes"
                    })

                return {
                    "tipo": "personalizado",
                    "recomendaciones": recomendaciones
                }

            # =========================
            # 2️⃣ GLOBAL (POPULARIDAD)
            # =========================
            sql_global = text("""
                SELECT 
                    p.nombre_producto,
                    COUNT(*) AS ventas
                FROM detalles_pedido d
                JOIN productos p ON p.id_producto = d.id_producto
                WHERE p.estado = 'ACTIVO'
                  AND p.stock_producto > 0
                GROUP BY p.nombre_producto
                ORDER BY ventas DESC
                LIMIT 8
            """)

            global_rows = db.execute(sql_global).fetchall()

            return {
                "tipo": "global",
                "recomendaciones": [
                    {
                        "nombre": r.nombre_producto,
                        "score": int(r.ventas),
                        "motivo": "Producto popular entre los usuarios"
                    }
                    for r in global_rows
                ]
            }

        finally:
            db.close()
