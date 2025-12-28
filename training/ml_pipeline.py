"""
training/ml_pipeline.py - Pipeline ML que consume tu API backend
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import joblib
import os
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from core.api_client import api_client
from models.ml_models.demand_model import DemandPredictor
from models.ml_models.price_model import PriceOptimizer
from models.ml_models.recommender_model import ProductRecommender


class MLPipeline:
    """Pipeline ML que consume datos de tu API backend existente"""
    
    def __init__(self, models_dir: str = "models/ml_models/saved"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar modelos
        self.demand_model = DemandPredictor()
        self.price_model = PriceOptimizer()
        self.recommender_model = ProductRecommender()
        
        # Tracking
        self.training_history = []
        self.is_trained = False
    
    def load_and_prepare_data(self) -> Dict[str, pd.DataFrame]:
        """
        Carga datos desde tu API backend
        
        Returns:
            Dict con DataFrames preparados
        """
        print("📊 Cargando datos desde tu API backend...")
        print(f"   API: {api_client.base_url}")
        
        try:
            # Ventas históricas
            ventas = api_client.get_historical_sales(days_back=365)
            print(f"✓ Ventas cargadas: {len(ventas)} registros")
            
            # Productos
            productos = api_client.get_products_with_stock()
            print(f"✓ Productos cargados: {len(productos)} items")
            
            # Historial de clientes
            clientes = api_client.get_client_purchase_history()
            print(f"✓ Historial de clientes cargado: {len(clientes)} registros")
            
            # Tendencias
            tendencias = api_client.get_market_trends(dias=90)
            print(f"✓ Tendencias cargadas: {len(tendencias)} registros")
            
            return {
                'ventas': ventas,
                'productos': productos,
                'clientes': clientes,
                'tendencias': tendencias
            }
            
        except Exception as e:
            print(f"❌ Error cargando datos de la API: {e}")
            print("   Verifica que tu backend esté corriendo y la URL sea correcta")
            return {
                'ventas': pd.DataFrame(),
                'productos': pd.DataFrame(),
                'clientes': pd.DataFrame(),
                'tendencias': pd.DataFrame()
            }
    
    def prepare_demand_features(self, ventas: pd.DataFrame) -> pd.DataFrame:
        """Prepara features para modelo de demanda"""
        if ventas.empty:
            print("⚠️  No hay datos de ventas para preparar")
            return pd.DataFrame()
        
        ventas = ventas.copy()
        
        # Asegurar que fecha sea datetime
        if 'fecha' in ventas.columns:
            ventas['fecha'] = pd.to_datetime(ventas['fecha'])
        
        # Features temporales (si no vienen de la API)
        if 'dia_semana' not in ventas.columns and 'fecha' in ventas.columns:
            ventas['dia_mes'] = ventas['fecha'].dt.day
            ventas['semana_año'] = ventas['fecha'].dt.isocalendar().week
        
        # Features de producto
        if 'producto_id' in ventas.columns and 'cantidad' in ventas.columns:
            producto_stats = ventas.groupby('producto_id').agg({
                'cantidad': ['mean', 'std', 'min', 'max'],
                'total': ['sum', 'mean'] if 'total' in ventas.columns else 'cantidad'
            }).reset_index()
            
            producto_stats.columns = ['producto_id', 'cant_mean', 'cant_std', 'cant_min', 
                                      'cant_max', 'total_sum', 'total_mean']
            
            ventas = ventas.merge(producto_stats, on='producto_id', how='left')
        
        # Tendencia últimos 7 días
        if 'fecha' in ventas.columns and 'producto_id' in ventas.columns:
            ventas = ventas.sort_values('fecha')
            ventas['demanda_7d'] = ventas.groupby('producto_id')['cantidad'].transform(
                lambda x: x.rolling(window=7, min_periods=1).mean()
            )
        
        return ventas
    
    def prepare_price_features(self, ventas: pd.DataFrame, productos: pd.DataFrame) -> pd.DataFrame:
        """Prepara features para modelo de precio"""
        if ventas.empty or productos.empty:
            return pd.DataFrame()
        
        # Merge
        precio_data = ventas.merge(
            productos, 
            left_on='producto_id', 
            right_on='id', 
            how='left',
            suffixes=('', '_prod')
        )
        
        # Features de precio
        if 'precio_unitario' in precio_data.columns and 'precio_venta' in precio_data.columns:
            precio_data['precio_vs_promedio'] = precio_data['precio_unitario'] / precio_data['precio_venta'].replace(0, 1)
        
        # Competitividad por categoría
        if 'categoria' in precio_data.columns and 'precio_unitario' in precio_data.columns:
            categoria_precios = precio_data.groupby('categoria')['precio_unitario'].agg(['mean', 'std']).reset_index()
            categoria_precios.columns = ['categoria', 'precio_cat_mean', 'precio_cat_std']
            precio_data = precio_data.merge(categoria_precios, on='categoria', how='left')
        
        # Margen
        if 'precio_unitario' in precio_data.columns and 'precio_costo' in precio_data.columns:
            precio_data['margen'] = (precio_data['precio_unitario'] - precio_data['precio_costo']) / precio_data['precio_costo'].replace(0, 1)
        
        return precio_data
    
    def prepare_recommendation_features(
        self, 
        clientes: pd.DataFrame, 
        ventas: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepara matriz de recomendaciones"""
        if clientes.empty or ventas.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Matriz usuario-item
        try:
            user_item_matrix = clientes.pivot_table(
                index='cliente_id',
                columns='producto_id',
                values='veces_comprado' if 'veces_comprado' in clientes.columns else 'cantidad_total',
                fill_value=0
            )
        except Exception as e:
            print(f"⚠️  Error creando matriz usuario-item: {e}")
            user_item_matrix = pd.DataFrame()
        
        # Features de productos
        if 'producto_id' in ventas.columns:
            producto_features = ventas.groupby('producto_id').agg({
                'categoria': 'first' if 'categoria' in ventas.columns else lambda x: 'general',
                'cantidad': 'sum',
                'total': 'sum' if 'total' in ventas.columns else 'cantidad',
                'precio_unitario': 'mean' if 'precio_unitario' in ventas.columns else lambda x: 0
            }).reset_index()
        else:
            producto_features = pd.DataFrame()
        
        return user_item_matrix, producto_features
    
    def train_all_models(self, retrain_from_scratch: bool = True) -> Dict[str, Dict]:
        """
        Entrena todos los modelos con datos de tu API
        
        Args:
            retrain_from_scratch: Si reentrenar desde cero
            
        Returns:
            Dict con métricas
        """
        print("\n🚀 Iniciando entrenamiento con datos de tu API...")
        print("=" * 70)
        
        start_time = datetime.now()
        results = {}
        
        # 1. Cargar datos de tu API
        data = self.load_and_prepare_data()
        
        # Verificar que hay datos suficientes
        if data['ventas'].empty or data['productos'].empty:
            print("\n❌ No hay suficientes datos para entrenar")
            print("   Verifica que tu API esté devolviendo datos correctamente")
            return results
        
        # 2. Modelo de demanda
        print("\n📈 Entrenando modelo de demanda...")
        try:
            demand_data = self.prepare_demand_features(data['ventas'])
            
            if not demand_data.empty and 'cantidad' in demand_data.columns:
                # Seleccionar features disponibles
                feature_cols = [
                    'dia_semana', 'mes', 'es_fin_semana', 'cant_mean', 'demanda_7d'
                ]
                available_features = [col for col in feature_cols if col in demand_data.columns]
                
                if available_features:
                    X_demand = demand_data[available_features]
                    y_demand = demand_data['cantidad']
                    
                    # Codificar categóricas si existen
                    if 'temporada' in demand_data.columns:
                        X_demand = pd.concat([
                            X_demand,
                            pd.get_dummies(demand_data['temporada'], prefix='temp')
                        ], axis=1)
                    
                    # Rellenar NaN
                    X_demand = X_demand.fillna(X_demand.mean())
                    
                    demand_metrics = self.demand_model.train(X_demand, y_demand)
                    results['demand'] = demand_metrics
                    print(f"✓ Modelo de demanda entrenado - R²: {demand_metrics.get('r2_score', 0):.3f}")
                else:
                    print("⚠️  No hay features suficientes para modelo de demanda")
            else:
                print("⚠️  Datos de demanda insuficientes")
        except Exception as e:
            print(f"❌ Error entrenando modelo de demanda: {e}")
        
        # 3. Modelo de precio
        print("\n💰 Entrenando modelo de precio...")
        try:
            price_data = self.prepare_price_features(data['ventas'], data['productos'])
            
            if not price_data.empty and 'precio_unitario' in price_data.columns:
                feature_cols = [
                    'precio_costo', 'stock_actual', 'cant_mean', 
                    'precio_vs_promedio', 'margen', 'precio_cat_mean'
                ]
                available_features = [col for col in feature_cols if col in price_data.columns]
                
                if available_features and len(available_features) >= 2:
                    X_price = price_data[available_features].fillna(0)
                    y_price = price_data['precio_unitario']
                    
                    price_metrics = self.price_model.train(X_price, y_price)
                    results['price'] = price_metrics
                    print(f"✓ Modelo de precio entrenado - MAE: {price_metrics.get('mae', 0):.2f}")
                else:
                    print("⚠️  No hay features suficientes para modelo de precio")
            else:
                print("⚠️  Datos de precio insuficientes")
        except Exception as e:
            print(f"❌ Error entrenando modelo de precio: {e}")
        
        # 4. Sistema de recomendaciones
        print("\n🎯 Entrenando sistema de recomendaciones...")
        try:
            user_item_matrix, product_features = self.prepare_recommendation_features(
                data['clientes'],
                data['ventas']
            )
            
            if not user_item_matrix.empty:
                recommender_metrics = self.recommender_model.train(
                    user_item_matrix,
                    product_features
                )
                results['recommender'] = recommender_metrics
                print(f"✓ Sistema de recomendaciones entrenado")
            else:
                print("⚠️  Datos insuficientes para recomendaciones")
        except Exception as e:
            print(f"❌ Error entrenando recomendaciones: {e}")
        
        # 5. Guardar modelos
        if results:
            self.save_all_models()
            self.is_trained = True
        
        # Registrar entrenamiento
        training_time = (datetime.now() - start_time).total_seconds()
        training_record = {
            'timestamp': datetime.now().isoformat(),
            'training_time_seconds': training_time,
            'samples_used': len(data['ventas']),
            'metrics': results,
            'api_source': api_client.base_url
        }
        self.training_history.append(training_record)
        
        print("\n" + "=" * 70)
        print(f"✅ Entrenamiento completado en {training_time:.1f} segundos")
        print(f"   Datos obtenidos de: {api_client.base_url}")
        print("=" * 70)
        
        return results
    
    def predict_demand(self, producto_id: int, fecha: datetime) -> Dict:
        """Predice demanda para un producto"""
        if not self.is_trained:
            return {
                'error': 'Modelos no entrenados',
                'message': 'Ejecuta el entrenamiento primero'
            }
        
        # Preparar features
        features = pd.DataFrame([{
            'dia_semana': fecha.weekday(),
            'mes': fecha.month,
            'es_fin_semana': 1 if fecha.weekday() >= 5 else 0,
            'cant_mean': 0,
            'demanda_7d': 0,
        }])
        
        # Agregar features que el modelo espera
        for col in self.demand_model.feature_names:
            if col not in features.columns:
                features[col] = 0
        
        features = features[self.demand_model.feature_names]
        
        prediction = self.demand_model.predict(features)[0]
        
        return {
            'producto_id': producto_id,
            'fecha': fecha.isoformat(),
            'demanda_predicha': float(prediction),
            'confianza': 'alta' if prediction > 10 else 'media',
            'api_source': api_client.base_url
        }
    
    def optimize_price(self, producto_id: int) -> Dict:
        """Optimiza precio consultando datos de tu API"""
        try:
            # Obtener datos del producto desde tu API
            producto = api_client.get_producto_by_id(producto_id)
            
            if not producto:
                return {'error': 'Producto no encontrado en la API'}
            
            # Preparar features
            features = pd.DataFrame([{
                'precio_costo': producto.get('precio_costo', 0),
                'stock_actual': producto.get('stock_actual', 100),
                'cant_mean': 0,
                'precio_vs_promedio': 1.0,
                'margen': 0.3,
                'precio_cat_mean': producto.get('precio_venta', 0)
            }])
            
            if self.is_trained:
                precio_optimo = self.price_model.predict(features)[0]
            else:
                precio_optimo = producto.get('precio_venta', 0) * 1.05
            
            return {
                'producto_id': producto_id,
                'precio_actual': float(producto.get('precio_venta', 0)),
                'precio_optimo': float(precio_optimo),
                'cambio_sugerido': float(precio_optimo - producto.get('precio_venta', 0)),
                'api_source': api_client.base_url
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_recommendations(self, cliente_id: int, n: int = 5) -> List[Dict]:
        """Obtiene recomendaciones"""
        if not self.is_trained:
            return []
        
        try:
            recommendations = self.recommender_model.recommend(cliente_id, n)
            
            # Enriquecer con datos de tu API
            result = []
            for rec in recommendations:
                producto = api_client.get_producto_by_id(rec['producto_id'])
                if producto:
                    result.append({
                        'producto_id': rec['producto_id'],
                        'nombre': producto.get('nombre'),
                        'categoria': producto.get('categoria'),
                        'precio': float(producto.get('precio_venta', 0)),
                        'score': rec['score'],
                        'razon': rec.get('reason', 'Basado en tu historial')
                    })
            
            return result
        except:
            return []
    
    def save_all_models(self):
        """Guarda modelos"""
        print("\n💾 Guardando modelos...")
        self.demand_model.save(self.models_dir / "demand_model.pkl")
        self.price_model.save(self.models_dir / "price_model.pkl")
        self.recommender_model.save(self.models_dir / "recommender_model.pkl")
        print(f"✓ Modelos guardados en {self.models_dir}")
    
    def load_all_models(self) -> bool:
        """Carga modelos guardados"""
        try:
            self.demand_model.load(self.models_dir / "demand_model.pkl")
            self.price_model.load(self.models_dir / "price_model.pkl")
            self.recommender_model.load(self.models_dir / "recommender_model.pkl")
            self.is_trained = True
            print("✓ Modelos cargados exitosamente")
            return True
        except Exception as e:
            print(f"⚠️  Error cargando modelos: {e}")
            self.is_trained = False
            return False
    
    def schedule_retraining(self, frequency_days: int = 7):
        """Configura reentrenamiento automático"""
        
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=self.train_all_models,
            trigger='interval',
            days=frequency_days,
            id='retrain_models',
            replace_existing=True
        )
        scheduler.start()
        
        print(f"✓ Reentrenamiento automático cada {frequency_days} días")


# Instancia global
ml_pipeline = MLPipeline()