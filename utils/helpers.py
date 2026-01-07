import re
from datetime import datetime

def clean_text(text: str) -> str:
    """
    Limpia el texto de entrada del usuario (emojis, espacios extra) 
    para que la IA lo procese mejor.
    """
    # Elimina caracteres especiales y espacios múltiples
    text = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ]', '', text)
    return " ".join(text.split())

def format_currency(value: float) -> str:
    """
    Da formato de moneda a los precios sugeridos por el modelo de IA (RF-06).
    """
    return f"${value:,.2f}"

def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Calcula la tendencia de demanda para el demand_predictor.py (RF-07).
    """
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)

def get_current_season() -> str:
    """
    Identifica la temporada actual para ayudar al modelo de predicción de demanda.
    """
    month = datetime.now().month
    if month in [12, 1, 2]: return "Invierno/Navidad"
    if month in [3, 4, 5]: return "Primavera/Semana Santa"
    if month in [6, 7, 8]: return "Verano/Vacaciones"
    return "Otoño/Cosecha"

def validate_ruc(ruc: str) -> bool:
    """
    Valida el formato del RUC para el registro de vendedores (RF-01).
    """
    # Validación básica de longitud para Ecuador (13 dígitos)
    return len(ruc) == 13 and ruc.isdigit()