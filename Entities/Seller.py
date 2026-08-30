from pydantic import BaseModel


class Seller(BaseModel):
    Id: int
    Name: str = ""
    CompanyName: str = ""
    Email: str = ""
    Phone: str = ""
    MobilePhone: str = ""
    Cpf: str = ""
    Cnpj: str = ""
    Address: str = ""
    Complement: str = ""
    City: str = ""
    State: str = ""
    ZipCode: str = ""
