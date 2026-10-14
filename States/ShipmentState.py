from Entities.Packages import Package, PackageStatus
from Entities.Shipment import Shipment
from dataclasses import dataclass, field
from itertools import chain, islice


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
                pkg if isinstance(pkg, Package) else Package(**pkg) for pkg in pkgs
            ]
            for shipment_id, pkgs in self.packages.items()
        }

    def get_oldest_open_shipment_per_seller(self) -> dict[int, int]:
        """Map seller_id -> the lowest shipment_id with a shipped package."""
        oldest: dict[int, int] = {}

        for p in chain.from_iterable(self.packages.values()):
            if p.package_status == PackageStatus.SHIPPED:
                current = oldest.get(p.seller_id)
                if current is None or p.shipment_id < current:
                    oldest[p.seller_id] = p.shipment_id

        # Limit the result to the first 10 sellers
        return dict(islice(oldest.items(), 10))

    def get_shipped_packages_by_shipment_id_and_seller_id(
        self, seller_id: int, shipment_id: int
    ) -> list[Package]:
        return [
            p
            for p in self.packages[shipment_id]
            if p.seller_id == seller_id and p.package_status == PackageStatus.SHIPPED
        ]

    def get_total_delivered_packages_for_shipment(self, shipment_id: int) -> int:
        return sum(
            1
            for p in self.packages[shipment_id]
            if p.package_status == PackageStatus.DELIVERED
        )
