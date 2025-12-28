from fastapi import APIRouter
from pydantic import BaseModel

from models.ml_models.price_model import PriceModel
from models.ml_models.demand_model import DemandModel
from models.ml_models.recommender_model import RecommenderModel

from services.chatbot import ask_chatbot
from services.price_recommender import recomendar_precio

router = APIRouter()

# Instancias de modelos de ML
precio_model = PriceModel()
demanda_model = DemandModel()
recomender_model = RecommenderModel()

class ChatRequest(BaseModel):
    id_usuario: int
    rol: str
    mensaje: str


@router.get("/precio/{id_producto}")
def precio(id_producto: int):
    return precio_model.predict(id_producto)


@router.get("/demanda/{id_producto}")
def demanda(id_producto: int):
    return demanda_model.predict(id_producto)


@router.get("/recomendar/{id_consumidor}")
def recomendar(id_consumidor: int):
    return recomender_model.recommend(id_consumidor)


@router.post("/chat")
def chat(req: ChatRequest):
    return ask_chatbot(
        user_id=req.id_usuario,
        rol=req.rol,
        mensaje=req.mensaje
    )
    


class PrecioRequest(BaseModel):
    nombre: str
    precio: float


@router.post("/precio/recomendar")
def recomendar_precio_endpoint(req: PrecioRequest):
    return recomendar_precio(
        req.nombre,
        req.precio
    )
