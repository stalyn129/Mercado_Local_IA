import joblib

class PriceModel:
    def __init__(self):
        try:
            # Aquí cargarás tu archivo entrenado
            self.model = joblib.load("data/price_model.pkl")
        except:
            self.model = None

    def suggest_price(self, base_price, category_avg):
        if not self.model:
            # Lógica simple si el modelo no está cargado
            return round((base_price + category_avg) / 2, 2)
        return self.model.predict([[base_price, category_avg]])[0]