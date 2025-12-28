from sqlalchemy import text
from core.database import SessionLocal
from models.ml_models.demand_model import DemandModel

class PriceModel:

    def __init__(self):
        self.demand_model = DemandModel()
        print("💰 PriceModel inteligente cargado.")

    def predict(self, product_id: int):
        """
        Modelo heurístico de recomendación de precio:
        - Promedio de ventas recientes
        - Ajuste por tendencia
        - Ajuste por demanda
        - Límites de seguridad
        """

        db = SessionLocal()
        try:
            # =========================
            # 1️⃣ PRECIOS DE VENTAS RECIENTES
            # =========================
            sql = text("""
                SELECT precio_unitario
                FROM detalles_pedido
                WHERE id_producto = :pid
                ORDER BY id_detalle DESC
                LIMIT 15
            """)
            rows = db.execute(sql, {"pid": product_id}).fetchall()
            precios = [float(r[0]) for r in rows]

            # =========================
            # 2️⃣ PRECIO BASE
            # =========================
            if precios:
                precio_base = sum(precios) / len(precios)

                # tendencia simple
                if len(precios) >= 5:
                    tendencia = (precios[0] - precios[-1]) / precios[-1]
                else:
                    tendencia = 0

            else:
                # sin ventas → precio actual del producto
                sql2 = text("""
                    SELECT precio_producto
                    FROM productos
                    WHERE id_producto = :pid
                """)
                row = db.execute(sql2, {"pid": product_id}).fetchone()

                if not row:
                    return {
                        "precio_recomendado": 0.0,
                        "mensaje": "Producto no encontrado"
                    }

                precio_base = float(row[0])
                tendencia = 0

            # =========================
            # 3️⃣ AJUSTE POR DEMANDA
            # =========================
            demanda = self.demand_model.predict(product_id)
            nivel_demanda = demanda.get("nivel_demanda", "MEDIA")

            ajuste_demanda = {
                "ALTA": 0.08,
                "MEDIA": 0.03,
                "BAJA": -0.05
            }.get(nivel_demanda, 0)

            # =========================
            # 4️⃣ PRECIO FINAL
            # =========================
            precio_recomendado = precio_base * (1 + tendencia + ajuste_demanda)

            # =========================
            # 5️⃣ LÍMITES DE SEGURIDAD
            # =========================
            min_price = precio_base * 0.85
            max_price = precio_base * 1.20

            precio_recomendado = max(
                min(precio_recomendado, max_price),
                min_price
            )

            return {
                "precio_recomendado": round(precio_recomendado, 2),
                "precio_base": round(precio_base, 2),
                "tendencia": round(tendencia * 100, 2),
                "nivel_demanda": nivel_demanda,
                "modelo": "Heurístico con tendencia y demanda"
            }

        finally:
            db.close()
