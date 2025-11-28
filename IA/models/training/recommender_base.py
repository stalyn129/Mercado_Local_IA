class PopularityRecommender:
    """
    Recomendador basado en popularidad (ventas simuladas).
    Se carga siempre que el modelo .pkl lo use.
    """

    def __init__(self, ranking_product_ids):
        self.ranking = list(ranking_product_ids)

    def recommend(self, user_id: int, limit: int = 5):
        return self.ranking[:limit]