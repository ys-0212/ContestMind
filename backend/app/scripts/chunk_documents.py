"""
This script reads the processed problems, chunks their text content,
and saves the chunks to a new JSONL file. This is the first step in the
embedding pipeline.
"""
import json
import logging
from pathlib import Path
from typing import List

from app.core.config import settings
from app.schemas.problem import Problem

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- Chunking Configuration ---
# A simple paragraph-based strategy is good for an MVP.
# We can introduce more sophisticated strategies (e.g., token-based with overlap) later.
MIN_CHUNK_SIZE_CHARS = 100  # Merge chunks smaller than this with the previous one.


def chunk_text(text: str) -> List[str]:
    """
    Splits text into chunks based on paragraphs. Merges small chunks.
    """
    if not text:
        return []

    # Split by double newlines, which typically separate paragraphs
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        p_stripped = p.strip()
        if not p_stripped:
            continue

        # If the current chunk is empty, start a new one
        if not current_chunk:
            current_chunk = p_stripped
        # If adding the new paragraph keeps the chunk reasonable, or if the paragraph is huge itself
        else:
            # If the current chunk is too small, always append
            if len(current_chunk) < MIN_CHUNK_SIZE_CHARS:
                 current_chunk += "\n\n" + p_stripped
            else:
                # Otherwise, the current chunk is large enough, so we save it and start a new one
                chunks.append(current_chunk)
                current_chunk = p_stripped

    # Add the last remaining chunk
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks


def main():
    logger.info("Starting document chunking process...")

    input_file = settings.PROCESSED_DATA_DIR / "problems.jsonl"
    output_dir = settings.CHUNKS_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "chunks.jsonl"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. Please run the preprocessing pipeline first.")
        return

    chunks_count = 0
    problems_processed = 0
    
    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8") as f_out:
        
        for line in f_in:
            try:
                data = json.loads(line)
                problem = Problem(**data)
                problems_processed += 1

                # Build a rich document from all available fields.
                # Header is always included; statement and editorial are appended when present.
                header_parts = [f"Problem: {problem.title}"]
                if problem.rating:
                    header_parts.append(f"Difficulty Rating: {problem.rating}")
                if problem.tags:
                    header_parts.append(f"Algorithm Tags: {', '.join(problem.tags)}")
                header = "\n".join(header_parts)

                body_parts = []
                if problem.statement and problem.statement.strip():
                    body_parts.append(f"Problem Statement:\n{problem.statement.strip()}")
                if problem.editorial and problem.editorial.strip():
                    body_parts.append(f"Editorial:\n{problem.editorial.strip()}")

                full_text = header
                if body_parts:
                    full_text += "\n\n" + "\n\n".join(body_parts)

                # Chunk only if there is substantial body content; otherwise keep as single doc.
                if body_parts:
                    text_chunks = chunk_text(full_text)
                    if not text_chunks:
                        text_chunks = [full_text]
                else:
                    text_chunks = [full_text]

                for i, chunk_content in enumerate(text_chunks):
                    chunk_id = f"{problem.problem_id}::{i}"
                    chunk_data = {
                        "chunk_id": chunk_id,
                        "problem_id": problem.problem_id,
                        "chunk_index": i,
                        "content": chunk_content,
                        "metadata": problem.model_dump(exclude={"statement", "editorial"})
                    }
                    f_out.write(json.dumps(chunk_data) + "\n")
                    chunks_count += 1

            except json.JSONDecodeError:
                logger.warning(f"Skipping malformed line: {line.strip()}")
            except Exception as e:
                logger.error(f"An error occurred processing line: {line.strip()}", exc_info=True)

    logger.info(f"Chunking complete. Processed {problems_processed} problems.")
    logger.info(f"Generated {chunks_count} chunks.")
    logger.info(f"Chunks saved to: {output_file}")


if __name__ == "__main__":
    main()
