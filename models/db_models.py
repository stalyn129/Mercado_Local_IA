
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from core.database import Base
import datetime

class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(100))
    apellido_usuario = Column(String(100))
    correo_electronico = Column(String(100), unique=True)
    contrasena_usuario = Column(String(255))
    id_rol = Column(Integer, ForeignKey("roles.id_rol"))
    fecha_registro = Column(DateTime, default=datetime.datetime.now)
    estado = Column(String(255))

class Vendedor(Base):
    __tablename__ = "vendedores"
    id_vendedor = Column(Integer, primary_key=True, index=True)
    nombre_empresa = Column(String(100))
    ruc_empresa = Column(String(13), unique=True)
    direccion_empresa = Column(String(255))
    telefono_empresa = Column(String(10))
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))

class Consumidor(Base):
    __tablename__ = "consumidores"
    id_consumidor = Column(Integer, primary_key=True, index=True)
    cedula_consumidor = Column(String(10), unique=True)
    direccion_consumidor = Column(String(255))
    telefono_consumidor = Column(String(10))
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))

class Producto(Base):
    __tablename__ = "productos"
    id_producto = Column(Integer, primary_key=True, index=True)
    nombre_producto = Column(String(150))
    descripcion_producto = Column(Text)
    precio_producto = Column(Float)
    stock_producto = Column(Integer)
    unidad = Column(String(20))
    id_vendedor = Column(Integer, ForeignKey("vendedores.id_vendedor"))
    id_subcategoria = Column(Integer, ForeignKey("subcategorias.id_subcategoria"))
    fecha_publicacion = Column(DateTime)
    estado = Column(String(20))

class Pedido(Base):
    __tablename__ = "pedidos"
    id_pedido = Column(Integer, primary_key=True, index=True)
    id_consumidor = Column(Integer, ForeignKey("consumidores.id_consumidor"))
    id_vendedor = Column(Integer, ForeignKey("vendedores.id_vendedor"))
    total = Column(Float)
    estado_pedido = Column(String(255))
    fecha_pedido = Column(DateTime)
    metodo_pago = Column(String(255))

class DetallesPedido(Base):
    __tablename__ = "detalles_pedido"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"))
    id_producto = Column(Integer, ForeignKey("productos.id_producto"))
    cantidad = Column(Integer)
    precio_unitario = Column(Float)
    subtotal = Column(Float)

class Pago(Base):
    __tablename__ = "pagos"
    id_pago = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido"))
    id_consumidor = Column(Integer, ForeignKey("consumidores.id_consumidor"))
    monto = Column(Float)
    fecha = Column(DateTime, default=datetime.datetime.now)
    metodo = Column(Enum('EFECTIVO', 'TARJETA', 'TRANSFERENCIA'))
    estado = Column(Enum('PAGADO', 'PENDIENTE', 'PENDIENTE_VERIFICACION'))