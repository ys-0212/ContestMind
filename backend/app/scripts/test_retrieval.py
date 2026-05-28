"""
A simple script to test the semantic retrieval functionality.
It takes a sample query and prints the top N most relevant results
from the ChromaDB collection.
"""
import logging
import pprint

from app.services.chroma_service import ChromaService

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Initializing ChromaDB service for retrieval test...")
    try:
        chroma_service = ChromaService()
    except Exception as e:
        logger.error("Failed to start Chroma service. Is the database path correct?", exc_info=True)
        return

    if chroma_service.get_collection_count() == 0:
        logger.error("ChromaDB collection is empty. Please run the `build_vector_index.py` script first.")
        return

    # --- Sample Queries ---
    queries = [
        "dynamic programming on trees",
        "problems with bitmasking",
        "constructive algorithms with greedy approach",
        "shortest path on a grid"
    ]

    for query in queries:
        logger.info(f"\n{'='*20} TESTING QUERY: '{query}' {'='*20}")
        
        results = chroma_service.query(query_text=query, top_k=3)

        if not results:
            logger.warning("Query returned no results.")
        else:
            logger.info(f"Found {len(results)} results:")
            for result in results:
                # Pretty print for readability
                pprint.pprint({
                    "distance": f"{result['distance']:.4f}",
                    "problem_id": result['metadata'].get('problem_id'),
                    "title": result['metadata'].get('title'),
                    "rating": result['metadata'].get('rating'),
                    "tags": result['metadata'].get('tags'),
                    "document": result['document'][:200] + "..." # Truncate for display
                })


if __name__ == "__main__":
    main()
