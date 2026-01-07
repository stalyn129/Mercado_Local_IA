from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.db_models import Producto, Vendedor
from api.schemas.product_schema import ProductCreate, ProductUpdate, ProductResponse
from typing import List
import datetime

router = APIRouter()

# 1. Crear Producto (RF-02)
@router.post("/", response_model=ProductResponse)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    # Verificar que el vendedor existe
    vendedor = db.query(Vendedor).filter(Vendedor.id_vendedor == product_data.id_vendedor).first()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")

    nuevo_producto = Producto(
        nombre_producto=product_data.nombre_producto,
        descripcion_producto=product_data.descripcion_producto,
        precio_producto=product_data.precio_producto,
        stock_producto=product_data.stock_producto,
        unidad=product_data.unidad,
        id_subcategoria=product_data.id_subcategoria,
        id_vendedor=product_data.id_vendedor,
        fecha_publicacion=datetime.datetime.now(),
        estado="ACTIVO"
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

# 2. Leer productos de un vendedor específico (Para el Dashboard del Productor)
@router.get("/vendedor/{id_vendedor}", response_model=List[ProductResponse])
def get_vendedor_inventory(id_vendedor: int, db: Session = Depends(get_db)):
    return db.query(Producto).filter(Producto.id_vendedor == id_vendedor).all()

# 3. Actualizar Producto (RF-02)
@router.put("/{id_producto}", response_model=ProductResponse)
def update_product(id_producto: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Actualizar campos dinámicamente
    for var, value in vars(product_data).items():
        if value is not None:
            setattr(db_product, var, value)
            
    db.commit()
    db.refresh(db_product)
    return db_product

# 4. Eliminar Producto (RF-02)
@router.delete("/{id_producto}")
def delete_product(id_producto: int, db: Session = Depends(get_db)):
    db_product = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Producto eliminado exitosamente"}