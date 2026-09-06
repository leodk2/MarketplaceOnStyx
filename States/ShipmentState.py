from Entities.Packages import Package
from Entities.Shipment import Shipment
from dataclasses import dataclass


@dataclass
class ShipmentState:
    shipment: dict[int, Shipment] = {}
    packages: dict[int, list[Package]] = {}
