from dataclasses import dataclass
from enum import Enum

from faststream.rabbit import ExchangeType

from app.dependencies.config import SETTINGS


class ExchangeName(str, Enum):
    DOCGEN_REQUEST = SETTINGS.RABBIT_EXC_DOCGEN_REQUEST
    DOCGEN_EVENT = SETTINGS.RABBIT_EXC_DOCGEN_EVENT


class RoutingKey(str, Enum):
    DOC_BOX_LABEL = SETTINGS.RABBIT_RK_DOC_BOX_LABEL
    DOC_GENERATED_BOX_LABEL = SETTINGS.RABBIT_RK_DOC_GENERATED_BOX_LABEL
    DOC_UNIT_LABEL = SETTINGS.RABBIT_RK_DOC_UNIT_LABEL
    DOC_GENERATED_UNIT_LABEL = SETTINGS.RABBIT_RK_DOC_GENERATED_UNIT_LABEL


class QueueName(str, Enum):
    RABBIT_Q_DOCGEN_BOX_LABEL_RESPONSE = SETTINGS.RABBIT_Q_DOCGEN_BOX_LABEL_RESPONSE
    RABBIT_Q_DOCGEN_UNIT_LABEL_RESPONSE = SETTINGS.RABBIT_Q_DOCGEN_UNIT_LABEL_RESPONSE


@dataclass(frozen=True)
class ExchangeConfig:
    name: str
    type: ExchangeType = ExchangeType.DIRECT
    durable: bool = True


@dataclass(frozen=True)
class QueueConfig:
    name: str
    routing_key: str
    durable: bool = True


EXCHANGE_CONFIGS: dict[ExchangeName, ExchangeConfig] = {
    ExchangeName.DOCGEN_REQUEST: ExchangeConfig(
        name=ExchangeName.DOCGEN_REQUEST.value,
    ),
    ExchangeName.DOCGEN_EVENT: ExchangeConfig(
        name=ExchangeName.DOCGEN_EVENT.value,
    ),
}


QUEUE_CONFIGS: dict[QueueName, QueueConfig] = {
    # QueueName.DOCGEN_BOX_LABEL: QueueConfig(
    #     name=QueueName.DOCGEN_BOX_LABEL.value, routing_key=RoutingKey.DOC_BOX_LABEL.value
    # ),
    # QueueName.DOCGEN_UNIT_LABEL: QueueConfig(
    #     name=QueueName.DOCGEN_UNIT_LABEL.value, routing_key=RoutingKey.DOC_UNIT_LABEL.value
    # ),
    QueueName.RABBIT_Q_DOCGEN_BOX_LABEL_RESPONSE: QueueConfig(
        name=QueueName.RABBIT_Q_DOCGEN_BOX_LABEL_RESPONSE.value, routing_key=RoutingKey.DOC_GENERATED_BOX_LABEL.value
    ),
    QueueName.RABBIT_Q_DOCGEN_UNIT_LABEL_RESPONSE: QueueConfig(
        name=QueueName.RABBIT_Q_DOCGEN_UNIT_LABEL_RESPONSE.value, routing_key=RoutingKey.DOC_GENERATED_UNIT_LABEL.value
    )
}