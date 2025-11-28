import os
import pickle

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from models.training.recommender_base import PopularityRecommender



# ============================
# Rutas de guardado de modelos
# ============================

# Este archivo está en: IA/models/training/train_models.py
# Vamos a dejar los modelos en: IA/models/ml_models/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # IA/models
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================
# 1. Modelo de PRECIOS
# ============================

def train_price_model():
    rng = np.random.default_rng(42)

    n_products = 300
    product_ids = np.arange(1, n_products + 1)

    # Precio base entre 0.3 y 15
    current_price = rng.uniform(0.3, 15.0, size=n_products)

    # Stock entre 20 y 600
    stock = rng.integers(20, 600, size=n_products)

    # Ventas históricas inversamente proporcionales al precio
    historical_sales = (1000 / current_price) + rng.normal(0, 30, size=n_products)
    historical_sales = np.clip(historical_sales, 5, None).astype(int)

    # "Precio recomendado" simulado como el precio base +/- un pequeño factor
    recommended_price = current_price * rng.uniform(0.8, 1.3, size=n_products)

    # Las columnas deben coincidir con lo que enviará el backend:
    # product_id, current_price, historical_sales, stock
    X_price = pd.DataFrame({
        "product_id": product_ids,
        "current_price": current_price,
        "historical_sales": historical_sales,
        "stock": stock
    })

    y_price = recommended_price

    model = LinearRegression()
    model.fit(X_price, y_price)

    path = os.path.join(MODEL_DIR, "price_model.pkl")
    with open(path, "wb") as f:
        pickle.dump(model, f)

    print(f"[OK] price_model entrenado y guardado en: {path}")
    # Devolvemos info útil para otros modelos
    return X_price, y_price


# ============================
# 2. Modelo de DEMANDA
# ============================

def train_demand_model():
    rng = np.random.default_rng(123)

    n_samples = 2000

    product_ids = rng.integers(1, 301, size=n_samples)
    current_price = rng.uniform(0.3, 15.0, size=n_samples)
    stock = rng.integers(0, 800, size=n_samples)
    month = rng.integers(1, 13, size=n_samples)       # 1–12
    day_of_week = rng.integers(0, 7, size=n_samples)  # 0=lunes ... 6=domingo

    # Demanda base inversa al precio
    base_demand = (2000 / current_price) + rng.normal(0, 50, size=n_samples)

    # Estacionalidad: más demanda en meses 12, 1, 4
    season_boost = np.where(np.isin(month, [12, 1, 4]), 1.3, 1.0)

    # Más demanda entre semana que fin de semana (0–4 vs 5–6)
    dow_boost = np.where(day_of_week < 5, 1.1, 0.9)

    demand = base_demand * season_boost * dow_boost
    demand = np.clip(demand, 0, None).astype(int)

    X_demand = pd.DataFrame({
        "product_id": product_ids,
        "current_price": current_price,
        "stock": stock,
        "month": month,
        "day_of_week": day_of_week
    })

    y_demand = demand

    model = RandomForestRegressor(
        n_estimators=80,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_demand, y_demand)

    path = os.path.join(MODEL_DIR, "demand_model.pkl")
    with open(path, "wb") as f:
        pickle.dump(model, f)

    print(f"[OK] demand_model entrenado y guardado en: {path}")


# ============================
# 3. Modelo RECOMENDADOR
# ============================

def train_recommender_model(price_training_df: pd.DataFrame):
    # Usamos historical_sales como proxy de popularidad
    ranking = price_training_df.sort_values(
        "historical_sales", ascending=False
    )["product_id"].tolist()

    model = PopularityRecommender(ranking)

    path = os.path.join(MODEL_DIR, "recommender_model.pkl")
    with open(path, "wb") as f:
        pickle.dump(model, f)

    print(f"[OK] recommender_model entrenado y guardado en: {path}")


# ============================
# MAIN
# ============================

if __name__ == "__main__":
    print("Entrenando modelos de IA con datos simulados realistas...")

    # 1) Precio -> usamos el DF también para el recomendador
    price_df, _ = train_price_model()

    # 2) Demanda
    train_demand_model()

    # 3) Recomendador
    train_recommender_model(price_df)

    print("\n✅ TODOS LOS MODELOS HAN SIDO ENTRENADOS Y GUARDADOS.")
    print(f"Carpeta de modelos: {MODEL_DIR}")
