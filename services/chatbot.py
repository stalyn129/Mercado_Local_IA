from models.db_models import Producto # Importamos el modelo de tu DB
from sqlalchemy.orm import Session
from services.ollama_service import OllamaService

historiales_activos = {}

class ChatbotService:
    def __init__(self, db: Session):
        self.ai = OllamaService()
        self.db = db

    async def handle_request(self, message: str, rol: str, id_usuario: int):
        # 1. Creamos el historial para el usuario si no existe
        if id_usuario not in historiales_activos:
            historiales_activos[id_usuario] = []
        
        # 2. Obtenemos los productos reales (Tu lógica actual)
        productos_reales = self.db.query(Producto).filter(Producto.id_vendedor == id_usuario).all()
        lista_productos = "\n".join([f"- {p.nombre_producto}: ${p.precio_producto}" for p in productos_reales])

        # 3. Definimos el System Prompt según el ROL que llega de Java
        # IMPORTANTE: Usamos 'rol' como String porque así lo envía tu IAClientService.java
        if rol == "VENDEDOR":
            contexto = f"Eres MercadoBot Pro. Ayudas al vendedor ID {id_usuario}. Sus productos: {lista_productos}"
        else:
            contexto = f"Eres MercadoBot. Ayudas al cliente. Productos disponibles: {lista_productos}"

        # 4. Construimos la memoria para la IA
        mensajes_para_ollama = [{"role": "system", "content": contexto}]
        
        # Agregamos los últimos mensajes de ESTE usuario específico
        mensajes_para_ollama.extend(historiales_activos[id_usuario][-6:]) # Últimos 6 mensajes
        
        # Agregamos el mensaje nuevo
        mensajes_para_ollama.append({"role": "user", "content": message})

        # 5. Llamamos a la IA
        respuesta = await self.ai.generate_response(mensajes_para_ollama)

        # 6. GUARDAMOS en el historial de ESTE usuario
        historiales_activos[id_usuario].append({"role": "user", "content": message})
        historiales_activos[id_usuario].append({"role": "assistant", "content": respuesta})

        return respuesta

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