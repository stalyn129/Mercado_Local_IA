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
# 🔹 Cargar servicios IA
# ===============================
price_optimizer = PriceOptimizer()
demand_predictor = DemandPredictor()
product_recommender = ProductRecommender()

# ===============================
# 🔹 MODELOS DE REQUEST
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
# 🔹 ENDPOINT: Optimización de precios
# ===============================
@app.post("/predict_price")
def predict_price(request: PriceRequest):
    data = request.dict()
    resultado = price_optimizer.predict_price(data)
    return {"precio_sugerido": resultado}


# ===============================
# 🔹 ENDPOINT: Predicción de demanda
# ===============================
@app.post("/predict_demand")
def predict_demand(request: DemandRequest):
    data = request.dict()
    resultado = demand_predictor.predict(data)
    return {"demanda_predicha": resultado}


# ===============================
# 🔹 ENDPOINT: Recomendación de productos
# ===============================
@app.post("/recommend_products")
def recommend_products(request: RecommendationRequest):
    features = request.features
    resultado = product_recommender.recommend(features)
    return {"productos_recomendados": resultado}


# ===============================
# 🔹 ENDPOINT DE PRUEBA
# ===============================
@app.get("/")
def home():
    return {"message": "Microservicio IA funcionando correctamente 🚀"}
