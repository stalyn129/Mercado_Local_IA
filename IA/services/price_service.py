from sqlalchemy.orm import Session
from sqlalchemy import text
from models.training.model_manager import models
import pandas as pd


PRICE_FEATURES = ["product_id", "current_price", "historical_sales", "stock"]


class PriceService:

    def predict(self, data: dict):
        df = pd.DataFrame([data])[PRICE_FEATURES]
        result = models.price_model.predict(df)
        return float(result[0])

    def predict_from_db(self, db: Session, product_id: int):

        # ============================
        # 1. Obtener producto
        # ============================
        producto = db.execute(
            text(
                "SELECT id_producto, precio_producto, stock_producto "
                "FROM productos WHERE id_producto = :id"
            ),
            {"id": product_id}
        ).fetchone()

        if not producto:
            return {"error": "Producto no encontrado"}

        current_price = float(producto.precio_producto)
        stock = int(producto.stock_producto)

        # ============================
        # 2. Obtener ventas históricas
        # ============================
        ventas = db.execute(
            text(
                """
                SELECT SUM(dp.cantidad)
                FROM detalles_pedido dp
                WHERE dp.id_producto = :id
                """
            ),
            {"id": product_id}
        ).fetchone()

        historical_sales = ventas[0] if ventas[0] is not None else 0

        # ============================
        # 3. Preparar datos del modelo
        # ============================
        data = {
            "product_id": product_id,
            "current_price": current_price,
            "historical_sales": int(historical_sales),
            "stock": stock
        }

        df = pd.DataFrame([data])[PRICE_FEATURES]
        result = models.price_model.predict(df)

        return {
            "product_id": product_id,
            "recommended_price": float(result[0]),
            "current_price": current_price,
            "stock": stock,
            "historical_sales": historical_sales
        }


price_service = PriceService()
