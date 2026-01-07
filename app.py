import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importación de configuraciones y rutas
from core.config import settings
from core.database import engine, Base
from api.routes import auth_routes, inventory_routes, chat_routes, order_routes

# Crear las tablas en MariaDB si no existen
# Nota: Esto usa las definiciones de db_models.py
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.PROJECT_VERSION
)

# --- CONFIGURACIÓN DE CORS ---
# Permite que tu Frontend (React, Vue, etc.) se comunique con esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRO DE RUTAS (ENDPOINTS) ---
# RF-01: Autenticación y Perfiles
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Autenticación"])

# RF-02: Gestión de Inventario para Vendedores
app.include_router(inventory_routes.router, prefix="/api/inventory", tags=["Inventario"])

# RF-04 y RF-05: Gestión de Pedidos y Ventas
app.include_router(order_routes.router, prefix="/api/orders", tags=["Pedidos"])

# RF-06 y RF-07: Chatbot con IA (Análisis y Recomendación)
app.include_router(chat_routes.router, prefix="/api/ia", tags=["Inteligencia Artificial"])

@app.get("/")
async def root():
    return {
        "message": "Bienvenido a la API de MercadoLocal-IA",
        "status": "Online",
        "docs": "/docs"
    }

# --- INICIO DEL SERVIDOR ---
if __name__ == "__main__":
    # Ejecuta el servidor en el puerto 8000
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)