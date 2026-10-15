-- Application-owned table: records whether a search result helped the user.
CREATE TABLE IF NOT EXISTS public.search_feedback (
    feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    article_id  BIGINT      NOT NULL,
    query_text  TEXT        NOT NULL,
    helpful     BOOLEAN     NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_search_feedback_article_id
    ON public.search_feedback (article_id);
