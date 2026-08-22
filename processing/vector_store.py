"""Módulo de persistencia vectorial utilizando ChromaDB."""

import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
COLLECTION_NAME = "personal_clone_texts"


class ChromaStore:
    """Administrador de la base de datos vectorial Chroma."""

    def __init__(self, persist_dir: str = PERSIST_DIR, collection_name: str = COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Crear directorio persistente si no existe
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Inicializar cliente persistente de Chroma
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Usar modelo de embeddings multilingüe optimizado para español
        # 'paraphrase-multilingual-MiniLM-L12-v2' es ligero, rápido y excelente para búsqueda semántica en español
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
        except Exception:
            # Fallback a función por defecto de Chroma si no carga SentenceTransformer
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # Obtener o crear colección
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "Textos limpios y reflexiones para el clon digital"}
        )

    def add_documents(self, ids: list, documents: list, metadatas: list = None):
        """Agrega o actualiza documentos vectorizados en Chroma."""
        if not ids or not documents:
            return
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def query(self, query_text: str, n_results: int = 3, where_filter: dict = None):
        """Busca los fragmentos más similares a una consulta dada."""
        kwargs = {
            "query_texts": [query_text],
            "n_results": n_results
        }
        if where_filter:
            kwargs["where"] = where_filter
            
        results = self.collection.query(**kwargs)
        return results

    def count(self) -> int:
        """Devuelve la cantidad total de vectores almacenados."""
        return self.collection.count()
