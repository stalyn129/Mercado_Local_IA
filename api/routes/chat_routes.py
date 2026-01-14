from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.chatbot import ChatbotService
from api.schemas.chat_schema import ChatRequest

router = APIRouter()

@router.post("/chat")
async def chat(payload: dict, db: Session = Depends(get_db)):
    service = ChatbotService(db)
    # Java envía 'id_usuario', 'rol' (String) y 'mensaje'
    respuesta = await service.handle_request(
        message=payload.get("mensaje"),
        rol=payload.get("rol"), # "VENDEDOR" o "CONSUMIDOR"
        id_usuario=payload.get("id_usuario")
    )
    return {"respuesta": respuesta}