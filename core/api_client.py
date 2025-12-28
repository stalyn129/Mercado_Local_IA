"""
core/api_client.py - Cliente para consumir la API existente de tu backend
"""
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from functools import lru_cache
import os


class APIClient:
    """
    Cliente para consumir la API REST existente de tu backend
    Reemplaza la conexión directa a base de datos
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Inicializa el cliente API
        
        Args:
            base_url: URL base de tu API (ej: http://localhost:3000/api)
            api_key: API key si tu backend requiere autenticación
        """
        self.base_url = base_url or os.getenv('BACKEND_API_URL', 'http://localhost:3000/api')
        self.api_key = api_key or os.getenv('BACKEND_API_KEY')
        
        # Headers por defecto
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Timeout por defecto
        self.timeout = 30
        
        print(f"🔌 Cliente API inicializado: {self.base_url}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Método genérico para hacer requests
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Endpoint sin el base_url (ej: /productos)
            params: Query parameters
            data: Body data para POST/PUT
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en request a {url}: {e}")
            # Retornar estructura vacía para no romper el flujo
            return {'data': [], 'error': str(e)}
    
    # ============= PRODUCTOS =============
    
    def get_products_with_stock(self) -> pd.DataFrame:
        """
        Obtiene productos con información de stock
        
        Adapta esto según los endpoints de tu API:
        - GET /productos
        - GET /productos/con-stock
        - GET /inventario
        """
        # Ejemplo: si tu endpoint es GET /productos
        response = self._make_request('GET', '/productos')
        
        # Adaptar según la estructura de respuesta de tu API
        # Ejemplo 1: Si devuelve { data: [...] }
        productos = response.get('data', [])
        
        # Ejemplo 2: Si devuelve directamente el array
        # productos = response if isinstance(response, list) else []
        
        if not productos:
            print("⚠️  No se obtuvieron productos de la API")
            return pd.DataFrame()
        
        df = pd.DataFrame(productos)
        
        # Normalizar nombres de columnas según lo que espera tu ML
        # Ajusta esto según los nombres de campos de tu API
        column_mapping = {
            # Tu API -> Nombre esperado
            'id': 'id',
            'nombre': 'nombre',
            'categoria': 'categoria',
            'precioVenta': 'precio_venta',  # Si tu API usa camelCase
            'precioCosto': 'precio_costo',
            'stock': 'stock_actual',
            'stockMinimo': 'stock_minimo',
            'stockMaximo': 'stock_maximo',
            # Agrega más mappings según tu API
        }
        
        # Renombrar columnas si es necesario
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Agregar columnas faltantes con valores por defecto
        required_columns = [
            'id', 'nombre', 'categoria', 'precio_venta', 'precio_costo',
            'stock_actual', 'stock_minimo', 'stock_maximo'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                if 'stock' in col:
                    df[col] = 100
                elif 'precio' in col:
                    df[col] = 0.0
                else:
                    df[col] = None
        
        return df
    
    # ============= VENTAS =============
    
    def get_historical_sales(self, days_back: int = 365) -> pd.DataFrame:
        """
        Obtiene histórico de ventas
        
        Endpoint esperado: GET /ventas?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
        O: GET /ventas/historico?dias=365
        """
        fecha_inicio = datetime.now() - timedelta(days=days_back)
        
        # Opción 1: Si tu API acepta parámetros de fecha
        params = {
            'desde': fecha_inicio.strftime('%Y-%m-%d'),
            'hasta': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Opción 2: Si tu API tiene un endpoint específico
        # params = {'dias': days_back}
        # endpoint = '/ventas/historico'
        
        response = self._make_request('GET', '/ventas', params=params)
        ventas = response.get('data', [])
        
        if not ventas:
            print("⚠️  No se obtuvieron ventas de la API")
            return pd.DataFrame()
        
        df = pd.DataFrame(ventas)
        
        # Normalizar columnas
        column_mapping = {
            'id': 'id',
            'productoId': 'producto_id',
            'clienteId': 'cliente_id',
            'cantidad': 'cantidad',
            'precioUnitario': 'precio_unitario',
            'total': 'total',
            'fecha': 'fecha',
            'hora': 'hora',
            'producto': 'producto_nombre',
            # Agrega más según tu API
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Convertir fecha a datetime
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Agregar features temporales si no vienen de la API
        if 'fecha' in df.columns and 'dia_semana' not in df.columns:
            df['dia_semana'] = df['fecha'].dt.dayofweek
            df['mes'] = df['fecha'].dt.month
            df['es_fin_semana'] = df['dia_semana'].isin([5, 6])
            
            # Temporada (ajustar según tu país)
            df['temporada'] = df['mes'].map({
                12: 'verano', 1: 'verano', 2: 'verano',
                3: 'otoño', 4: 'otoño', 5: 'otoño',
                6: 'invierno', 7: 'invierno', 8: 'invierno',
                9: 'primavera', 10: 'primavera', 11: 'primavera'
            })
        
        return df
    
    # ============= CLIENTES =============
    
    def get_client_purchase_history(self, cliente_id: Optional[int] = None) -> pd.DataFrame:
        """
        Obtiene historial de compras por cliente
        
        Endpoint: GET /clientes/{id}/compras o GET /clientes/compras
        """
        if cliente_id:
            endpoint = f'/clientes/{cliente_id}/compras'
        else:
            endpoint = '/clientes/compras'
        
        response = self._make_request('GET', endpoint)
        compras = response.get('data', [])
        
        if not compras:
            return pd.DataFrame()
        
        df = pd.DataFrame(compras)
        
        # Normalizar
        column_mapping = {
            'clienteId': 'cliente_id',
            'clienteNombre': 'cliente_nombre',
            'productoId': 'producto_id',
            'productoNombre': 'producto_nombre',
            'categoria': 'categoria',
            'vecesComprado': 'veces_comprado',
            'cantidadTotal': 'cantidad_total',
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        return df
    
    # ============= TENDENCIAS =============
    
    def get_market_trends(self, dias: int = 30) -> pd.DataFrame:
        """
        Obtiene tendencias del mercado
        
        Endpoint: GET /estadisticas/tendencias?dias=30
        """
        params = {'dias': dias}
        response = self._make_request('GET', '/estadisticas/tendencias', params=params)
        
        tendencias = response.get('data', [])
        
        if not tendencias:
            return pd.DataFrame()
        
        df = pd.DataFrame(tendencias)
        
        # Normalizar
        column_mapping = {
            'categoria': 'categoria',
            'fecha': 'fecha',
            'cantidadVendida': 'cantidad_vendida',
            'ventaTotal': 'venta_total',
            'precioPromedio': 'precio_promedio',
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
        
        return df
    
    # ============= PREDICCIONES =============
    
    def save_predictions(self, predictions: List[Dict], tipo_prediccion: str):
        """
        Guarda predicciones en el backend
        
        Endpoint: POST /predicciones
        """
        data = {
            'tipo': tipo_prediccion,
            'predicciones': predictions,
            'fecha_prediccion': datetime.now().isoformat()
        }
        
        response = self._make_request('POST', '/predicciones', data=data)
        
        if 'error' in response:
            print(f"⚠️  Error guardando predicciones: {response['error']}")
        else:
            print(f"✅ {len(predictions)} predicciones guardadas")
    
    # ============= HEALTH CHECK =============
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica que la API esté funcionando
        
        Endpoint: GET /health o GET /status
        """
        try:
            response = self._make_request('GET', '/health')
            return {
                'status': 'ok' if response else 'error',
                'api_url': self.base_url,
                'response': response
            }
        except Exception as e:
            return {
                'status': 'error',
                'api_url': self.base_url,
                'error': str(e)
            }
    
    # ============= MÉTODOS ESPECÍFICOS SEGÚN TU BACKEND =============
    
    def get_producto_by_id(self, producto_id: int) -> Dict[str, Any]:
        """Obtiene un producto específico"""
        response = self._make_request('GET', f'/productos/{producto_id}')
        return response.get('data', {})
    
    def get_cliente_by_id(self, cliente_id: int) -> Dict[str, Any]:
        """Obtiene un cliente específico"""
        response = self._make_request('GET', f'/clientes/{cliente_id}')
        return response.get('data', {})
    
    def create_venta(self, venta_data: Dict) -> Dict[str, Any]:
        """Crea una nueva venta"""
        response = self._make_request('POST', '/ventas', data=venta_data)
        return response
    
    def update_stock(self, producto_id: int, cantidad: int) -> Dict[str, Any]:
        """Actualiza el stock de un producto"""
        data = {'cantidad': cantidad}
        response = self._make_request('PUT', f'/productos/{producto_id}/stock', data=data)
        return response
    
    # ============= BÚSQUEDAS =============
    
    def search_products(self, query: str) -> List[Dict]:
        """
        Busca productos por nombre o categoría
        
        Endpoint: GET /productos/buscar?q=query
        """
        params = {'q': query}
        response = self._make_request('GET', '/productos/buscar', params=params)
        return response.get('data', [])
    
    # ============= DASHBOARD =============
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Obtiene datos para el dashboard
        
        Endpoint: GET /dashboard
        """
        response = self._make_request('GET', '/dashboard')
        return response.get('data', {})


# ============= INSTANCIA GLOBAL =============

# Singleton del cliente API
_api_client_instance = None

def get_api_client() -> APIClient:
    """Obtiene la instancia global del cliente API"""
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = APIClient()
    return _api_client_instance

# Alias para compatibilidad con código existente
api_client = get_api_client()