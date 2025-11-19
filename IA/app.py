from fastapi import FastAPI
from pydantic import BaseModel
from services.price_optimizer import PriceOptimizer
from services.demand_predictor import DemandPredictor
from services.product_recommender import ProductRecommender

app = FastAPI(
    title="MercadoLocal-IA Microservice",
    description="Microservicio de Inteligencia Artificial para precios, demanda y recomendaciones.",
    version="1.0.0"
)

# ===============================
# 🔹 Cargar servicios IA (TUS MODELOS)
# ===============================
price_optimizer = PriceOptimizer()
demand_predictor = DemandPredictor()
product_recommender = ProductRecommender()

# ===============================
# 🔹 MODELOS DE REQUEST ORIGINALES
# ===============================

class PriceRequest(BaseModel):
    categoria: float
    precio_actual: float
    stock: float
    ventas_historicas: float


class DemandRequest(BaseModel):
    mes: float
    ventas_pasadas: float
    tendencia: float


class RecommendationRequest(BaseModel):
    features: list


# ===============================
# 🔹 ENDPOINTS ORIGINALES (NO TOCA NADA)
# ===============================

@app.post("/predict_price")
def predict_price(request: PriceRequest):
    data = request.dict()
    resultado = price_optimizer.predict_price(data)
    return {"precio_sugerido": resultado}


@app.post("/predict_demand")
def predict_demand(request: DemandRequest):
    data = request.dict()
    resultado = demand_predictor.predict(data)
    return {"demanda_predicha": resultado}


@app.post("/recommend_products")
def recommend_products(request: RecommendationRequest):
    features = request.features
    resultado = product_recommender.recommend(features)
    return {"productos_recomendados": resultado}


# =======================================================================================
# 🔥🔥🔥 NUEVOS ENDPOINTS COMPATIBLES CON SPRING BOOT (ADAPTADORES)
# =======================================================================================

# ---------------------------------------------------------
# 1️⃣ PRECIO SUGERIDO (Versión que Spring Boot llama)
# ---------------------------------------------------------
class PrecioSugeridoSpring(BaseModel):
    idProducto: int
    precioActual: float
    costo: float
    stockActual: float
    ventasUltimos30Dias: float


@app.post("/precio-sugerido")
def precio_sugerido_spring(request: PrecioSugeridoSpring):

    # Adaptar los campos al formato esperado por tu modelo IA
    data = {
        "categoria": request.idProducto,              # si tu modelo usa categoría real, cambiar aquí
        "precio_actual": request.precioActual,
        "stock": request.stockActual,
        "ventas_historicas": request.ventasUltimos30Dias
    }

    precio = price_optimizer.predict_price(data)

    return {
        "idProducto": request.idProducto,
        "precioSugerido": round(precio, 2),
        "explicacion": "Predicción generada con modelo price_model.pkl"
    }


# ---------------------------------------------------------
# 2️⃣ PREDICCIÓN DE DEMANDA (Versión que Spring Boot llama)
# ---------------------------------------------------------
class DemandaSpring(BaseModel):
    idProducto: int
    horizonteDias: float
    ventasUltimos30Dias: float
    stockActual: float


@app.post("/prediccion-demanda")
def prediccion_demanda_spring(request: DemandaSpring):

    data = {
        "mes": request.horizonteDias,           # en tu modelo X_demand son 3 columnas: mes, ventas_pasadas, tendencia
        "ventas_pasadas": request.ventasUltimos30Dias,
        "tendencia": 1.0                         # valor por defecto
    }

    demanda = demand_predictor.predict(data)

    recomendacion = "Comprar más stock" if demanda > request.stockActual else "Stock suficiente"

    return {
        "idProducto": request.idProducto,
        "horizonteDias": request.horizonteDias,
        "demandaEsperada": round(demanda, 2),
        "recomendacion": recomendacion
    }


# ===============================
# 🔹 ENDPOINT DE PRUEBA
# ===============================
@app.get("/")
def home():
    return {"message": "Microservicio IA funcionando correctamente 🚀"}