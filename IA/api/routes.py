from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from api.dependencies import price_service
from core.database import get_db

router = APIRouter()

@router.get("/price/from_db/{product_id}")
def predict_price_from_db(product_id: int, db: Session = Depends(get_db)):
    return price_service.predict_from_db(db, product_id)
