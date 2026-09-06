from dataclasses import dataclass


@dataclass
class Customer:
    Id: int
    FirstName: str
    Lastname: str
    Address: str
    Complement: str
    BirthDate: str
    ZipCode: str
    City: str
    State: str
    CardNumber: str
    CardSecurityNumber: str
    CardExpiration: str
    CardHolderName: str
    CardType: str
    SuccessPaymentCount: int
    FailedPaymentCount: int
    DeliveryCount: int
    Data: str
