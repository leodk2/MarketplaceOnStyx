from Entities.Packages import Package
from Entities.Shipment import Shipment
from dataclasses import dataclass, field


@dataclass
class ShipmentState:
    shipment: dict[int, Shipment] = field(default_factory=dict)
    packages: dict[int, list[Package]] = field(default_factory=dict)
