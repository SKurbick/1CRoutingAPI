import asyncio
import json
import time
from pprint import pprint
from typing import List

import aiohttp
from aiohttp import ClientSession


class Docs:

    def __init__(self, token):
        self.token = token
        self.base_url = "https://discounts-prices-api.wildberries.ru"
        self.url = "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/{}"
        self.post_url = "https://discounts-prices-api.wildberries.ru/api/v2/upload/task"

        self.headers = {
            "Authorization": self.token,
            'Content-Type': 'application/json'
        }


    async def get_docs_list(self, begin_date, end_date):
        '''
        Функция достаёт названия (!) документов из WB API.
        Дату принимает в формате "2025-07-15".
        В kwargs можно передать category
        '''
        url = 'https://documents-api.wildberries.ru/api/v1/documents/list'
        params = {
            "beginTime": begin_date,
            "endTime": end_date,
            "category": 'upd'
        }
        async with ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                # response.raise_for_status()
                response_json = await response.json()
                return response_json


    async def get_upd_docs_per_client(self, doc_names):
        '''
        Принимает результат get_upd_doc_names.
        Отдаёт бинарный файл из WB API, содержащий zip-архив
        '''
        url = 'https://documents-api.wildberries.ru/api/v1/documents/download/all'
        async with ClientSession() as session:
            async with session.post(url, json=doc_names, headers=self.headers) as response:
                print(response.json())
                response_json =  await response.json()
                return response_json['data']['document']