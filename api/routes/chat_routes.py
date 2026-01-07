from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.chatbot import ChatbotService
from api.schemas.chat_schema import ChatRequest

router = APIRouter()

@router.post("/chat")
async def chat_with_ia(request: ChatRequest, db: Session = Depends(get_db)):
    bot = ChatbotService(db) # Aquí se usa el nombre de la clase
    response = await bot.handle_request(
        message=request.mensaje,
        id_rol=request.id_rol,
        id_usuario=request.id_usuario
    )
    return {"reply": response}