# d:\Project\ContestMind\backend\app\scripts\seed_vectors.py
import json
import logging
from sentence_transformers import SentenceTransformer
from typing import Dict, Any
from supabase import create_client, Client

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 100

def main():
    logger.info("Starting pgvector seed process...")
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
        
    logger.info("Initializing Supabase client...")
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return
        
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    logger.info(f"Reading chunks from {input_file}...")
    chunks = [json.loads(line) for line in open(input_file, "r", encoding="utf-8")]
    
    if not chunks:
        logger.warning("No chunks found to process. Exiting.")
        return

    logger.info(f"Found {len(chunks)} chunks to embed and upload.")

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(chunks) - 1) // BATCH_SIZE + 1
        logger.info(f"Processing batch {batch_num}/{total_batches}...")

        documents = [chunk['content'] for chunk in batch]
        
        # Generate embeddings
        embeddings = model.encode(documents, show_progress_bar=False).tolist()

        # Prepare records for Supabase insert
        records = []
        for idx, chunk in enumerate(batch):
            records.append({
                "chunk_id": chunk["chunk_id"],
                "problem_id": chunk["problem_id"],
                "content": chunk["content"],
                "metadata": chunk["metadata"],
                "embedding": embeddings[idx]
            })

        try:
            # Upsert into Supabase
            response = supabase.table("document_chunks").upsert(records).execute()
        except Exception as e:
            logger.error(f"Failed to upload batch to Supabase.", exc_info=True)

    logger.info("Vector index seed process complete!")

if __name__ == "__main__":
    main()
