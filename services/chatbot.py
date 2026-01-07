from models.db_models import Producto # Importamos el modelo de tu DB
from sqlalchemy.orm import Session
from services.ollama_service import OllamaService

class ChatbotService:
    def __init__(self, db: Session):
        self.ai = OllamaService()
        self.db = db

    async def handle_request(self, message: str, id_rol: int, id_usuario: int):
        # 1. BUSCAR DATOS REALES DE TU BASE DE DATOS
        # Vamos a traer los productos de este vendedor específico
        productos_reales = self.db.query(Producto).filter(Producto.id_vendedor == id_usuario).all()
        
        # Convertimos los productos a una lista de texto que la IA entienda
        lista_productos = ""
        for p in productos_reales:
            lista_productos += f"- {p.nombre_producto}: Precio ${p.precio_producto}, Stock: {p.stock_producto}\n"

        # 2. SELECCIÓN DE PROMPT (Inyectando los productos reales)
        if id_rol == 2:
            system_context = self._get_vendedor_context(id_usuario, lista_productos)
        else:
            system_context = self._get_consumidor_context(lista_productos)

        # 3. ENVIAR A OLLAMA
        response = await self.ai.generate_response(message, system_context)
        return response

    def _get_vendedor_context(self, id_vendedor: int, productos: str) -> str:
        return (
            f"Eres MercadoBot Pro. El vendedor ID {id_vendedor} tiene estos productos REALES:\n"
            f"{productos}\n"
            "Usa SOLO estos productos para tus respuestas. Si no tiene productos, dile que debe agregar stock."
            "Responde en el JSON que definimos antes."
        )
    
    def _get_consumidor_context(self, productos: str) -> str:
        return (
            f"Eres MercadoBot. Los productos disponibles en la tienda son:\n"
            f"{productos}\n"
            "Recomienda solo lo que ves en la lista anterior."
            "Responde en el JSON de consumidor."
        )