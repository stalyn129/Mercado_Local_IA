from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.db_models import Pedido, DetallesPedido, Producto, Pago
from api.schemas.order_schema import OrderCreate, OrderResponse
from typing import List
import datetime

router = APIRouter()

# 1. Crear un Pedido (RF-04: Checkout)
@router.post("/", response_model=OrderResponse)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    # Calcular totales y validar stock
    total_pedido = 0
    items_procesados = []

    for item in order_data.items:
        producto = db.query(Producto).filter(Producto.id_producto == item.id_producto).first()
        if not producto or producto.stock_producto < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {producto.nombre_producto}")
        
        subtotal = producto.precio_producto * item.cantidad
        total_pedido += subtotal
        
        # Descontar stock
        producto.stock_producto -= item.cantidad
        items_procesados.append({
            "id_producto": producto.id_producto,
            "cantidad": item.cantidad,
            "precio_unitario": producto.precio_producto,
            "subtotal": subtotal
        })

    # Crear cabecera del pedido
    nuevo_pedido = Pedido(
        id_consumidor=order_data.id_consumidor,
        id_vendedor=order_data.id_vendedor,
        fecha_pedido=datetime.datetime.now(),
        estado_pedido="PENDIENTE", # RF-05: Estado inicial
        total=total_pedido,
        metodo_pago=order_data.metodo_pago
    )
    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)

    # Crear los detalles del pedido
    for item in items_procesados:
        detalle = DetallesPedido(
            id_pedido=nuevo_pedido.id_pedido,
            id_producto=item["id_producto"],
            cantidad=item["cantidad"],
            precio_unitario=item["precio_unitario"],
            subtotal=item["subtotal"]
        )
        db.add(detalle)
    
    db.commit()
    return nuevo_pedido

# 2. Actualizar Estado del Pedido (RF-05: Para el Productor)
@router.patch("/{id_pedido}/estado")
def update_order_status(id_pedido: int, nuevo_estado: str, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id_pedido == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Estados: "En preparación", "Enviado", "Entregado"
    pedido.estado_pedido = nuevo_estado
    db.commit()
    return {"message": f"Pedido actualizado a: {nuevo_estado}"}

# 3. Listar pedidos para el Productor (RF-05)
@router.get("/vendedor/{id_vendedor}", response_model=List[OrderResponse])
def get_seller_orders(id_vendedor: int, db: Session = Depends(get_db)):
    return db.query(Pedido).filter(Pedido.id_vendedor == id_vendedor).all()

# 4. Listar pedidos para el Consumidor (Historial)
@router.get("/consumidor/{id_consumidor}", response_model=List[OrderResponse])
def get_consumer_orders(id_consumidor: int, db: Session = Depends(get_db)):
    return db.query(Pedido).filter(Pedido.id_consumidor == id_consumidor).all()