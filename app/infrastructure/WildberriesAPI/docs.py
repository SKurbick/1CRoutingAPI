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

    # async def get_docs_list(self, begin_date, end_date):
    #     '''
    #     Функция достаёт названия (!) документов из WB API.
    #     Дату принимает в формате "2025-07-15".
    #     В kwargs можно передать category
    #     '''
    #     url = 'https://documents-api.wildberries.ru/api/v1/documents/list'
    #     params = {
    #         "beginTime": begin_date,
    #         "endTime": end_date,
    #         "category": 'upd'
    #     }
    #     async with ClientSession() as session:
    #         async with session.get(url, headers=self.headers, params=params) as response:
    #             # response.raise_for_status()
    #             response_json = await response.json()
    #             return response_json

    async def get_docs_list(self, begin_date, end_date, **kwargs):
        url = 'https://documents-api.wildberries.ru/api/v1/documents/list'
        all_items = []
        offset = 0
        limit = kwargs.get('limit', 50)

        retry = 0
        retry_limit = 3

        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "beginTime": begin_date,
                    "endTime": end_date,
                    "offset": offset,
                    "limit": limit,
                    **kwargs
                }

                try:
                    async with session.get(url, headers=self.headers, params=params) as response:
                        if response.status == 429:
                            print("Rate limit exceeded (429). Retrying in 10 seconds...")
                            await asyncio.sleep(10)
                            continue
                        response.raise_for_status()

                        data = await response.json()
                        items = data['data']['documents']
                        all_items.extend(items)

                        if len(items) < limit:
                            break
                        offset += limit

                        # Сбрасываем счетчик повторных попыток при успешном запросе
                        retry = 0

                except aiohttp.ClientError as e:
                    if retry < retry_limit:
                        print(f"Request failed: {e}. Retrying in 10 seconds...")
                        retry += 1
                        await asyncio.sleep(10)
                        continue
                    else:
                        print(f"Failed after {retry_limit} retries: {e}")
                        break

            print(f"Всего за указанный период получено {len(all_items)} документов")
            return all_items


    async def get_upd_docs_per_client(self, doc_names):
        '''
        Принимает результат get_upd_doc_names.
        Отдаёт бинарный файл из WB API, содержащий zip-архив
        '''
        url = 'https://documents-api.wildberries.ru/api/v1/documents/download/all'
        async with ClientSession() as session:
            async with session.post(url, json=doc_names, headers=self.headers) as response:
                response_json =  await response.json()
                print(response_json)
                return response_json['data']['document']

    async def download_documents(self, doc_names):
        '''
        Принимает результат get_docs_list (метод documents/list в API)
        Отдаёт ОДИН бинарный zip-архив со ВСЕМИ запрошенными документами

        !!! За раз можно запросить только 50 документов !!!
        (в ответе бинарный файл на ВСЕ документы, мерджить опасно)
        '''

        json_data = {'params': [{"extension": i['extensions'][0], "serviceName": i['serviceName']} for i in doc_names]}

        url = 'https://documents-api.wildberries.ru/api/v1/documents/download/all'

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_data, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()

        return data['data']['document']
