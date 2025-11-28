import os
import pickle
from core.config import settings
from models.training.recommender_base import PopularityRecommender



class ModelManager:

    def __init__(self):
        base = settings.MODEL_PATH  # debería ser "models/ml_models"
        self.base_path = base

        self.price_model = self.load(os.path.join(base, "price_model.pkl"))
        self.demand_model = self.load(os.path.join(base, "demand_model.pkl"))
        self.recommender_model = self.load(os.path.join(base, "recommender_model.pkl"))

    def load(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Modelo no encontrado en: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)


models = ModelManager()
