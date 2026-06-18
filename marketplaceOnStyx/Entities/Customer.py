from pydantic import BaseModel


class Customer(BaseModel):
    Id: int
    FirstName: str = ""
    Lastname: str = ""
    Address: str = ""
    Complement: str = ""
    BirthDate: str = ""
    ZipCode: str = ""
    City: str = ""
    State: str = ""
    CardNumber: str = ""
    CardSecurityNumber: str = ""
    CardExpiration: str = ""
    CardHolderName: str = ""
    CardType: str = ""
    SuccessPaymentCount: int = 0
    FailedPaymentCount: int = 0
    DeliveryCount: int = 0
    Data: str = ""
