from typing import Self
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    INVOICED = 0
    SHIPPED = 1
    DELIVERED = 2
    PAYMENT_FAILED = 3
    PAYMENT_PROCESSED = 4
    READY_FOR_SHIPMENT = 5
    IN_TRANSIT = 6


@dataclass
class Order:
    id: int
    customerId: int
    orderStatus: OrderStatus
    invoiceNumber: str
    purchaseTimestamp: datetime
    updatedAt: datetime
    paymentDate: datetime | None
    deliveredCarrierDate: datetime | None
    deliveredCustomerDate: datetime | None
    countItems: int
    totalAmount: float
    totalFreight: float
    totalIncentive: float
    totalInvoice: float
    totalItems: float
    data: str
    createdAt: datetime

    def __init__(
        self,
        id: int,
        customerId: int,
        orderStatus: OrderStatus,
        invoiceNumber: str,
        purchaseTimestamp: datetime,
        paymentDate: datetime | None,
        deliveredCarrierDate: datetime | None,
        deliveredCustomerDate: datetime | None,
        countItems: int,
        totalAmount: float,
        totalFreight: float,
        totalIncentive: float,
        totalInvoice: float,
        totalItems: float,
        data: str,
    ):

        self.id = id
        self.customerId = customerId
        self.orderStatus = orderStatus
        self.invoiceNumber = invoiceNumber
        self.purchaseTimestamp = purchaseTimestamp
        self.paymentDate = paymentDate
        self.deliveredCarrierDate = deliveredCarrierDate
        self.deliveredCustomerDate = deliveredCustomerDate
        self.countItems = countItems
        self.totalAmount = totalAmount
        self.totalFreight = totalFreight
        self.totalIncentive = totalIncentive
        self.totalInvoice = totalInvoice
        self.totalItems = totalItems
        self.data = data
        self.createdAt = datetime.now()
        self.updatedAt = self.createdAt
