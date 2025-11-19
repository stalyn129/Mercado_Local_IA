import pickle
import pandas as pd

class PriceOptimizer:

    def __init__(self):
        # Cargar modelo entrenado
        self.model = pickle.load(open("models/price_model.pkl", "rb"))

    def predict_price(self, data: dict):
        # Convertir datos a DataFrame
        df = pd.DataFrame([data])

        # Realizar predicción
        prediction = self.model.predict(df)

        return float(prediction[0])
