import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, status, Body, HTTPException, Query, Path, Response
from app.models.shipment_of_goods import FBOReservePatch

from app.models import ShippedGoodsByID
from app.models.shipment_of_goods import ShipmentOfGoodsUpdate, ShipmentOfGoodsResponse, example_shipment_of_goods_data, ShipmentParamsData, \
    ReserveOfGoodsResponse, ReserveOfGoodsCreate, example_reserve_of_goods_data, ShippedGoods, example_shipped_goods_data, DeliveryType, ReservedData, \
    SummReserveData, CreationWithMovement, ShipmentWithReserveUpdating, WriteOffAccordingToFBS
from app.service.shipment_of_goods import ShipmentOfGoodsService
from app.dependencies import get_shipment_of_goods_service

router = APIRouter(prefix="/shipment_of_goods", tags=["Отгрузка со склада продавца"])

FBO_RESERVE_ERRORS = {
    404: {
        "description": "Строка резерва с указанным id не найдена.",
        "content": {"application/json": {"example": {"detail": "Резерв не найден"}}},
    },
    409: {
        "description": (
            "Операция запрещена текущим состоянием: не ФБО, shipped != 0, есть отгрузки, "
            "посторонние движения или нарушена связь со складским резервом. "
            "Для PATCH также запрещена смена товара/склада при связи с перемещением; "
            "для DELETE — наличие дочерних резервов. Причина находится в detail."
        ),
        "content": {"application/json": {"example": {
            "detail": "Операция доступна только для резерва ФБО с shipped = 0",
        }}},
    },
    422: {
        "description": (
            "Ошибка запроса. При валидации detail — массив ошибок с loc/msg/type. "
            "При ошибке ссылки на товар/склад или CHECK в БД detail — строка."
        ),
        "content": {"application/json": {"examples": {
            "validation": {"summary": "Запрещённое поле", "value": {"detail": [{
                "type": "extra_forbidden", "loc": ["body", "shipped"],
                "msg": "Extra inputs are not permitted", "input": 1,
            }]}},
            "reference": {"summary": "Несуществующий товар или склад (PATCH)",
                          "value": {"detail": "Указан несуществующий товар или склад"}},
        }}},
    },
}


@router.patch("/fbo_reserves/{reserve_id}", response_model=ShipmentOfGoodsResponse,
              summary="Изменить неотгруженную строку резерва ФБО",
              responses={**FBO_RESERVE_ERRORS, 200: {
                  "description": "Резерв обновлён. Полная строка — в data[0], её идентификатор — id.",
                  "content": {"application/json": {"example": {
                      "status": 200, "message": "Резерв ФБО обновлён", "details": None,
                      "data": [{"id": 11, "product_id": "testwild", "warehouse_id": 1,
                                "ordered": "12", "shipped": "0", "account": "Вектор",
                                "delivery_type": "ФБО", "supply_id": "WB-GI-166715280",
                                "created_at": "2026-10-26T09:00:00Z", "expires_at": None,
                                "is_fulfilled": False, "reserve_date": "2026-10-26",
                                "wb_warehouse": "Коледино", "source_reserve_id": None,
                                "is_hanging": False}],
                  }}},
              }})
async def patch_fbo_reserve(
        data: FBOReservePatch = Body(..., openapi_examples={
            "quantity": {"summary": "Изменить количество", "value": {"ordered": 12}},
            "supply": {"summary": "Изменить поставку и дату", "value": {
                "supply_id": "WB-GI-166715280", "reserve_date": "2026-10-26",
                "expires_at": "2026-11-01T12:00:00+03:00",
            }},
        }),
        reserve_id: int = Path(..., gt=0, description=(
            "ID строки резерва: reserve_id из GET /api/shipment_of_goods/get_reserved_data "
            "или product_reserves_id из создания резерва. Не supply_id."
        )),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service),
):
    """Изменяет одну существующую строку. Доступно только для **ФБО с shipped = 0**.

    - Отправляйте объект только с изменяемыми полями; остальные сохраняются.
      Пустой объект запрещён. `ordered` — новое количество, а не разница.
    - `null` очищает account, supply_id, wb_warehouse, reserve_date, expires_at.
      Для product_id, warehouse_id, ordered значение `null` запрещено.
    - Нельзя передавать shipped, delivery_type, is_hanging, is_fulfilled,
      id, created_at, source_reserve_id и неизвестные поля: HTTP 422.
    - Товар/склад нельзя менять, если есть исходный или дочерние резервы.
      Остальные разрешённые поля таких строк можно менять.
    - Связанные отгрузки и движения кроме reservation блокируют изменение.

    Пример очистки необязательных полей:
    ```json
    {"wb_warehouse": null, "expires_at": null}
    ```

    Успех: **200**, полная обновлённая строка в `data[0]`.
    Поля numeric (`ordered`, `shipped`) в ответе передаются строками.
    Складской резерв пересчитывается автоматически; уведомление 1С не отправляется.
    При ошибке изменения откатываются. Для сообщения об ошибке используйте `detail`.
    """
    return await service.patch_fbo_reserve(reserve_id, data)


@router.delete("/fbo_reserves/{reserve_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Удалить неотгруженную строку ФБО и снять резерв",
               responses={**FBO_RESERVE_ERRORS, 204: {
                   "description": "Строка удалена, резерв освобождён. Тело ответа отсутствует.",
               }})
async def delete_fbo_reserve(
        reserve_id: int = Path(..., gt=0, description=(
            "ID строки резерва: reserve_id из GET /api/shipment_of_goods/get_reserved_data "
            "или product_reserves_id из создания резерва. Не supply_id."
        )),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service),
):
    """Удаляет одну строку **ФБО с shipped = 0** и освобождает зарезервированное количество.

    - Запрос без тела. Физическое количество товара не меняется.
    - При наличии отгрузок, дочерних резервов или движений кроме reservation — 409.
    - Если строка создана перемещением, количество в исходный резерв **не возвращается**.
    - Успех: **204 без тела**; не вызывайте response.json(), уберите строку из списка.
    - При повторном удалении уже удалённого id — 404. Причина ошибки находится в `detail`.

    Удаление и пересчёт резерва выполняются в одной транзакции.
    """
    await service.delete_fbo_reserve(reserve_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/shipment_with_reserve_updating", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def shipment_with_reserve_updating(
        background_tasks: BackgroundTasks,
        data: List[ShipmentWithReserveUpdating],
        delivery_type: DeliveryType = Query(..., description="принимает ФБС или ФБО"),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.shipment_with_reserve_updating(data, delivery_type, background_tasks)
    return result



@router.post("/creation_reserve_with_movement", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def creation_reserve_with_movement(
        data: List[CreationWithMovement],
        delivery_type: DeliveryType = Query(..., description="принимает ФБС или ФБО"),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    """Создание поставки резерва с перемещением из другой поставки резерва.\n
    Для осуществления перемещения товара необходимо, чтобы исходная поставка (move_from_supply) с соответствующим product_id была создана заранее.
    \n quantity_to_move - какое количество
    \n move_from_supply - из какой поставки """
    result = await service.creation_reserve_with_movement(data, delivery_type)
    return result


@router.post("/write_off_according_to_fbs", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def write_off_according_to_fbs(
        data: List[WriteOffAccordingToFBS],
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    """
    Отгрузка товаров со склада по методу ФБС.
    """
    print(data)
    result = await service.write_off_according_to_fbs(data)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result



@router.post("/update", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED, deprecated=True)
async def create_data(
        background_tasks: BackgroundTasks,
        delivery_type: DeliveryType = Query(..., description="принимает ФБС или ФБО"),
        data: List[ShipmentOfGoodsUpdate] = Body(examples=[example_shipment_of_goods_data]),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.create_data(data, delivery_type, background_tasks)

    if result.status >= 400:
        raise HTTPException(
            status_code=result.status,
            detail={
                "message": result.message,
                "details": result.details
            }
        )

    return result


@router.get("/get_shipment_params", response_model=ShipmentParamsData, status_code=status.HTTP_200_OK)
async def shipment_params_data(
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    return await service.get_shipment_params()


@router.post("/create_reserve", response_model=List[ReserveOfGoodsResponse]|ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def create_reserve(
        data: List[ReserveOfGoodsCreate], #= Body(example=example_reserve_of_goods_data)
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.create_reserve(data)
    #
    # if result.status >= 400:
    #     raise HTTPException(
    #         status_code=result.status,
    #         detail={
    #             "message": result.message,
    #             "details": result.details
    #         }
    #     )

    return result


@router.get("/get_reserved_data", response_model=List[ReservedData], status_code=status.HTTP_200_OK)
async def get_reserved_data(
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service),
        delivery_type: DeliveryType = Query(None, description="принимает ФБС или ФБО"),
        is_fulfilled: Optional[bool] = Query(None, description="Фильтр по статусу отгрузок. False для неотгруженных"),
        begin_date: Optional[datetime.date] = Query(None, description="Начальная дата"),
):
    return await service.get_reserved_data(is_fulfilled, begin_date, delivery_type)


@router.post("/add_shipped_goods_by_id", response_model=ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def add_shipped_goods_by_id(
        data: List[ShippedGoodsByID],
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.add_shipped_goods_by_id(data)
    return result


@router.post("/add_shipped_goods", response_model=List[ReserveOfGoodsResponse]|ShipmentOfGoodsResponse, status_code=status.HTTP_201_CREATED)
async def add_shipped_goods(
        data: List[ShippedGoods] = Body(examples=[example_shipped_goods_data]),
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.add_shipped_goods(data)
    return result


@router.get("/summ_reserve_data", response_model=List[SummReserveData], status_code=status.HTTP_200_OK)
async def get_summ_reserve_data(
        service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
):
    result = await service.get_summ_reserve_data()
    return result

# @router.get("/get_shipment_data", response_model=List[ITGroupData] | InventoryTransactionsResponse, status_code=status.HTTP_200_OK,
#             responses={200: shipment_data_response_example})
# async def get_shipment_data(
#         date_from: datetime.date = None,
#         date_to: datetime.date = None,
#         service: ShipmentOfGoodsService = Depends(get_shipment_of_goods_service)
# ):
#     if date_from is None or date_to is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="date_from and date_to are required."
#         )
#
#     return await service.get_shipment_data(date_from=date_from, date_to=date_to)
