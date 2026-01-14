from fastapi import APIRouter, Body
from services.price_recommender import recomendar_precio

router = APIRouter()

@router.post("/precio/recomendar")
async def api_recomendar_precio(payload: dict = Body(...)):
    nombre = payload.get("nombre")
    precio = payload.get("precio")
    # Llamamos a tu lógica de price_recommender.py
    return recomendar_precio(nombre, precio)