from datetime import datetime, timedelta
from sqlalchemy import text
from core.database import SessionLocal

class DemandModel:

    def __init__(self):
        print("📊 DemandModel inteligente cargado.")

    def predict(self, product_id: int):
        """
        Demanda estimada usando ventas ponderadas por recencia (últimos 30 días)
        """

        db = SessionLocal()
        try:
            hoy = datetime.now()

            rangos = [
                (hoy - timedelta(days=7), 1.0),
                (hoy - timedelta(days=14), 0.7),
                (hoy - timedelta(days=30), 0.4)
            ]

            demanda_ponderada = 0

            for fecha, peso in rangos:
                sql = text("""
                    SELECT COALESCE(SUM(d.cantidad), 0)
                    FROM detalles_pedido d
                    JOIN pedidos p ON p.id_pedido = d.id_pedido
                    WHERE d.id_producto = :pid
                    AND p.fecha_pedido >= :fecha
                """)

                total = db.execute(
                    sql,
                    {"pid": product_id, "fecha": fecha}
                ).scalar()

                demanda_ponderada += (total or 0) * peso

            # promedio diario estimado
            demanda_mensual = int(demanda_ponderada)

            # clasificación
            if demanda_mensual >= 50:
                nivel = "ALTA"
            elif demanda_mensual >= 20:
                nivel = "MEDIA"
            else:
                nivel = "BAJA"

            return {
                "demanda_estimada_30_dias": demanda_mensual,
                "nivel_demanda": nivel,
                "modelo": "Heurístico ponderado por recencia"
            }

        finally:
            db.close()
