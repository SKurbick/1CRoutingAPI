import base64
import datetime
import zipfile
from pprint import pprint
from typing import List

from app.models import DocsData
from app.database.repositories import DocsRepository
from app.models import MetawildsData, AllProductsData
from app.infrastructure.WildberriesAPI.docs import Docs
import datetime
import io
import re
import os
import base64
import zipfile
from pprint import pprint

import requests
import pdfplumber
import json
import pandas as pd


class DocsService:
    def __init__(
            self,
            docs_repository: DocsRepository,
    ):
        self.docs_repository = docs_repository

    async def get_docs(self, date_from: datetime.date, date_to: datetime.date) -> List[DocsData]:
        tokens = await self.docs_repository.get_tokens()
        pprint(tokens)
        token = tokens['ВЕКТОР']
        docs_wb_api = Docs(token=token)

        docs_list = await docs_wb_api.get_docs_list(str(date_from), str(date_to))

        upd_docs_names = self.get_upd_doc_names(docs_list['data']['documents'])
        pprint(upd_docs_names)
        upd_docs_per_client_zip = await docs_wb_api.get_upd_docs_per_client(upd_docs_names)
        raw_text = self.extract_and_process_pdfs_from_zip(upd_docs_per_client_zip)
        final_data = self.merge_invoice_data(raw_text)
        pprint(final_data)

        return [DocsData(**res) for res in final_data]


    def get_upd_doc_names(self, docs_list_data):
        '''
        Возвращает { 'params' : [{'extension': 'zip', 'serviceName': 'upd-250070987'}, ... ]}
        (структура, готовая для загрузки в POST-запрос)
        '''
        return {'params': [{"extension": i['extensions'][0], "serviceName": i['serviceName']} for i in docs_list_data]}

    def extract_and_process_pdfs_from_zip(self, zip_data, parse_func=None):
        """
        Extracts PDFs from nested ZIPs.
        - Always includes raw_data (text + tables) on success
        - Includes parsed_data only if parse_func is given
        - On failure: saves pdf_base64 for recovery, no raw_data
        """
        results = []

        for inner_zip_name, pdf_filename, pdf_data in self.iter_inner_pdfs(zip_data):
            try:
                # Extract structured raw data (text, tables)
                raw_data = self.extract_pdf_data(pdf_data)

                # Build success result
                item = {
                    "filename": pdf_filename,
                    "inner_zip_name": inner_zip_name,  # ← NEW
                    "pdf_base64": base64.b64encode(pdf_data).decode('utf-8'),  # ← NEW
                    "raw_data": raw_data
                }
                if parse_func is not None:
                    item["parsed_data"] = parse_func(raw_data)

                results.append(item)

            except Exception as e:
                # Extraction failed → keep base64 for later retry
                results.append({
                    "filename": pdf_filename,
                    "inner_zip_name": inner_zip_name,  # ← NEW
                    "error": str(e),
                    "pdf_base64": base64.b64encode(pdf_data).decode('utf-8')
                })
                print(f"Failed to extract raw_data: {pdf_filename} – {e}")

        return results

    def iter_inner_pdfs(self, zip_data):
        """
        Yield (inner_zip_name, pdf_filename, pdf_bytes) from outer ZIP → inner ZIPs → PDFs
        """
        if isinstance(zip_data, str):
            zip_data = base64.b64decode(zip_data)

        with zipfile.ZipFile(io.BytesIO(zip_data)) as outer_zip:
            for outer_info in outer_zip.infolist():
                if outer_info.filename.lower().endswith('.zip'):
                    inner_zip_data = outer_zip.read(outer_info)
                    inner_zip_name = outer_info.filename  # Capture inner zip name
                    with zipfile.ZipFile(io.BytesIO(inner_zip_data)) as inner_zip:
                        for file_info in inner_zip.infolist():
                            if file_info.filename.lower().endswith('.pdf'):
                                yield inner_zip_name, file_info.filename, inner_zip.read(file_info)

    def extract_pdf_data(self, pdf_data):
        """
        Extract raw text and tables from all pages of a PDF.
        Returns: dict with page-by-page content.
        """
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            result = {
                "pages": []
            }
            for i, page in enumerate(pdf.pages):
                result["pages"].append({
                    "page_num": i + 1,
                    "text": page.extract_text(),
                    "tables": page.extract_tables()
                })
            return result

    def merge_invoice_data(self, res):
        """
        Combine header data and service rows from parsed PDF results.

        Args:
            res (list): Output of extract_and_process_pdfs_from_zip
                      Each item has 'raw_data', 'filename', 'inner_zip_name', 'pdf_base64'

        Returns:
            list of dicts: Each with header + 'Услуги' + 'pdf_base64' + 'inner_zip_name'
        """
        result = []

        for doc in res:
            main_data = {}
            services = []

            # Extract from all pages
            for page in doc['raw_data']['pages']:
                text = page.get('text', '')

                # Extract header (only once, but we collect across pages if needed)
                if not main_data:
                    header = self.extract_invoice_data(text)
                    if header:
                        main_data = header

                # Extract from all tables on page
                if 'tables' in page:
                    for table in page['tables']:
                        if table:  # Skip empty tables
                            rows = self.process_invoice_table(table)
                            services.extend(rows)

            # Only include if we have at least header or services
            if main_data or services:
                combined = main_data or {}
                combined['Услуги'] = services
                # Add metadata
                combined['inner_zip_name'] = doc['inner_zip_name']
                combined['pdf_base64'] = doc['pdf_base64']
                result.append(combined)

        return result

    def extract_invoice_data(self, text):
        data = {}
        match = re.search(r'Счет-фактура №\s*(\d+) от (\d{2}\.\d{2}\.\d{4})', text)
        if match:
            data["Счёт фактура номер"] = match.group(1)
            data["Счёт фактура дата"] = match.group(2)

        seller_match = re.search(r'Продавец:[^\"]*\"([^\"]+)\"', text)
        data["Наименование продавца"] = seller_match.group(1) if seller_match else None

        inn_seller = re.search(r'ИНН/КПП продавца:\s*([\d/]+)', text)
        if inn_seller:
            parts = inn_seller.group(1).split('/')
            data["ИНН продавца"] = parts[0]
            data["КПП продавца"] = parts[1] if len(parts) > 1 else None
        else:
            data["ИНН продавца"] = data["КПП продавца"] = None

        data["Наименование покупателя"] = self.extract_buyer_name(text)
        # buyer_match = re.search(r'Покупатель:\s*([^"\s][^"]*?)"', text)
        # data["Наименование покупателя"] = buyer_match.group(1) if buyer_match else None

        inn_buyer = re.search(r'ИНН/КПП покупателя:\s*([\d/]+)', text)
        if inn_buyer:
            parts = inn_buyer.group(1).split('/')
            data["ИНН покупателя"] = parts[0]
            data["КПП покупателя"] = parts[1] if len(parts) > 1 else None
        else:
            data["ИНН покупателя"] = data["КПП покупателя"] = None

        # Return only if at least one field is found
        if all(v is None for v in data.values()):
            return {}
        return data

    @staticmethod
    def extract_buyer_name(text):
        # 1. Standard case: Покупатель: "Company Name"
        match = re.search(r'Покупатель:\s*"?([^"\s][^"]*?)"', text)
        if match:
            return match.group(1).strip()

        # 2. Fallback: ИП — take first word after "Индивидуальный предприниматель"
        match = re.search(r'Индивидуальный\s+предприниматель\s+([^\s]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def process_invoice_table(table_data):
        if not table_data or len(table_data) < 2:
            return []

        df = pd.DataFrame(table_data)

        def clean_col(x):
            if not isinstance(x, str) or x is None:
                return ""
            x = re.sub(r'\s+', ' ', x.strip().replace('\n', ' '))
            x = re.sub(r'^[^a-zA-Zа-яА-Я0-9]+|[^a-zA-Zа-яА-Я0-9]+$', '', x)
            return x.lower()

        df.columns = [clean_col(col) for col in df.iloc[0]]
        df = df.drop(df.index[0]).reset_index(drop=True)

        col_mapping = {
            'наименование товара': 'Услуга',
            'без налога - всего': 'Стоимость без НДС',
            'с налогом - всего': 'Стоимость с НДС',
            'налоговая ставка': 'Налоговая ставка'
        }
        selected_cols = {}
        for key_part, standard_name in col_mapping.items():
            matches = [col for col in df.columns if key_part in col]
            if matches:
                selected_cols[standard_name] = matches[0]

        if 'Услуга' not in selected_cols:
            return []

        df_clean = df[list(selected_cols.values())].copy()
        df_clean.columns = list(selected_cols.keys())
        df_clean['Услуга'] = df_clean['Услуга'].str.replace('\n', ' ', regex=False).str.strip()

        df_clean = df_clean.dropna(subset=['Услуга'])
        df_clean = df_clean[df_clean['Услуга'] != ""]
        df_clean = df_clean[
            df_clean['Услуга'].str[0].str.match(r'[a-zA-Zа-яА-Я]', na=False)
        ]

        for col in ('Стоимость без НДС', 'Стоимость с НДС'):
            df_clean[col] = df_clean[col].str.replace(',', '.', regex=False).astype(float)
        return df_clean.to_dict('records')
