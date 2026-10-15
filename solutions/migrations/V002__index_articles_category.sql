-- Secondary index for category-filtered searches on the synced articles.
CREATE INDEX IF NOT EXISTS ix_support_articles_category
    ON "$schema$".support_articles_synced (category);
