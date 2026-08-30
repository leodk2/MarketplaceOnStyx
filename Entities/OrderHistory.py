from datetime import datetime
from pydantic import BaseModel
class OrderHistory(BaseModel):
    orderId:int
    status:int
    createdAt:datetime
    
