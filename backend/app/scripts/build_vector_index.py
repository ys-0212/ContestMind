# d:\Project\ContestMind\backend\app\scripts\build_vector_index.py
import json
import logging
from sentence_transformers import SentenceTransformer
from typing import Dict, Any

from app.core.config import settings
from app.services.chroma_service import ChromaService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans metadata to prevent errors during ChromaDB insertion.
    - Removes keys with empty list values (e.g., 'tags': []).
    """
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, list) and not value:
            # If the value is an empty list, skip this key
            continue
        sanitized[key] = value
    return sanitized

def main():
    logger.info("Starting vector index build process...")
    input_file = settings.CHUNKS_DATA_DIR / "chunks.jsonl"
    if not input_file.exists():
        logger.error(f"Chunks file not found: {input_file}. Please run the chunking script first.")
        return

    logger.info(f"Loading sentence-transformer model: {MODEL_NAME}")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        logger.error("Failed to load model. Ensure 'sentence-transformers' and 'torch' are installed.", exc_info=True)
        return
        
    logger.info("Initializing ChromaDB service...")
    chroma_service = ChromaService()

    logger.info(f"Reading chunks from {input_file}...")
    chunks = [json.loads(line) for line in open(input_file, "r", encoding="utf-8")]
    
    if not chunks:
        logger.warning("No chunks found to process. Exiting.")
        return

    logger.info(f"Found {len(chunks)} chunks to embed and index.")

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(chunks) - 1) // BATCH_SIZE + 1
        logger.info(f"Processing batch {batch_num}/{total_batches}...")

        ids = [chunk['chunk_id'] for chunk in batch]
        documents = [chunk['content'] for chunk in batch]
        
        # --- Sanitization Step ---
        metadatas = [sanitize_metadata(chunk['metadata']) for chunk in batch]

        logger.info(f"Generating embeddings for {len(documents)} documents...")
        embeddings = model.encode(documents, show_progress_bar=False).tolist()

        try:
            chroma_service.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            logger.error(f"Failed to add batch to ChromaDB.", exc_info=True)

    final_count = chroma_service.get_collection_count()
    logger.info("Vector index build process complete.")
    logger.info(f"Total documents in collection: {final_count}")
    
    if final_count == len(chunks):
        logger.info("SUCCESS: Final collection count matches the number of chunks.")
    else:
        logger.error(f"ERROR: Mismatch! Expected {len(chunks)} documents, but found {final_count}.")

if __name__ == "__main__":
    main()