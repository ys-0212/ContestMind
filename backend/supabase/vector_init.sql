-- 1. Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the document chunks table
CREATE TABLE IF NOT EXISTS public.document_chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    problem_id VARCHAR(255) NOT NULL REFERENCES public.problems(problem_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(384) -- all-MiniLM-L6-v2 produces 384-dimensional embeddings
);

-- 3. Create an index for faster similarity searches
-- using inner product or cosine distance. Here we use halfvec for better performance if supported, or standard HNSW.
CREATE INDEX ON public.document_chunks USING hnsw (embedding vector_cosine_ops);

-- 4. Create an RPC function to perform similarity search
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(384),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id VARCHAR(255),
    document TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.chunk_id AS id,
        document_chunks.content AS document,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity
    FROM document_chunks
    -- where 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    -- We can enforce threshold if needed, but standard top K is usually enough
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
