# Карта API

Все пути имеют prefix `/api`. Router-файл одноимённый группе в `app/api/v1/endpoints/`; handler и response приведены ниже. Авторизация: **нет на всех активных routes**. Стандартный flow: handler -> одноимённый service -> repository; monitoring не использует repository. Ошибки обычно: Pydantic 422, explicit 400/404/409 в CRUD/stickers, DB errors часто возвращаются телом с `status=422` при HTTP 200/201.

| Method/path | Handler | Request -> response | Data/side effect |
|---|---|---|---|
| GET `/inventory_transactions/group_data` | `group_data` | date query -> `List[ITGroupData]` | read movements |
| GET `/inventory_transactions/get_add_stock_by_client` | same | dates -> grouped response | read inventory_transactions |
| GET `/inventory_transactions/get_kit_operations` | same | dates -> grouped response | read kit_operations |
| GET `/inventory_transactions/get_incoming_returns` | same | dates -> grouped response | read returns |
| GET `/inventory_transactions/get_re_sorting_operations` | same | dates -> grouped response | read resorting |
| GET/POST `/containers/` | `get_containers/create_container` | filters/`ContainerCreate` -> Container(s) | read/insert containers |
| GET/PUT/DELETE `/containers/{container_id}` | matching CRUD | id + update -> Container/204 | read/update/delete containers |
| GET `/returns/get_return_of_goods` | `get_return_of_goods` | none -> grouped returns | reads return + article/status |
| POST `/returns/incoming_returns` | handler also named `get_return_of_goods` | `List[IncomingReturns]` -> response | DB transaction, then 1С |
| POST `/cash_flow_writeoff/update` | `receive_writeoff_data` | list writeoffs -> response | versions cash_flow_writeoffs |
| GET `/goods_information/get_metawilds_data` | same | none -> kits | reads products |
| GET `/goods_information/get_all_products_data` | same | none -> products | reads products |
| POST `/goods_information/add_product` | same | `List[AllProductsData]` -> response | inserts products |
| POST `/return_to_supplier/update` | same | `List[ReturnToSupplierUpdate]` -> response | versions two tables |
| POST `/ordered_goods_from_buyers/update` | `create_data` | list updates -> response | versions buyer orders |
| GET `/ordered_goods_from_buyers/get_buyers_orders` | same | dates/acceptance -> aggregate | reads orders/barcodes |
| POST `/ordered_goods_from_buyers/update_acceptance_status` | same | list status -> response | updates acceptance |
| GET/PUT `/products_dimensions/{product_id}` | matching | id/update -> `ProductDimensions` | products_data + containers |
| GET `/products_dimensions/` | `get_all_product_dimensions` | filters -> list | read dimensions |
| POST `/inventory_check/add_inventory_result` | `create_data` | `InventoryCheckUpdate` -> response | inserts inventory_checks |
| GET `/inventory_check/get_inventory_data` | same | dates -> grouped response | read inventory |
| GET `/docs/get_docs` | `get_docs` | account/dates -> `List[Dict]` | WB HTTP + PDF parse |
| GET `/stickers/{transport|individual}/template/{product_id}` | template handlers | path/query -> response class implicit | reads products/localisation/user data |
| POST `/stickers/{transport|individual}/generate` | create/get task handlers | generation model -> task | DB + Rabbit publish |
| GET `/stickers/templates`, `/manufacturers`, `/importers` | list handlers | none -> implicit lists | reads dictionaries |
| GET `/stickers/tasks` | `get_generation_tasks` | filters -> implicit list | task reads |
| GET `/stickers/tasks/{task_id}/download` | `get_file_url_for_download` | id -> redirect/URL | signed S3 URL |
| GET `/stickers/tasks/events` | `stream_tasks_notifications` | none -> SSE | Redis subscription |
| POST `/shipment_of_goods/shipment_with_reserve_updating` | same | list + delivery_type -> response | DB; FBO -> 1С |
| POST `/shipment_of_goods/creation_reserve_with_movement` | same | list + delivery_type -> response | reserve + movement |
| POST `/shipment_of_goods/write_off_according_to_fbs` | same | list -> response | FBS write-off |
| POST `/shipment_of_goods/update` | `create_data` (deprecated) | shipment list/type -> response | DB; FBO -> 1С |
| GET `/shipment_of_goods/get_shipment_params` | `shipment_params_data` | none -> params | reads seller accounts |
| POST `/shipment_of_goods/create_reserve` | same | reserve list -> response | inserts reserves |
| GET `/shipment_of_goods/get_reserved_data` | same | filters -> list | reads reserves |
| POST `/shipment_of_goods/add_shipped_goods_by_id` | same | list -> response | fulfills by ids |
| POST `/shipment_of_goods/add_shipped_goods` | same | list -> response | fulfills reserves |
| GET `/shipment_of_goods/summ_reserve_data` | same | none -> list | reserve aggregation |
| POST `/receipt_of_goods/update` | `create_data` | receipt list -> response | DB -> WMS |
| POST `/receipt_of_goods/add_incoming_receipt` | same | incoming list -> response | DB -> 1С |
| GET `/warehouse_and_balances/get_statuses_for_products_in_reserve` | same | none -> stats | shared order tables |
| POST `/warehouse_and_balances/add_defective_goods` | same | list -> response | paired transactions |
| GET `/warehouse_and_balances/get_warehouses` | same | none -> warehouses | read |
| GET `/warehouse_and_balances/get_all_product_current_balances` | same | none -> balances | read view/table |
| POST `/warehouse_and_balances/assembly_or_disassembly_metawild` | same | operation -> response | DB wait -> 1С |
| POST `/warehouse_and_balances/re_sorting_operations` | same | operation -> response | DB wait -> 1С |
| POST `/warehouse_and_balances/add_stock_by_client` | same | list -> response | inventory insert |
| POST `/warehouse_and_balances/get_historical_stocks` | same | `HistoricalStockBody` -> list | calls DB function |
| POST `/warehouse_and_balances/product_quantity_check` | same | warehouse + list -> result | read/check balances |
| POST `/local_barcode_generation/update` | `create_data` | `GoodsAcceptanceCertificateCreate` -> implicit | acceptance + boxes + barcode |
| POST `/financial_transactions/income_on_bank_account` | same | list -> response | versions income rows |
| POST `/financial_transactions/write_off_of_non_cash_funds` | same | list -> response | versions writeoff rows |
| POST `/financial_transactions/cash_disbursement_order` | same | list -> response | versions cash orders |
| GET `/health`, `/metrics`, `/dashboard` | monitoring handlers | none -> implicit | process-local metrics/dashboard |

Точные Pydantic arguments находятся в соответствующем endpoint-файле; точные SQL — в одноимённом repository. Sticker routes намеренно не имеют `response_model`.
