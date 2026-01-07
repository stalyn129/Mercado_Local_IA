from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Esquema para los items individuales dentro de un pedido
class OrderItem(BaseModel):
    id_producto: int
    cantidad: int

# Esquema para crear un pedido (lo que envía el Frontend)
class OrderCreate(BaseModel):
    id_consumidor: int
    id_vendedor: int
    metodo_pago: str # "EFECTIVO", "TARJETA", etc.
    items: List[OrderItem]

# Esquema para mostrar la respuesta del pedido
class OrderResponse(BaseModel):
    id_pedido: int
    id_consumidor: int
    id_vendedor: int
    fecha_pedido: datetime
    total: float
    estado_pedido: str

    class Config:
        from_attributes = True