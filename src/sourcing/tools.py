from .models import ReplacementRequest, SupplierOffer


demo_supplier_list = [
    SupplierOffer(
        supplier_name="Horizon Components Pte Ltd.",
        supplier_email="sales@horizon.com",
        part_number="30112A",
        available_quantity=1000,
        unit_price=420.69,
        lead_time_days=4,
    ),
    SupplierOffer(
        supplier_name="Solar Systems Inc.",
        supplier_email="sales@solar.com",
        part_number="30121",
        available_quantity=800,
        unit_price=467.67,
        lead_time_days=2,
    ),
    SupplierOffer(
        supplier_name="LunarTech Corporation",
        supplier_email="sales@lunartech.com",
        part_number="30112",
        available_quantity=10000,
        unit_price=488.32,
        lead_time_days=1,
    )
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
