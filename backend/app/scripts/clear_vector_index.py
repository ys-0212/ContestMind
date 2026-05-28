# d:\Project\ContestMind\backend\app\scripts\clear_vector_index.py
import logging
import chromadb
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Attempting to clear the ChromaDB collection...")
    try:
        client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
        logger.info(f"Client connected. Deleting collection: {settings.CHROMA_COLLECTION_NAME}")
        client.delete_collection(name=settings.CHROMA_COLLECTION_NAME)
        logger.info("Collection deleted successfully.")
    except ValueError as e:
        # This error is often raised if the collection doesn't exist, which is fine.
        logger.warning(f"Could not delete collection (it may not exist): {e}")
    except Exception as e:
        logger.error("An unexpected error occurred while clearing the collection.", exc_info=True)

if __name__ == "__main__":
    main()