from dataclasses import dataclass


@dataclass
class Seller:
    id: int
    name: str
    company_name: str
    email: str
    phone: str
    mobile_phone: str
    cpf: str
    cnpj: str
    address: str
    complement: str
    city: str
    state: str
    zip_code: str
