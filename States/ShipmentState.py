from Entities.Packages import Package, PackageStatus
from Entities.Shipment import Shipment
from dataclasses import dataclass, field
from itertools import chain, islice


@dataclass
class ShipmentState:
    # # shipments per customer
    # shipment: dict[int, Shipment] = field(default_factory=dict)
    # # packages per customer
    # packages: dict[int, list[Package]] = field(default_factory=dict)

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

    def get_ten_oldest_unconcluded_shipments(self) -> dict[int, int]:
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
        return list(
            filter(
                lambda p: (
                    p.seller_id == seller_id
                    and p.package_status == PackageStatus.SHIPPED
                ),
                self.packages,
            )
        )

    def get_total_delivered_packages_for_shipment(self, shipment_id: int) -> int:
        return len(
            list(
                filter(
                    lambda p: p.package_status == PackageStatus.DELIVERED, self.packages
                )
            )
        )
