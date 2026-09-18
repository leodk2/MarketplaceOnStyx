from Entities.Packages import Package
from Entities.Shipment import Shipment
from dataclasses import dataclass, field


@dataclass
class ShipmentState:
    shipment: dict[int, Shipment] = field(default_factory=dict)
    packages: dict[int, list[Package]] = field(default_factory=dict)

    def __post_init__(self):
        self.shipment = {
            shipment_id: (s if isinstance(s, Shipment) else Shipment(**s))
            for shipment_id, s in self.shipment.items()
        }
        self.packages = {
            shipment_id: [
                pkg if isinstance(pkg, Package) else Package(**pkg)
                for pkg in pkgs
            ]
            for shipment_id, pkgs in self.packages.items()
        }
