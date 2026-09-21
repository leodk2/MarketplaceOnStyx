from dataclasses import dataclass


@dataclass
class Customer:
    id: int
    first_name: str
    last_name: str
    address: str
    complement: str
    birth_date: str
    zip_code: str
    city: str
    state: str
    card_number: str
    card_security_number: str
    card_expiration: str
    card_holder_name: str
    card_type: str
    success_payment_count: int
    failed_payment_count: int
    delivery_count: int
    data: str
