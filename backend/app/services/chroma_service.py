"""
Service to manage all interactions with ChromaDB for vector storage and retrieval.
"""
import chromadb
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class ChromaService:
    def __init__(self):
        """
        Initializes the ChromaDB client and gets or creates the collection.
        """
        try:
            self.client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME
            )
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("ChromaDB client initialized and collection is ready.")
            logger.info(f"ChromaDB is persisting data to: {settings.CHROMA_PERSIST_DIR}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}", exc_info=True)
            raise

    def add_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """
        Adds a batch of documents and their embeddings to the collection.

        Args:
            ids: A list of unique identifiers for each chunk.
            documents: A list of the text content of each chunk.
            metadatas: A list of dictionaries containing metadata for each chunk.
        """
        if not ids:
            logger.warning("Attempted to add an empty list of documents. Skipping.")
            return

        try:
            # Generate embeddings explicitly to match ingest logic exactly
            embeddings = self.embedding_model.encode(documents, show_progress_bar=False).tolist()
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(ids)} documents to the collection.")
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}", exc_info=True)

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a semantic search query against the vector collection.

        Args:
            query_text: The user's query string.
            top_k: The number of top results to return.

        Returns:
            A list of dictionaries, where each dictionary contains the
            retrieved document, its metadata, and distance score.
        """
        try:
            # Generate explicit embeddings to guarantee match with index
            query_embedding = self.embedding_model.encode([query_text])[0].tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
            
            # Flatten the results for easier processing
            if not results or not results.get('ids') or not results['ids'][0]:
                return []

            ids = results['ids'][0]
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]

            return [
                {
                    "id": ids[i],
                    "document": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i]
                }
                for i in range(len(ids))
            ]

        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}", exc_info=True)
            return []

    def get_collection_count(self) -> int:
        """Returns the number of items in the collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}", exc_info=True)
            return 0

# Optional: Singleton instance for easy access across the app
# chroma_service = ChromaService()
