from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime  # <--- ESTA ES LA LÍNEA QUE FALTA

class ChatRequest(BaseModel):
    mensaje: str
    id_usuario: int
    id_rol: int 
    contexto_previo: Optional[List[str]] = None

class ChatResponse(BaseModel):
    respuesta_ia: str
    intent_detectado: str 
    sugerencias: Optional[List[str]] = None

class ChatHistorySchema(BaseModel):
    id_chat: int
    mensaje_usuario: str
    respuesta_ia: str
    fecha: datetime # Ahora ya reconocerá qué es datetime

    class Config:
        from_attributes = True