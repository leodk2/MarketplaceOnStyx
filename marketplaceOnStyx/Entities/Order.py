from datetime import datetime
from pydantic import BaseModel


class Order(BaseModel):
    id: int
    customerId: int
    orderStatus: int
    invoiceNumber: str
    purchaseTimestamp: datetime
    createdAt: datetime
    updatedAt: datetime
    paymentDate: datetime
    deliveredCarrierDate: datetime
    deliveredCustomerDate: datetime
    countItems: int
    totalAmount: float
    totalFreight: float
    totalIncentive: float
    totalInvoice: float
    totalItems: float
    data: str
