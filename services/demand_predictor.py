from sqlalchemy.orm import Session
from sqlalchemy import func
from models.db_models import DetallesPedido, Producto, Pedido
import datetime

class DemandPredictor:
    def __init__(self, db: Session):
        self.db = db

    def predict_demand(self, id_producto: int):
        """
        Analiza las ventas de los últimos 30 días para predecir la demanda futura.
        """
        hace_un_mes = datetime.datetime.now() - datetime.timedelta(days=30)
        
        # Sumar cantidades vendidas del producto en el último mes
        total_vendido = self.db.query(func.sum(DetallesPedido.cantidad))\
            .join(Pedido)\
            .filter(DetallesPedido.id_producto == id_producto)\
            .filter(Pedido.fecha_pedido >= hace_un_mes)\
            .scalar() or 0

        # Lógica de clasificación (RF-07)
        if total_vendido > 50:
            return {"nivel": "ALTA", "mensaje": "Se recomienda aumentar el stock para evitar quiebres."}
        elif total_vendido > 20:
            return {"nivel": "MEDIA", "mensaje": "La demanda es estable. Mantén tu stock actual."}
        else:
            return {"nivel": "BAJA", "mensaje": "Considera una promoción para rotar este producto."}

    def get_seasonal_boost(self):
        """
        Analiza si estamos cerca de festivos según el calendario (Opcional para el predictor).
        """
        hoy = datetime.datetime.now()
        # Ejemplo: Navidad o Feriados locales detectados por fecha
        if hoy.month == 12:
            return 1.5 # Incremento del 50% en la demanda estimada
        return 1.0