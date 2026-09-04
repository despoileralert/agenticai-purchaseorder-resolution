from .models import ReplacementRequest, SupplierOffer

demo_request = ReplacementRequest(
    order_item_id=50,
    part_number="SKF 6205-2RS1",
    description="25mm x 52mm x 15mm Sealed Bearing",
    unit_price=5.00,
    quantity=2,
    currency="SGD",
)

demo_supplier_list = [
    SupplierOffer(
        supplier_name="Supplier B",
        supplier_email="sales@b.com",
        part_number="SKF 6205-2Z",
        description="25x52x15 Bearing",
        unit_price=8.50,
        currency="SGD",
        available_quantity=1000,
        lead_time_days=4,
    ),
    SupplierOffer(
        supplier_name="Supplier C",
        supplier_email="sales@c.com",
        part_number="FAG 6205-2RSR",
        description="Deep Groove Ball Bearing 25x52x15",
        unit_price=7.20,
        currency="SGD",
        available_quantity=800,
        lead_time_days=2,
    ),
    SupplierOffer(
        supplier_name="Supplier C",
        supplier_email="sales@c.com",
        part_number="SKF 6205-2RS1/C3",
        description="Bearing",
        unit_price=4.50,
        currency="SGD",
        available_quantity=10000,
        lead_time_days=1,
    ),
]


def search_suppliers(request: ReplacementRequest) -> list[SupplierOffer]:
    """
    Returns a list of suppliers for the item to be replaced
    :param request:
    :return:
    """
    # Temporary mock search
    return demo_supplier_list

def send_email():
    """
    Sends an email to recommended suppliers
    :return:
    """

# Test
# print(search_suppliers(demo_request))
