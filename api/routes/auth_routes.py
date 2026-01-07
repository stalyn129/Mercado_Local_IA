from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import Security
from models.db_models import Usuario, Vendedor, Consumidor
from api.schemas.user_schema import UserCreate, UserResponse
import datetime

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Verificar si el correo ya existe
    db_user = db.query(Usuario).filter(Usuario.correo_electronico == user_data.correo_electronico).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # 2. Encriptar contraseña (RNF-03)
    hashed_pwd = Security.hash_password(user_data.contrasena_usuario)

    # 3. Crear el usuario base en la tabla 'usuarios'
    nuevo_usuario = Usuario(
        nombre_usuario=user_data.nombre_usuario,
        apellido_usuario=user_data.apellido_usuario,
        correo_electronico=user_data.correo_electronico,
        contrasena_usuario=hashed_pwd,
        id_rol=user_data.id_rol, # 1 para Consumidor, 2 para Vendedor
        fecha_registro=datetime.datetime.now(),
        estado="ACTIVO"
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # 4. Crear el perfil específico según el rol (RF-01)
    if user_data.id_rol == 2:  # Rol Vendedor
        perfil_vendedor = Vendedor(
            nombre_empresa=user_data.nombre_empresa,
            ruc_empresa=user_data.ruc_empresa,
            direccion_empresa=user_data.direccion_empresa,
            telefono_empresa=user_data.telefono_empresa,
            id_usuario=nuevo_usuario.id_usuario
        )
        db.add(perfil_vendedor)
    
    elif user_data.id_rol == 1:  # Rol Consumidor
        perfil_consumidor = Consumidor(
            cedula_consumidor=user_data.cedula_consumidor,
            direccion_consumidor=user_data.direccion_consumidor,
            telefono_consumidor=user_data.telefono_consumidor,
            id_usuario=nuevo_usuario.id_usuario
        )
        db.add(perfil_consumidor)

    db.commit()
    return nuevo_usuario

@router.post("/login")
def login(request: dict, db: Session = Depends(get_db)):
    # Buscar usuario por correo
    user = db.query(Usuario).filter(Usuario.correo_electronico == request["correo"]).first()
    
    if not user or not Security.verify_password(request["contrasena"], user.contrasena_usuario):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # Retornar datos básicos y el rol para que el Frontend sepa qué mostrar
    return {
        "id_usuario": user.id_usuario,
        "nombre": user.nombre_usuario,
        "rol": "Vendedor" if user.id_rol == 2 else "Consumidor",
        "message": "Login exitoso"
    }