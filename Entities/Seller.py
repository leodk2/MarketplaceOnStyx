from dataclasses import dataclass


@dataclass
class Seller:
    Id: int
    Name: str
    CompanyName: str
    Email: str
    Phone: str
    MobilePhone: str
    Cpf: str
    Cnpj: str
    Address: str
    Complement: str
    City: str
    State: str
    ZipCode: str
