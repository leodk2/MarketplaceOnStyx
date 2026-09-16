from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass
class TransactionMark:
    tid: str
    type: TransactionType
    actorId: int
    status: MarkStatus
    source: str


class TransactionType(Enum):
    CUSTOMER_SESSION = 0
    QUERY_DASHBOARD = 1
    PRICE_UPDATE = 2
    UPDATE_PRODUCT = 3
    UPDATE_DELIVERY = 4
    NONE = 5


class MarkStatus(Enum):
    SUCCESS = 0
    ERROR = 1
    ABORT = 2
    NOT_ACCEPTED = 3
