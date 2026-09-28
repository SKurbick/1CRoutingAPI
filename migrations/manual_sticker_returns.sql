-- Приходы возвратов по стикерам, отсутствующим в goods_returns_dev.
CREATE TABLE IF NOT EXISTS public.manual_sticker_returns (
    id                 BIGSERIAL PRIMARY KEY,
    incoming_return_id BIGINT NOT NULL,
    sticker_id         VARCHAR(255) NOT NULL,
    product_id         VARCHAR(50) NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_manual_sticker_returns_incoming_return
        FOREIGN KEY (incoming_return_id)
        REFERENCES public.incoming_returns(id),
    CONSTRAINT fk_manual_sticker_returns_product
        FOREIGN KEY (product_id)
        REFERENCES public.products(id),
    CONSTRAINT uq_manual_sticker_returns_incoming_return
        UNIQUE (incoming_return_id),
    CONSTRAINT uq_manual_sticker_returns_sticker
        UNIQUE (sticker_id)
);
