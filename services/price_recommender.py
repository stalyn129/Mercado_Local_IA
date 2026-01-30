from sqlalchemy import text
from core.database import SessionLocal
from utils.text_normalizer import extraer_palabras_clave
import unicodedata
import re
from collections import Counter


def normalizar(texto: str) -> str:
    """Normaliza texto eliminando acentos y convirtiendo a minúsculas"""
    return ''.join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()


def normalizar_unidad(unidad: str) -> str:
    """Normaliza nombres de unidades a un formato estándar"""
    if not unidad:
        return 'unidad'
    
    unidad = unidad.lower().strip()
    
    # Mapeo de unidades comunes
    mapeo = {
        'kilogramo': 'kg',
        'kilogramos': 'kg',
        'kilo': 'kg',
        'kilos': 'kg',
        'gramo': 'g',
        'gramos': 'g',
        'libra': 'lb',
        'libras': 'lb',
        'litro': 'l',
        'litros': 'l',
        'mililitro': 'ml',
        'mililitros': 'ml',
        'centimetro cubico': 'ml',
        'centímetros cúbicos': 'ml',
        'cc': 'ml',
        'unidad': 'unidad',
        'unidades': 'unidad',
        'docena': 'docena',
        'docenas': 'docena',
        'media docena': 'media docena',
        'media docenas': 'media docena',
        'paquete': 'paquete',
        'paquetes': 'paquete',
        'pack': 'paquete',
        'packs': 'paquete',
        'caja': 'caja',
        'cajas': 'caja',
        'bolsa': 'bolsa',
        'bolsas': 'bolsa'
    }
    
    # Buscar en el mapeo
    for key, value in mapeo.items():
        if key in unidad:
            return value
    
    return unidad


def sugerir_unidad_segun_producto(nombre_producto: str, unidad_ingresada: str) -> str:
    """Sugiere la unidad más apropiada según el tipo de producto"""
    nombre_lower = nombre_producto.lower()
    unidad_ingresada_norm = normalizar_unidad(unidad_ingresada)
    
    # ===== PRODUCTOS POR UNIDAD (contables) =====
    productos_por_unidad = [
        'huevo', 'huevos', 'huevito', 'ovo',
        'manzana', 'naranja', 'limón', 'limones', 'cebolla', 'tomate',
        'plátano', 'banano', 'pera', 'durazno', 'melocotón',
        'pan', 'panes', 'bolillo', 'torta',
        'papa', 'papas', 'zanahoria', 'zanahorias',
        'ajo', 'ajos', 'cebollín', 'pimiento', 'pimientos'
    ]
    
    # ===== PRODUCTOS POR PESO =====
    productos_por_peso = [
        'carne', 'pollo', 'pescado', 'res', 'cerdo',
        'queso', 'jamón', 'salchicha', 'chorizo',
        'arroz', 'frijol', 'azúcar', 'sal', 'harina', 'maíz',
        'café', 'chocolate', 'cacao',
        'pasta', 'espagueti', 'fideo',
        'mantequilla', 'margarina'
    ]
    
    # ===== PRODUCTOS LÍQUIDOS =====
    productos_liquidos = [
        'leche', 'aceite', 'agua', 'jugo', 'refresco', 'vino', 'cerveza',
        'licor', 'whisky', 'ron', 'vodka',
        'salsa', 'vinagre', 'sopa', 'caldo'
    ]
    
    # Verificar tipo de producto
    for palabra in productos_por_unidad:
        if palabra in nombre_lower:
            # Si el usuario ingresó ml, l, kg, g para productos por unidad, sugerir unidad
            if unidad_ingresada_norm in ['ml', 'l', 'kg', 'g', 'lb']:
                return "unidad"
            return unidad_ingresada_norm if unidad_ingresada_norm in ['unidad', 'docena', 'media docena'] else "unidad"
    
    for palabra in productos_por_peso:
        if palabra in nombre_lower:
            # Si el usuario ingresó ml, l, unidad, docena para productos por peso, sugerir kg
            if unidad_ingresada_norm in ['ml', 'l', 'unidad', 'docena', 'media docena']:
                return "kg"
            return unidad_ingresada_norm if unidad_ingresada_norm in ['kg', 'g', 'lb'] else "kg"
    
    for palabra in productos_liquidos:
        if palabra in nombre_lower:
            # Si el usuario ingresó kg, g, unidad, docena para líquidos, sugerir l
            if unidad_ingresada_norm in ['kg', 'g', 'lb', 'unidad', 'docena', 'media docena']:
                return "l"
            return unidad_ingresada_norm if unidad_ingresada_norm in ['l', 'ml'] else "l"
    
    # Si no hay coincidencia, mantener la unidad ingresada
    return unidad_ingresada_norm


def es_unidad_de_peso(unidad: str) -> bool:
    """Verifica si la unidad es de peso"""
    return unidad in ['kg', 'g', 'lb']


def es_unidad_de_volumen(unidad: str) -> bool:
    """Verifica si la unidad es de volumen"""
    return unidad in ['l', 'ml']


def es_unidad_contable(unidad: str) -> bool:
    """Verifica si la unidad es contable (no peso/volumen)"""
    return unidad in ['unidad', 'docena', 'media docena', 'paquete', 'caja', 'bolsa']


def es_unidad_inapropiada_para_producto(unidad: str, nombre_producto: str) -> bool:
    """Verifica si la unidad es inapropiada para el tipo de producto"""
    nombre_lower = nombre_producto.lower()
    unidad_norm = normalizar_unidad(unidad)
    
    # Productos por unidad no deben usar peso/volumen
    productos_por_unidad = ['huevo', 'huevos', 'huevito', 'ovo']
    for palabra in productos_por_unidad:
        if palabra in nombre_lower:
            return es_unidad_de_peso(unidad_norm) or es_unidad_de_volumen(unidad_norm)
    
    return False


def convertir_precio_por_unidad(precio: float, unidad_origen: str, unidad_destino: str, nombre_producto: str = "") -> float:
    """
    Convierte un precio de una unidad a otra para comparación
    """
    if not precio or precio <= 0:
        return None
    
    # Normalizar unidades
    unidad_origen_norm = normalizar_unidad(unidad_origen)
    unidad_destino_norm = normalizar_unidad(unidad_destino)
    
    # Si son la misma unidad, no hay conversión
    if unidad_origen_norm == unidad_destino_norm:
        return precio
    
    nombre_lower = nombre_producto.lower() if nombre_producto else ""
    
    # ===== CONVERSIONES ESPECÍFICAS PARA HUEVOS =====
    if any(palabra in nombre_lower for palabra in ['huevo', 'huevos', 'huevito', 'ovo']):
        # Huevos: solo conversiones entre unidades contables
        if es_unidad_contable(unidad_origen_norm) and es_unidad_contable(unidad_destino_norm):
            conversiones_huevos = {
                ('docena', 'unidad'): precio / 12,
                ('unidad', 'docena'): precio * 12,
                ('media docena', 'unidad'): precio / 6,
                ('unidad', 'media docena'): precio * 6,
                ('media docena', 'docena'): precio * 2,
                ('docena', 'media docena'): precio / 2,
            }
            
            return conversiones_huevos.get(
                (unidad_origen_norm, unidad_destino_norm), 
                None
            )
        # No convertir huevos a/desde peso/volumen
        return None
    
    # ===== CONVERSIONES DE PESO =====
    if es_unidad_de_peso(unidad_origen_norm) and es_unidad_de_peso(unidad_destino_norm):
        # Convertir todo a gramos primero
        a_gramos = {
            'kg': 1000,
            'g': 1,
            'lb': 453.592,
        }
        
        # Convertir de gramos a unidad destino
        desde_gramos = {
            'kg': 0.001,
            'g': 1,
            'lb': 1 / 453.592,
        }
        
        if unidad_origen_norm in a_gramos and unidad_destino_norm in desde_gramos:
            gramos = precio * a_gramos[unidad_origen_norm]
            return gramos * desde_gramos[unidad_destino_norm]
    
    # ===== CONVERSIONES DE VOLUMEN =====
    if es_unidad_de_volumen(unidad_origen_norm) and es_unidad_de_volumen(unidad_destino_norm):
        # Convertir todo a mililitros primero
        a_ml = {
            'l': 1000,
            'ml': 1,
        }
        
        # Convertir de ml a unidad destino
        desde_ml = {
            'l': 0.001,
            'ml': 1,
        }
        
        if unidad_origen_norm in a_ml and unidad_destino_norm in desde_ml:
            ml = precio * a_ml[unidad_origen_norm]
            return ml * desde_ml[unidad_destino_norm]
    
    # ===== CONVERSIONES ENTRE UNIDADES CONTABLES =====
    if es_unidad_contable(unidad_origen_norm) and es_unidad_contable(unidad_destino_norm):
        # Conversiones básicas entre unidades contables
        if unidad_origen_norm == 'paquete' and unidad_destino_norm == 'unidad':
            try:
                match = re.search(r'\d+', unidad_origen.lower())
                if match:
                    unidades_por_paquete = int(match.group())
                    if unidades_por_paquete > 0:
                        return precio / unidades_por_paquete
            except:
                pass
        
        # Caja/bolsa a unidad (asumir 12 unidades)
        if unidad_origen_norm in ['caja', 'bolsa'] and unidad_destino_norm == 'unidad':
            return precio / 12
    
    # ===== Si no hay conversión posible =====
    return None


def calcular_estado_precio(precio_usuario: float, precio_referencia: float) -> dict:
    """Calcula el estado del precio comparado con la referencia"""
    if precio_referencia <= 0 or precio_usuario <= 0:
        return {
            "estado": "sin_referencia",
            "mensaje": "Sin datos suficientes",
            "diferencia_porcentaje": 0
        }
    
    diferencia = precio_usuario - precio_referencia
    diferencia_porcentaje = (diferencia / precio_referencia) * 100
    
    if diferencia_porcentaje <= -30:
        estado = "muy_bajo"
        mensaje = "Muy por debajo del mercado"
    elif diferencia_porcentaje <= -15:
        estado = "bajo"
        mensaje = "Por debajo del mercado"
    elif diferencia_porcentaje <= -5:
        estado = "ligeramente_bajo"
        mensaje = "Ligeramente por debajo"
    elif diferencia_porcentaje <= 5:
        estado = "adecuado"
        mensaje = "En línea con el mercado"
    elif diferencia_porcentaje <= 15:
        estado = "ligeramente_alto"
        mensaje = "Ligeramente por encima"
    elif diferencia_porcentaje <= 30:
        estado = "alto"
        mensaje = "Por encima del mercado"
    else:
        estado = "muy_alto"
        mensaje = "Muy por encima del mercado"
    
    return {
        "estado": estado,
        "mensaje": mensaje,
        "diferencia_porcentaje": round(diferencia_porcentaje, 1)
    }


def recomendar_precio(nombre: str, precio_ingresado: float, unidad: str = "unidad"):
    """
    Recomienda precio considerando la unidad de medida
    """
    db = SessionLocal()
    try:
        print(f"🔍 Iniciando análisis para: {nombre}")
        print(f"💰 Precio ingresado: ${precio_ingresado:.2f} / {unidad}")
        
        # Normalizar unidad ingresada
        unidad_normalizada = normalizar_unidad(unidad)
        print(f"📏 Unidad normalizada: {unidad_normalizada}")
        
        # 🔹 Verificar si la unidad es apropiada para el producto
        unidad_sugerida = sugerir_unidad_segun_producto(nombre, unidad_normalizada)
        print(f"💡 Unidad sugerida por tipo de producto: {unidad_sugerida}")
        
        unidad_inapropiada = es_unidad_inapropiada_para_producto(unidad_normalizada, nombre)
        if unidad_inapropiada:
            print(f"⚠️ Unidad inapropiada detectada: {unidad_normalizada}")
        
        # 🔹 Extraer palabras clave
        palabras_raw = extraer_palabras_clave(nombre)
        palabras = [normalizar(p) for p in palabras_raw if len(p) >= 3]
        
        print(f"📝 Palabras clave extraídas: {palabras}")

        if not palabras:
            return {
                "similar_found": False,
                "message": "Nombre de producto demasiado ambiguo.",
                "precio_ingresado": round(precio_ingresado, 2),
                "unidad": unidad,
                "unidad_inapropiada": unidad_inapropiada,
                "unidad_sugerida": unidad_sugerida,
                "consejo": f"Usa '{unidad_sugerida}' para {nombre}"
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

        if not rows:
            print("❌ No se encontró ningún producto en la base de datos")
            return {
                "similar_found": False,
                "message": "No se encontraron productos en la base de datos.",
                "precio_ingresado": round(precio_ingresado, 2),
                "unidad": unidad,
                "unidad_inapropiada": unidad_inapropiada,
                "unidad_sugerida": unidad_sugerida,
                "consejo": f"Agrega algunos productos primero para tener referencias. Usa '{unidad_sugerida}' para {nombre}"
            }

        # 🔹 Recolectar todas las unidades encontradas para sugerencia
        todas_unidades = []
        for row in rows:
            unidad_producto = normalizar_unidad(row[3] if row[3] else 'unidad')
            todas_unidades.append(unidad_producto)
        
        # 🔹 Procesar y convertir precios
        productos_procesados = []
        precios_convertidos = []
        conversiones_aplicadas = 0
        productos_omitidos = 0
        
        print(f"📈 Procesando {len(rows)} productos...")
        
        for i, row in enumerate(rows):
            id_producto, nombre_producto, precio_producto, unidad_producto, stock, empresa, direccion = row
            
            # Normalizar unidad del producto
            unidad_producto_norm = normalizar_unidad(unidad_producto) if unidad_producto else 'unidad'
            
            # Convertir precio
            precio_convertido = convertir_precio_por_unidad(
                precio_producto, 
                unidad_producto_norm, 
                unidad_normalizada,
                nombre_producto
            )
            
            # Si no se puede convertir (None), omitir este producto
            if precio_convertido is None:
                productos_omitidos += 1
                print(f"   [{i+1}] ⚠️ {nombre_producto[:30]}... - OMITIDO (no convertible: {unidad_producto_norm} → {unidad_normalizada})")
                continue
            
            conversion_necesaria = (unidad_producto_norm != unidad_normalizada)
            
            if precio_convertido > 0:
                precios_convertidos.append(precio_convertido)
                
                if conversion_necesaria:
                    conversiones_aplicadas += 1
                
                productos_procesados.append({
                    "id": id_producto,
                    "nombre": nombre_producto,
                    "precio_original": round(precio_producto, 2),
                    "unidad_original": unidad_producto_norm,
                    "precio_convertido": round(precio_convertido, 2),
                    "unidad_convertida": unidad_normalizada,
                    "conversion_necesaria": conversion_necesaria,
                    "stock": stock,
                    "nombre_empresa": empresa or 'Empresa no disponible',
                    "direccion_empresa": direccion or ''
                })
                
                print(f"   [{i+1}] {nombre_producto[:30]}...")
                print(f"       💰 Original: ${precio_producto:.2f} / {unidad_producto_norm}")
                print(f"       🔄 Convertido: ${precio_convertido:.2f} / {unidad_normalizada}")
                if conversion_necesaria:
                    print(f"       ⚖️ Conversión: Sí ({unidad_producto_norm} → {unidad_normalizada})")

        print(f"📊 Productos procesados válidos: {len(productos_procesados)}")
        print(f"🔄 Conversiones aplicadas: {conversiones_aplicadas}")
        print(f"🚫 Productos omitidos: {productos_omitidos}")
        
        # 🔹 ANALIZAR SI HAY PRODUCTOS PROCESADOS
        if not productos_procesados:
            print("⚠️ No se pudieron procesar los precios - analizando unidades disponibles")
            
            # Analizar qué unidades hay disponibles
            unidades_disponibles = list(set(todas_unidades))
            print(f"📦 Unidades disponibles en mercado: {unidades_disponibles}")
            
            # Si la unidad es inapropiada, usar la unidad sugerida
            if unidad_inapropiada:
                print(f"🔄 Usando unidad sugerida: {unidad_sugerida}")
                
                # Reprocesar con la unidad sugerida
                productos_procesados_sugeridos = []
                precios_convertidos_sugeridos = []
                
                for i, row in enumerate(rows):
                    id_producto, nombre_producto, precio_producto, unidad_producto, stock, empresa, direccion = row
                    unidad_producto_norm = normalizar_unidad(unidad_producto) if unidad_producto else 'unidad'
                    
                    precio_convertido = convertir_precio_por_unidad(
                        precio_producto, 
                        unidad_producto_norm, 
                        unidad_sugerida,
                        nombre_producto
                    )
                    
                    if precio_convertido is not None and precio_convertido > 0:
                        precios_convertidos_sugeridos.append(precio_convertido)
                        productos_procesados_sugeridos.append({
                            "id": id_producto,
                            "nombre": nombre_producto,
                            "precio_original": round(precio_producto, 2),
                            "unidad_original": unidad_producto_norm,
                            "precio_convertido": round(precio_convertido, 2),
                            "unidad_convertida": unidad_sugerida,
                            "conversion_necesaria": unidad_producto_norm != unidad_sugerida,
                            "stock": stock,
                            "nombre_empresa": empresa or 'Empresa no disponible',
                            "direccion_empresa": direccion or ''
                        })
                
                if productos_procesados_sugeridos:
                    # Calcular precio de referencia con unidad sugerida
                    if len(precios_convertidos_sugeridos) >= 3:
                        sorted_precios = sorted(precios_convertidos_sugeridos)
                        mid = len(sorted_precios) // 2
                        precio_referencia = sorted_precios[mid]
                        metodo = "mediana"
                    elif len(precios_convertidos_sugeridos) > 0:
                        precio_referencia = sum(precios_convertidos_sugeridos) / len(precios_convertidos_sugeridos)
                        metodo = "promedio"
                    else:
                        precio_referencia = 0
                        metodo = "sin_datos"
                    
                    print(f"📊 Precio referencia en {unidad_sugerida}: ${precio_referencia:.2f}")
                    
                    # Calcular estado basado en la conversión
                    estado_info = calcular_estado_precio(precio_ingresado, precio_referencia)
                    estado = estado_info["estado"]
                    mensaje_estado = estado_info["mensaje"]
                    diferencia_porcentaje = estado_info["diferencia_porcentaje"]
                    
                    # Crear mensaje específico
                    if unidad_inapropiada:
                        mensaje_unidad = f"Los huevos se venden por '{unidad_sugerida}', no por '{unidad_normalizada}'"
                        consejo = f"Cambia la unidad a '{unidad_sugerida}' para una comparación precisa. Los huevos no se venden por peso o volumen."
                    else:
                        mensaje_unidad = f"Los productos similares se venden por {unidad_sugerida}"
                        consejo = f"Cambia la unidad a '{unidad_sugerida}' para una comparación precisa."
                    
                    return {
                        "similar_found": True,
                        "productos_similares": productos_procesados_sugeridos[:10],
                        "precio_promedio": round(precio_referencia, 2),
                        "precio_ingresado": round(precio_ingresado, 2),
                        "estado": estado,
                        "mensaje_estado": mensaje_unidad,
                        "recomendado": round(precio_referencia, 2),
                        "unidad_analizada": unidad_sugerida,
                        "unidad_sugerida": unidad_sugerida,
                        "unidad_original_usuario": unidad_normalizada,
                        "unidad_inapropiada": unidad_inapropiada,
                        "total_productos": len(productos_procesados_sugeridos),
                        "diferencia_porcentaje": diferencia_porcentaje,
                        "metodo_calculo": metodo,
                        "productos_conversion": len([p for p in productos_procesados_sugeridos if p["conversion_necesaria"]]),
                        "consejo": consejo,
                        "unidades_disponibles": unidades_disponibles
                    }
            
            # Si aún no hay productos procesados
            mensaje_error = f"No se encontraron productos comparables en {unidad_normalizada}."
            if unidad_inapropiada:
                mensaje_error += f" Usa '{unidad_sugerida}' en lugar de '{unidad_normalizada}'."
            
            return {
                "similar_found": False,
                "message": mensaje_error,
                "precio_ingresado": round(precio_ingresado, 2),
                "unidad": unidad,
                "unidad_inapropiada": unidad_inapropiada,
                "unidades_disponibles": unidades_disponibles,
                "unidad_sugerida": unidad_sugerida,
                "consejo": f"Usa '{unidad_sugerida}' para {nombre}."
            }
        
        # 🔹 Si hay productos procesados, calcular precio de referencia normal
        if precios_convertidos:
            print(f"💰 Precios convertidos: {[round(p, 2) for p in precios_convertidos]}")
        
        if len(precios_convertidos) >= 3:
            sorted_precios = sorted(precios_convertidos)
            mid = len(sorted_precios) // 2
            precio_referencia = sorted_precios[mid]
            metodo = "mediana"
        elif len(precios_convertidos) > 0:
            precio_referencia = sum(precios_convertidos) / len(precios_convertidos)
            metodo = "promedio"
        else:
            precio_referencia = 0
            metodo = "sin_datos"
        
        print(f"📊 Precio referencia calculado: ${precio_referencia:.2f} (método: {metodo})")

        # 🔹 Determinar estado
        estado_info = calcular_estado_precio(precio_ingresado, precio_referencia)
        estado = estado_info["estado"]
        mensaje_estado = estado_info["mensaje"]
        diferencia_porcentaje = estado_info["diferencia_porcentaje"]
        
        print(f"📈 Comparación:")
        print(f"   Tu precio: ${precio_ingresado:.2f}")
        print(f"   Precio ref: ${precio_referencia:.2f}")
        print(f"   Diferencia: ${precio_ingresado - precio_referencia:.2f}")
        print(f"   Porcentaje: {diferencia_porcentaje:.1f}%")
        print(f"   Estado: {estado} - {mensaje_estado}")

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
            "unidad_analizada": unidad_normalizada,
            "unidad_inapropiada": unidad_inapropiada,
            "unidad_sugerida": unidad_sugerida if unidad_inapropiada else unidad_normalizada,
            "total_productos": len(productos_procesados),
            "conteo_unidades": conteo_unidades,
            "diferencia_porcentaje": diferencia_porcentaje,
            "metodo_calculo": metodo,
            "productos_conversion": conversiones_aplicadas,
            "productos_omitidos": productos_omitidos,
            "consejo": f"Los huevos se venden por '{unidad_sugerida}', no por '{unidad_normalizada}'" if unidad_inapropiada else ""
        }
        
        print(f"✅ Análisis completado exitosamente")
        print(f"📋 Resultado: {estado} - {mensaje_estado}")
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