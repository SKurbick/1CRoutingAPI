from app.service.docs import DocsService


BASE_DOCUMENT_TEXT = """
Продавец: "РВБ"
ИНН/КПП продавца: 9714053621/507401001
Покупатель: "Лопатина"
ИНН/КПП покупателя: 771575954343/
"""


def test_extracts_legacy_invoice_number_and_date():
    service = DocsService(docs_repository=None)
    result = service.extract_invoice_data(
        "Счет-фактура № 301548886 от 07.06.2026\n" + BASE_DOCUMENT_TEXT
    )

    assert result["Счёт фактура номер"] == "301548886"
    assert result["Счёт фактура дата"] == "07.06.2026"


def test_extracts_upd_number_and_date_from_document_text():
    service = DocsService(docs_repository=None)
    result = service.extract_invoice_data(
        "Документ об отгрузке Универсальный передаточный документ, "
        "№ 302613165 от 14.06.2026 г.\n" + BASE_DOCUMENT_TEXT
    )

    assert result["Счёт фактура номер"] == "302613165"
    assert result["Счёт фактура дата"] == "14.06.2026"


def test_falls_back_to_upd_pdf_filename():
    service = DocsService(docs_repository=None)
    result = service.extract_invoice_data(
        BASE_DOCUMENT_TEXT,
        filename="УПД №302613165 от 14.06.2026.pdf"
    )

    assert result["Счёт фактура номер"] == "302613165"
    assert result["Счёт фактура дата"] == "14.06.2026"


def test_legacy_text_has_priority_over_upd_filename():
    service = DocsService(docs_repository=None)
    result = service.extract_invoice_data(
        "Счет-фактура № 301548886 от 07.06.2026\n" + BASE_DOCUMENT_TEXT,
        filename="УПД №999999999 от 01.01.2000.pdf"
    )

    assert result["Счёт фактура номер"] == "301548886"
    assert result["Счёт фактура дата"] == "07.06.2026"
