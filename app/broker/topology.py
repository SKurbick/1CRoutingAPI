from dataclasses import dataclass
from enum import Enum

from faststream.rabbit import ExchangeType

from app.dependencies.config import SETTINGS





class ExchangeName(str, Enum):
    DOCGEN_REQUEST = SETTINGS.RABBIT_EXC_DOCGEN_REQUEST


class RoutingKey(str, Enum):
    DOC_BOX_LABEL = SETTINGS.RABBIT_RK_DOC_BOX_LABEL


@dataclass(frozen=True)
class ExchangeConfig:
    name: str
    type: ExchangeType = ExchangeType.DIRECT
    durable: bool = True


EXCHANGE_CONFIGS: dict[ExchangeName, ExchangeConfig] = {
    ExchangeName.DOCGEN_REQUEST: ExchangeConfig(
        name=ExchangeName.DOCGEN_REQUEST.value,
    ),
}