from sqlalchemy.orm import Session
from models.db_models import Usuario, Vendedor, Consumidor
from core.security import Security
from fastapi import HTTPException, status
import datetime

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, correo: str, password_plano: str):
        """
        Verifica las credenciales del usuario (RF-01).
        """
        # Buscar el usuario en la tabla 'usuarios' según tu SQL
        user = self.db.query(Usuario).filter(Usuario.correo_electronico == correo).first()
        
        if not user:
            return None
            
        # Verificar el hash de la contraseña (RNF-03)
        if not Security.verify_password(password_plano, user.contrasena_usuario):
            return None
            
        return user

    def register_new_user(self, user_data):
        """
        Gestiona el registro dual: Usuario + Perfil (Vendedor/Consumidor).
        """
        # 1. Encriptar contraseña antes de guardar
        hashed_password = Security.hash_password(user_data.contrasena_usuario)

        # 2. Crear instancia de Usuario base
        nuevo_usuario = Usuario(
            nombre_usuario=user_data.nombre_usuario,
            apellido_usuario=user_data.apellido_usuario,
            correo_electronico=user_data.correo_electronico,
            contrasena_usuario=hashed_password,
            id_rol=user_data.id_rol,
            fecha_registro=datetime.datetime.now(),
            estado="ACTIVO"
        )
        
        try:
            self.db.add(nuevo_usuario)
            self.db.flush() # Para obtener el id_usuario sin terminar la transacción

            # 3. Crear el perfil específico basado en el rol del SQL
            if user_data.id_rol == 2:  # Rol Vendedor
                perfil = Vendedor(
                    id_usuario=nuevo_usuario.id_usuario,
                    nombre_empresa=user_data.nombre_empresa,
                    ruc_empresa=user_data.ruc_empresa,
                    direccion_empresa=user_data.direccion_empresa,
                    telefono_empresa=user_data.telefono_empresa
                )
                self.db.add(perfil)
            
            elif user_data.id_rol == 1:  # Rol Consumidor
                perfil = Consumidor(
                    id_usuario=nuevo_usuario.id_usuario,
                    cedula_consumidor=user_data.cedula_consumidor,
                    direccion_consumidor=user_data.direccion_consumidor,
                    telefono_consumidor=user_data.telefono_consumidor
                )
                self.db.add(perfil)

            self.db.commit()
            self.db.refresh(nuevo_usuario)
            return nuevo_usuario

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en el registro: {str(e)}"
            )

    def get_user_role_name(self, id_rol: int):
        """
        Retorna el nombre del rol según el ID para que la IA sepa con quién habla.
        """
        if id_rol == 1: return "Consumidor"
        if id_rol == 2: return "Vendedor"
        return "Desconocido"