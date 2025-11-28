from models.training.model_manager import models

class RecommenderService:

    def recommend(self, user_id: int, limit: int = 5):
        result = models.recommender_model.recommend(user_id, limit)
        return result
