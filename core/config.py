import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

class Settings:
    PROJECT_NAME: str = "MercadoLocal-IA"
    PROJECT_VERSION: str = "1.0.0"

    # Configuración de Base de Datos (MariaDB)
    # Se recomienda usar variables de entorno para mayor seguridad
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "mercado_local_ia")
    
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Configuración de IA (Ollama)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3") # o el modelo que prefieras

    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-para-tokens")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

    # CORS: Permite que tu frontend acceda a la API
    # En desarrollo puedes usar ["*"], en producción especifica la URL del front
    ALLOWED_ORIGINS = [
        "http://localhost:3000", # React/Next.js
        "http://127.0.0.1:5500", # Live Server VS Code
        "*", 
    ]

settings = Settings()