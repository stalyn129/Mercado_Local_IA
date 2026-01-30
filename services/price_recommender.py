from sqlalchemy import text
from core.database import SessionLocal
from utils.text_normalizer import extraer_palabras_clave
import unicodedata


def normalizar(texto: str) -> str:
    """Normaliza texto eliminando acentos y convirtiendo a minúsculas"""
    return ''.join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()


def convertir_precio_por_unidad(precio: float, unidad_origen: str, unidad_destino: str, nombre_producto: str = "") -> float:
    """
    Convierte un precio de una unidad a otra para comparación
    """
    if not precio or precio <= 0:
        return precio
    
    # Si son la misma unidad, no hay conversión
    if unidad_origen.lower().strip() == unidad_destino.lower().strip():
        return precio
    
    # Normalizar nombres de unidades
    unidad_origen = unidad_origen.lower().strip()
    unidad_destino = unidad_destino.lower().strip()
    nombre_lower = nombre_producto.lower() if nombre_producto else ""
    
    # 1. Huevos: conversiones comunes
    if 'huevo' in nombre_lower:
        if unidad_origen == 'docena' and unidad_destino == 'unidad':
            return precio / 12
        elif unidad_origen == 'unidad' and unidad_destino == 'docena':
            return precio * 12
        elif 'media' in unidad_origen and 'docena' in unidad_origen and unidad_destino == 'unidad':
            return precio / 6
        elif unidad_origen == 'unidad' and 'media' in unidad_destino and 'docena' in unidad_destino:
            return precio * 6
    
    # 2. Conversiones de peso (kg ↔ lb)
    if unidad_origen in ['kg', 'kilogramo'] and unidad_destino in ['lb', 'libra']:
        return precio * 2.20462
    elif unidad_origen in ['lb', 'libra'] and unidad_destino in ['kg', 'kilogramo']:
        return precio * 0.453592
    
    # 3. Conversiones de volumen (litro ↔ ml)
    if unidad_origen == 'litro' and unidad_destino == 'ml':
        return precio * 1000
    elif unidad_origen == 'ml' and unidad_destino == 'litro':
        return precio / 1000
    
    # Si no hay conversión conocida, devolver el precio original
    return precio


def recomendar_precio(nombre: str, precio_ingresado: float, unidad: str = "unidad"):
    """
    Recomienda precio considerando la unidad de medida e incluye información del vendedor
    """
    db = SessionLocal()
    try:
        print(f"🔍 Iniciando análisis para: {nombre}")
        print(f"💰 Precio ingresado: ${precio_ingresado} / {unidad}")
        
        # 🔹 Extraer palabras clave
        palabras_raw = extraer_palabras_clave(nombre)
        palabras = [normalizar(p) for p in palabras_raw if len(p) >= 3]
        
        print(f"📝 Palabras clave extraídas: {palabras}")

        if not palabras:
            return {
                "similar_found": False,
                "message": "Nombre de producto demasiado ambiguo.",
                "precio_ingresado": round(precio_ingresado, 2),
                "unidad": unidad
            }

        # 🔹 Construir condiciones de búsqueda
        condiciones = " OR ".join(
            [f"LOWER(p.nombre_producto) LIKE :p{i}" for i in range(len(palabras))]
        )

        # 🔹 Consulta SQL con información del vendedor
        sql = text(f"""
            SELECT 
                p.id_producto, 
                p.nombre_producto, 
                p.precio_producto, 
                p.unidad, 
                p.stock_producto,
                v.nombre_empresa,
                v.direccion_empresa
            FROM productos p
            LEFT JOIN vendedores v ON p.id_vendedor = v.id_vendedor
            WHERE ({condiciones})
              AND p.estado = 'Disponible'
              AND p.precio_producto > 0
            ORDER BY p.precio_producto
            LIMIT 30
        """)

        params = {
            f"p{i}": f"%{palabras[i]}%"
            for i in range(len(palabras))
        }

        print(f"🔎 Parámetros: {params}")

        rows = db.execute(sql, params).fetchall()
        print(f"📊 Productos encontrados: {len(rows)}")

        # 🔹 Si no hay resultados, buscar ampliamente
        if not rows:
            print("⚠️ No se encontraron productos directos, buscando ampliamente...")
            
            # Buscar por cada palabra individualmente
            productos_todos = []
            for palabra in palabras:
                sql_palabra = text("""
                    SELECT 
                        p.id_producto, 
                        p.nombre_producto, 
                        p.precio_producto, 
                        p.unidad, 
                        p.stock_producto,
                        v.nombre_empresa,
                        v.direccion_empresa
                    FROM productos p
                    LEFT JOIN vendedores v ON p.id_vendedor = v.id_vendedor
                    WHERE LOWER(p.nombre_producto) LIKE :palabra
                      AND p.estado = 'Disponible'
                      AND p.precio_producto > 0
                    LIMIT 10
                """)
                
                rows_palabra = db.execute(sql_palabra, {"palabra": f"%{palabra}%"}).fetchall()
                productos_todos.extend(rows_palabra)
            
            # Eliminar duplicados
            seen_ids = set()
            rows = []
            for row in productos_todos:
                if row[0] not in seen_ids:
                    seen_ids.add(row[0])
                    rows.append(row)
            
            print(f"📊 Productos encontrados (amplio): {len(rows)}")

        if not rows:
            print("❌ No se encontró ningún producto en la base de datos")
            return {
                "similar_found": False,
                "message": "No se encontraron productos en la base de datos.",
                "precio_ingresado": round(precio_ingresado, 2),
                "unidad": unidad,
                "sugerencia": "Agrega algunos productos primero para tener referencias"
            }

        # 🔹 Procesar y convertir precios
        productos_procesados = []
        precios_convertidos = []
        conversiones_aplicadas = 0
        
        print(f"📈 Procesando {len(rows)} productos...")
        
        for i, row in enumerate(rows):
            id_producto = row[0]
            nombre_producto = row[1]
            precio_producto = float(row[2]) if row[2] is not None else 0
            unidad_producto = row[3] if row[3] else 'unidad'
            stock_producto = row[4]
            nombre_empresa = row[5] if row[5] else 'Empresa no disponible'
            direccion_empresa = row[6] if row[6] else ''
            
            # Convertir precio si es necesario
            precio_convertido = convertir_precio_por_unidad(
                precio_producto, 
                unidad_producto, 
                unidad,
                nombre_producto
            )
            
            conversion_necesaria = (unidad_producto.lower() != unidad.lower() and 
                                   abs(precio_convertido - precio_producto) > 0.001)
            
            if precio_convertido > 0:
                precios_convertidos.append(precio_convertido)
                
                if conversion_necesaria:
                    conversiones_aplicadas += 1
                
                productos_procesados.append({
                    "id": id_producto,
                    "nombre": nombre_producto,
                    "precio_original": round(precio_producto, 2),
                    "unidad_original": unidad_producto,
                    "precio_convertido": round(precio_convertido, 2),
                    "unidad_convertida": unidad,
                    "conversion_necesaria": conversion_necesaria,
                    "stock": stock_producto,
                    "nombre_empresa": nombre_empresa,
                    "direccion_empresa": direccion_empresa
                })
                
                print(f"   [{i+1}] {nombre_producto[:30]}...")
                print(f"       💰 Original: ${precio_producto:.2f} / {unidad_producto}")
                print(f"       🔄 Convertido: ${precio_convertido:.2f} / {unidad}")
                print(f"       🏢 Empresa: {nombre_empresa}")
                print(f"       ⚖️ Conversión: {'Sí' if conversion_necesaria else 'No'}")

        if not productos_procesados:
            print("❌ No se pudieron procesar los precios")
            return {
                "similar_found": False,
                "message": "No se encontraron precios válidos para comparar.",
                "precio_ingresado": round(precio_ingresado, 2),
                "unidad": unidad
            }

        print(f"📊 Productos procesados válidos: {len(productos_procesados)}")
        print(f"🔄 Conversiones aplicadas: {conversiones_aplicadas}")

        # 🔹 Calcular precio de referencia
        if len(precios_convertidos) >= 3:
            # Usar mediana para evitar outliers
            sorted_precios = sorted(precios_convertidos)
            mid = len(sorted_precios) // 2
            precio_referencia = sorted_precios[mid]
            metodo = "mediana"
        elif len(precios_convertidos) > 0:
            # Usar promedio si hay pocos datos
            precio_referencia = sum(precios_convertidos) / len(precios_convertidos)
            metodo = "promedio"
        else:
            precio_referencia = 0
            metodo = "sin_datos"
        
        print(f"📊 Precio referencia calculado: ${precio_referencia:.2f} (método: {metodo})")

        # 🔹 Determinar estado
        estado = "sin_referencia"
        mensaje_estado = "Sin datos suficientes"
        diferencia_porcentaje = 0
        
        if precio_referencia > 0:
            diferencia = precio_ingresado - precio_referencia
            diferencia_porcentaje = (diferencia / precio_referencia) * 100 if precio_referencia > 0 else 0
            
            print(f"📈 Comparación:")
            print(f"   Tu precio: ${precio_ingresado:.2f}")
            print(f"   Precio ref: ${precio_referencia:.2f}")
            print(f"   Diferencia: ${diferencia:.2f}")
            print(f"   Porcentaje: {diferencia_porcentaje:.1f}%")
            
            if precio_ingresado <= 0:
                estado = "sin_precio"
                mensaje_estado = "No has ingresado un precio"
            elif diferencia_porcentaje <= -30:
                estado = "muy_bajo"
                mensaje_estado = "Muy por debajo del mercado"
            elif diferencia_porcentaje <= -15:
                estado = "bajo"
                mensaje_estado = "Por debajo del mercado"
            elif diferencia_porcentaje <= -5:
                estado = "ligeramente_bajo"
                mensaje_estado = "Ligeramente por debajo"
            elif diferencia_porcentaje <= 5:
                estado = "adecuado"
                mensaje_estado = "En línea con el mercado"
            elif diferencia_porcentaje <= 15:
                estado = "ligeramente_alto"
                mensaje_estado = "Ligeramente por encima"
            elif diferencia_porcentaje <= 30:
                estado = "alto"
                mensaje_estado = "Por encima del mercado"
            else:
                estado = "muy_alto"
                mensaje_estado = "Muy por encima del mercado"
        else:
            estado = "sin_referencia"
            mensaje_estado = "No hay datos de referencia suficientes"

        # 🔹 Contar productos por unidad
        conteo_unidades = {}
        for prod in productos_procesados:
            unidad_orig = prod["unidad_original"]
            conteo_unidades[unidad_orig] = conteo_unidades.get(unidad_orig, 0) + 1

        # 🔹 Preparar respuesta final
        resultado = {
            "similar_found": True,
            "productos_similares": productos_procesados[:10],
            "precio_promedio": round(precio_referencia, 2),
            "precio_ingresado": round(precio_ingresado, 2),
            "estado": estado,
            "mensaje_estado": mensaje_estado,
            "recomendado": round(precio_referencia, 2),
            "unidad_analizada": unidad,
            "total_productos": len(productos_procesados),
            "conteo_unidades": conteo_unidades,
            "diferencia_porcentaje": round(diferencia_porcentaje, 1) if precio_referencia > 0 else 0,
            "metodo_calculo": metodo,
            "productos_conversion": conversiones_aplicadas
        }
        
        print(f"✅ Análisis completado exitosamente")
        print(f"📋 Resultado: {resultado['estado']} - {resultado['mensaje_estado']}")
        print(f"📦 Productos en respuesta: {len(resultado['productos_similares'])}")
        
        return resultado

    except Exception as e:
        print(f"❌ Error en recomendar_precio: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "error": str(e),
            "similar_found": False,
            "message": "Error al analizar el precio",
            "precio_ingresado": round(precio_ingresado, 2),
            "unidad": unidad
        }
    finally:
        db.close()
        print("🔒 Conexión a BD cerrada")