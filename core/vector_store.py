import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

class VectorStore:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Modelo para convertir texto a vectores
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.product_ids = []
        self.dimension = 384 # Dimensión para el modelo MiniLM

    def build_index(self, products_list):
        """
        products_list: Lista de diccionarios con [{'id': 1, 'text': 'Tomate riñón fresco'}]
        """
        if not products_list:
            return

        texts = [p['text'] for p in products_list]
        self.product_ids = [p['id'] for p in products_list]

        # Crear los vectores
        embeddings = self.model.encode(texts)
        embeddings = np.array(embeddings).astype('float32')

        # Crear el índice FAISS
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
        print(f"Índice vectorial creado con {len(texts)} productos.")

    def search(self, query, top_k=3):
        """
        Busca los productos más relevantes para una consulta
        """
        if self.index is None:
            return []

        query_vector = self.model.encode([query]).astype('float32')
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx in indices[0]:
            if idx != -1:
                results.append(self.product_ids[idx])
        return results

# Instancia global para ser usada en los servicios
vector_store = VectorStore()