-- Approximate nearest-neighbour index over the precomputed embeddings (cosine distance).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE INDEX IF NOT EXISTS ix_support_articles_embedding_hnsw
    ON "$schema$".support_articles_synced
    USING hnsw (embedding vector_cosine_ops);
