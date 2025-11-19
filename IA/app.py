from fastapi import FastAPI
from pydantic import BaseModel
from services.price_optimizer import PriceOptimizer
from services.demand_predictor import DemandPredictor
from services.product_recommender import ProductRecommender

app = FastAPI(
    title="MercadoLocal-IA Microservice",
    description="Microservicio de Inteligencia Artificial compatible 100% con Spring Boot.",
    version="2.0.0"
)

# ===============================
# 🔹 Cargar tus modelos IA reales
# ===============================
price_optimizer = PriceOptimizer()
demand_predictor = DemandPredictor()
product_recommender = ProductRecommender()

# ===============================
# 🔹 MODELOS COMPATIBLES CON SPRING BOOT
# ===============================

class PrecioSugeridoSpring(BaseModel):
    idProducto: int
    precioActual: float
    costo: float
    stockActual: float
    ventasUltimos30Dias: float


class DemandaSpring(BaseModel):
    idProducto: int
    horizonteDias: float
    ventasUltimos30Dias: float
    stockActual: float


# ===============================
# 🔥🔥🔥 ENDPOINT: PRECIO SUGERIDO (Mismo DTO que Spring)
# ===============================
@app.post("/precio-sugerido")
def precio_sugerido_spring(request: PrecioSugeridoSpring):

    # Adaptar tu formato → a lo que tu modelo IA espera
    data = {
        "categoria": request.idProducto,     # campo adaptado
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


# ===============================
# 🔥🔥🔥 ENDPOINT: DEMANDA (Mismo DTO que Spring)
# ===============================
@app.post("/prediccion-demanda")
def prediccion_demanda_spring(request: DemandaSpring):

    data = {
        "mes": request.horizonteDias,
        "ventas_pasadas": request.ventasUltimos30Dias,
        "tendencia": 1.0     # Valor por defecto para tu modelo
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
# 🔹 Tus ENDPOINTS ORIGINALES (NO se tocaron)
# ===============================
class PriceRequest(BaseModel):
    categoria: float
    precio_actual: float
    stock: float
    ventas_historicas: float


@app.post("/predict_price")
def predict_price(request: PriceRequest):
    data = request.dict()
    return {"precio_sugerido": price_optimizer.predict_price(data)}


class DemandRequest(BaseModel):
    mes: float
    ventas_pasadas: float
    tendencia: float


@app.post("/predict_demand")
def predict_demand(request: DemandRequest):
    data = request.dict()
    return {"demanda_predicha": demand_predictor.predict(data)}


class RecommendationRequest(BaseModel):
    features: list


@app.post("/recommend_products")
def recommend_products(request: RecommendationRequest):
    return {"productos_recomendados": product_recommender.recommend(request.features)}


# ===============================
# 🔹 ENDPOINT raíz
# ===============================
@app.get("/")
def home():
    return {"message": "Microservicio IA funcionando correctamente"}