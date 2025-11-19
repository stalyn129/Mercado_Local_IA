import pickle
import pandas as pd

class DemandPredictor:

    def __init__(self):
        # Cargar modelo pre-entrenado para demanda
        self.model = pickle.load(open("models/demand_model.pkl", "rb"))

    def predict(self, data: dict):
        # Convertir JSON a DataFrame
        df = pd.DataFrame([data])

        result = self.model.predict(df)

        return float(result[0])
