-- Apply before deploying the application with KIZ outbox support.
CREATE TABLE IF NOT EXISTS public.kiz_returns_outbox (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_error TEXT,
    CONSTRAINT kiz_returns_outbox_payload_check CHECK (
        jsonb_typeof(payload) = 'object'
        AND payload ? 'mark_codes'
        AND jsonb_typeof(payload->'mark_codes') = 'array'
        AND payload->'mark_codes' <> '[]'::jsonb
    )
);

CREATE INDEX IF NOT EXISTS ix_kiz_returns_outbox_pending
    ON public.kiz_returns_outbox (next_attempt_at, id)
    WHERE sent_at IS NULL;
