from fastapi import APIRouter, Body
from services.price_recommender import recomendar_precio

router = APIRouter()

@router.post("/precio/recomendar")
async def api_recomendar_precio(payload: dict = Body(...)):
    nombre = payload.get("nombre")
    precio = payload.get("precio")
    unidad = payload.get("unidad", "unidad")  # 🔹 Nuevo: recibir unidad
    
    # Validar parámetros
    if not nombre:
        return {"error": "El nombre es requerido"}
    
    try:
        precio_float = float(precio) if precio else 0
    except ValueError:
        return {"error": "Precio inválido"}
    
    # 🔹 Llamar a la función actualizada con unidad
    return recomendar_precio(nombre, precio_float, unidad)