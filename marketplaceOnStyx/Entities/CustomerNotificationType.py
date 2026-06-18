from enum import Enum

class CustomerNotificationType(Enum):
    PAYMENT_SUCCESS = 0
    PAYMENT_FAILED = 1
    CHECKOUT_FAILED=2
    
