import os

class Settings:
    MODEL_PATH = os.path.join("models", "ml_models")
    API_VERSION = "/api/v1"

    # Database config
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "mercado_local_backend   ")
    DB_USERNAME = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

settings = Settings()
