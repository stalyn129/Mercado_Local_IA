from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

class UserBase(BaseModel):
    nombre_usuario: str
    apellido_usuario: str
    correo_electronico: EmailStr
    id_rol: int # 1: Consumidor, 2: Vendedor

class UserCreate(UserBase):
    contrasena_usuario: str
    # Campos opcionales para Vendedor
    nombre_empresa: Optional[str] = None
    ruc_empresa: Optional[str] = None
    direccion_empresa: Optional[str] = None
    telefono_empresa: Optional[str] = None
    # Campos opcionales para Consumidor
    cedula_consumidor: Optional[str] = None
    direccion_consumidor: Optional[str] = None
    telefono_consumidor: Optional[str] = None

class UserResponse(UserBase):
    id_usuario: int
    fecha_registro: datetime
    estado: str

    class Config:
        from_attributes = True