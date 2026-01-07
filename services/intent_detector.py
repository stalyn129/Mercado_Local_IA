class IntentDetector:
    def detect(self, message: str):
        msg = message.lower()
        if any(w in msg for w in ["precio", "sugerencia", "vender"]):
            return "ANALISIS_PRECIO"
        if any(w in msg for w in ["demanda", "cuanto", "ventas"]):
            return "PREDICCION_DEMANDA"
        if any(w in msg for w in ["comprar", "buscar", "recomienda"]):
            return "RECOMENDACION_COMPRA"
        return "CHAT_GENERAL"