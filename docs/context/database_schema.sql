-- Справочный неполный DDL.
-- Единственный источник DDL в репозитории: migrations/return_to_supplier.sql.
-- Не предназначен для применения: исходная migration выполняет DROP TABLE.
-- Остальные используемые таблицы, views, functions и triggers в репозитории не определены.

CREATE TABLE public.return_to_supplier (
    id                       SERIAL PRIMARY KEY,
    guid                     VARCHAR(45) NULL,
    document_number          VARCHAR(30) NULL,
    document_created_at      TIMESTAMP NULL,
    return_date              TIMESTAMP NULL,
    local_vendor_code        VARCHAR(30) NULL,
    product_name             VARCHAR(300) NULL,
    event_status             VARCHAR(20) NULL,
    quantity                 NUMERIC(15, 2) NULL,
    amount_with_vat          NUMERIC(15, 2) NULL,
    amount_without_vat       NUMERIC(15, 2) NULL,
    supplier_name            VARCHAR(150) NULL,
    supplier_code            VARCHAR(30) NULL,
    supply_guid              VARCHAR(45) NULL,
    update_document_datetime TIMESTAMP NULL,
    author_of_the_change     VARCHAR(150) NULL,
    our_organizations_name   VARCHAR(250) NULL,
    currency                 VARCHAR(10) NULL,
    is_valid                 BOOLEAN NULL
);

CREATE INDEX idx_rts_guid ON public.return_to_supplier(guid);
CREATE INDEX idx_rts_is_valid ON public.return_to_supplier(is_valid);
CREATE INDEX idx_rts_local_vendor_code ON public.return_to_supplier(local_vendor_code);

CREATE TABLE public.return_to_supplier_items (
    id                       SERIAL PRIMARY KEY,
    guid                     VARCHAR(45) NOT NULL,
    product_id               VARCHAR(50) NOT NULL,
    quantity                 NUMERIC(10, 3) NOT NULL,
    is_valid                 BOOLEAN DEFAULT TRUE NOT NULL,
    correction_comment       TEXT NULL,
    created_at               TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    return_date              TIMESTAMP NULL,
    document_created_at      TIMESTAMP NULL,
    CONSTRAINT fk_rts_items_product
      FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE
);

CREATE INDEX idx_rts_items_guid ON public.return_to_supplier_items(guid);
CREATE INDEX idx_rts_items_product_id ON public.return_to_supplier_items(product_id);
CREATE INDEX idx_rts_items_is_valid ON public.return_to_supplier_items(is_valid);
