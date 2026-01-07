from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    nombre_producto: str
    descripcion_producto: str
    precio_producto: float
    stock_producto: int
    unidad: str # Ej: "kg", "lb", "unidad"
    id_subcategoria: int
    id_vendedor: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    nombre_producto: Optional[str] = None
    descripcion_producto: Optional[str] = None
    precio_producto: Optional[float] = None
    stock_producto: Optional[int] = None
    estado: Optional[str] = None

class ProductResponse(ProductBase):
    id_producto: int
    fecha_publicacion: datetime
    estado: str
    imagen_producto: Optional[str] = None

    class Config:
        from_attributes = True