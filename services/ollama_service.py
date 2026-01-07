import httpx
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from core.config import settings

# Configuración de logging para monitorear el comportamiento de la IA
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = httpx.Timeout(60.0, connect=10.0) # Tiempo de espera extendido para modelos pesados

    def _get_system_prompt(self, context: str) -> str:
        """
        Genera el prompt de sistema dinámico con fecha y personalidad.
        """
        now = datetime.now()
        fecha_formateada = now.strftime("%A, %d de %B de %Y (Hora: %H:%M)")
        
        return (
            f"Eres el Asistente Inteligente de 'MercadoLocal-IA', una plataforma de comercio local. "
            f"INFORMACIÓN EN TIEMPO REAL: Hoy es {fecha_formateada}. "
            f"TU ROL: {context}. "
            "INSTRUCCIONES: "
            "1. Saluda cordialmente. 2. Usa datos de la plataforma si se te proporcionan. "
            "3. Si no sabes algo, admítelo pero ofrece ayuda relacionada al comercio. "
            "4. Tus respuestas deben ser profesionales, breves y en español."
        )

    async def generate_response(self, prompt: str, system_context: str = "Asesor General") -> str:
        """
        Envía una petición al modelo Ollama y gestiona el ciclo de vida de la respuesta.
        """
        url = f"{self.base_url}/api/generate"
        system_prompt = self._get_system_prompt(system_context)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7, # Creatividad balanceada
                "num_predict": 500  # Límite de tokens para evitar respuestas infinitas
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Enviando solicitud a Ollama ({self.model})...")
                response = await client.post(url, json=payload)
                
                # Verificación de errores HTTP (404, 500, etc.)
                response.raise_for_status()
                
                data = response.json()
                logger.info("Respuesta recibida exitosamente de la IA.")
                return data.get("response", "No se obtuvo una respuesta válida del modelo.")

            except httpx.ConnectError:
                logger.error("Error: No se pudo conectar con el servidor de Ollama. ¿Está encendido?")
                return "Error técnico: El motor de IA no está disponible en este momento."
            
            except httpx.ReadTimeout:
                logger.error("Error: La IA tardó demasiado en responder (Timeout).")
                return "La IA está procesando demasiada información, por favor intenta de nuevo en un momento."
            
            except Exception as e:
                logger.error(f"Error inesperado en OllamaService: {str(e)}")
                return f"Lo siento, ocurrió un error interno al procesar tu consulta."

    async def check_health(self) -> bool:
        """
        Verifica si el servicio de Ollama está activo.
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False