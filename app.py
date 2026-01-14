import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importación de configuraciones y base de datos
from core.config import settings
from core.database import engine, Base

# Importación de rutas existentes
from api.routes import auth_routes, inventory_routes, chat_routes, order_routes, ia_routes

# Crear las tablas en la base de datos si no existen
# Esto asegura que 'productos' esté disponible para la IA
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.PROJECT_VERSION
)

# --- CONFIGURACIÓN DE CORS ---
# Crucial para que React y Spring Boot puedan consultar este microservicio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En desarrollo puedes usar settings.ALLOWED_ORIGINS
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

# RF-06 y RF-07: Módulo de IA - Recomendación de Precios y Predicciones
# Este es el router que tu IAClientService en Java está buscando
app.include_router(ia_routes.router, prefix="/api/ia", tags=["IA - Precios"])

# Chatbot con IA
app.include_router(chat_routes.router, prefix="/api/chat", tags=["IA - Chatbot"])

@app.get("/")
async def root():
    return {
        "message": "Bienvenido a la API de MercadoLocal-IA",
        "status": "Online",
        "docs": "/docs"
    }

# --- INICIO DEL SERVIDOR ---
if __name__ == "__main__":
    # Se ejecuta en el puerto 8000 para coincidir con la IA_URL de tu Java
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)