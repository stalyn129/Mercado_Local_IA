import pickle
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import NearestNeighbors

# Crear carpeta models si no existe
os.makedirs("models", exist_ok=True)

print("Generando modelos IA...\n")

# ================================
# 1. Modelo de PRECIO
# ================================
print("📌 Generando price_model.pkl")

X_price = np.random.rand(400, 4)
y_price = np.random.rand(400) * 20

price_model = RandomForestRegressor(n_estimators=80)
price_model.fit(X_price, y_price)

with open("models/price_model.pkl", "wb") as f:
    pickle.dump(price_model, f)


# ================================
# 2. Modelo de DEMANDA
# ================================
print("📌 Generando demand_model.pkl")

X_demand = np.random.rand(400, 3)
y_demand = np.random.randint(10, 200, size=400)

demand_model = RandomForestRegressor(n_estimators=80)
demand_model.fit(X_demand, y_demand)

with open("models/demand_model.pkl", "wb") as f:
    pickle.dump(demand_model, f)


# ================================
# 3. Modelo de RECOMENDACIÓN
# ================================
print("📌 Generando recommender_model.pkl")

X_rec = np.random.rand(200, 5)

recommender_model = NearestNeighbors(n_neighbors=5, algorithm='auto')
recommender_model.fit(X_rec)

with open("models/recommender_model.pkl", "wb") as f:
    pickle.dump(recommender_model, f)


print("\n✅ Modelos generados correctamente.")
print("Revisa la carpeta 'models/' para verificar los .pkl.\n")
