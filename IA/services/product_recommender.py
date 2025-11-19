import pickle
import numpy as np

class ProductRecommender:

    def __init__(self):
        # Cargar modelo de recomendación (KNN)
        self.model = pickle.load(open("models/recommender_model.pkl", "rb"))

    def recommend(self, features: list):
        """
        features: lista de valores que representan al usuario o producto.
        Ejemplo: [edad_usuario, categoria_preferida, calificacion_promedio, ...]
        """
        distances, indices = self.model.kneighbors([features])

        # indices[0] contiene los 5 productos recomendados
        return indices[0].tolist()
