from pydantic import BaseModel

class PriceRequest(BaseModel):
    product_id: int
    current_price: float
    historical_sales: int
    stock: int

class ChatRequest(BaseModel):
    message: str
