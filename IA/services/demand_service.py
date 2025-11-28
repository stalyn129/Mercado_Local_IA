from models.training.model_manager import models
import pandas as pd

class DemandService:

    def forecast(self, data: dict):
        df = pd.DataFrame([data])
        result = models.demand_model.predict(df)
        return float(result[0])
