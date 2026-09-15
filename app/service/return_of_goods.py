import logging
import datetime
from typing import List
from fastapi import BackgroundTasks


from app.database.repositories import ReturnOfGoodsRepository
from app.dependencies.config import settings
from app.infrastructure.ONE_C import ONECRouting
from app.models.return_of_goods import (
    IncomingReturns,
    ManualUnidentifiedReturn,
    ReturnOfGoodsData,
    ReturnOfGoodsResponse,
    UnidentifiedGoodsReturn,
)

logger = logging.getLogger(__name__)


class ReturnOfGoodsService:
    def __init__(
            self,
            return_of_goods_repository: ReturnOfGoodsRepository,
    ):
        self.return_of_goods_repository = return_of_goods_repository

    async def get_return_of_goods(
            self,
            date_from: datetime.date | None = None,
    ) -> List[ReturnOfGoodsData] | ReturnOfGoodsResponse:
        result = await self.return_of_goods_repository.get_return_of_goods(date_from=date_from)
        return result

    async def get_unidentified_goods(
            self,
            date_from: datetime.date | None = None,
    ) -> List[UnidentifiedGoodsReturn] | ReturnOfGoodsResponse:
        return await self.return_of_goods_repository.get_unidentified_goods(date_from=date_from)

    async def receive_unidentified(
            self,
            data: ManualUnidentifiedReturn,
            background_tasks: BackgroundTasks,
    ) -> ReturnOfGoodsResponse:
        result = await self.return_of_goods_repository.receive_unidentified(data)
        if result.status != 201:
            return result

        log_context = {
            "item_count": len(data.srids),
            "product_ids": [data.product_id],
            "warehouse_ids": [data.warehouse_id],
            "identification_method": "manual",
        }
        try:
            one_c_database_data = (
                await self.return_of_goods_repository.get_manual_incoming_data_for_one_c(data)
            )
        except Exception as exc:
            logger.exception(
                "event=manual_returns_notification_data_error exception_type=%s exception_message=%s",
                type(exc).__name__,
                str(exc),
                extra=log_context,
            )
            return result

        background_tasks.add_task(
            self.notify_one_c_about_returns,
            one_c_database_data,
            log_context,
        )
        return result

    async def incoming_returns(
            self,
            data: List[IncomingReturns],
            background_tasks: BackgroundTasks,
    ) -> ReturnOfGoodsResponse:
        result = await self.return_of_goods_repository.incoming_returns(data)

        if result.status == 201:
            one_c_database_data = (
                await self.return_of_goods_repository.get_incoming_data_for_one_c(data)
            )
            log_context = {
                "item_count": len(data),
                "product_ids": [item.product_id for item in data],
                "warehouse_ids": sorted({item.warehouse_id for item in data}),
            }
            background_tasks.add_task(
                self.notify_one_c_about_returns,
                one_c_database_data,
                log_context,
            )

        return result

    async def notify_one_c_about_returns(
            self,
            one_c_database_data: list,
            log_context: dict,
    ) -> None:
        try:
            one_c_connect = ONECRouting(
                base_url=settings.ONE_C_BASE_URL,
                password=settings.ONE_C_PASSWORD,
                login=settings.ONE_C_LOGIN,
            )
            response = await one_c_connect.goods_returns(data=one_c_database_data)

            if not 200 <= response.status < 300:
                logger.error(
                    "event=one_c_returns_notification_http_error http_status=%s response_body=%s",
                    response.status,
                    response.body[:4096],
                    extra=log_context,
                )
                return

            logger.info(
                "event=one_c_returns_notification_succeeded http_status=%s",
                response.status,
                extra=log_context,
            )
        except Exception as exc:
            logger.exception(
                "event=one_c_returns_notification_transport_error exception_type=%s exception_message=%s",
                type(exc).__name__,
                str(exc),
                extra=log_context,
            )
