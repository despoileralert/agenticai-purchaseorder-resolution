from database import db


def save_parsed_invoice(parsed_invoice: dict) -> None:
    vendor_id = parsed_invoice["vendor_id"]
    invoice_id = parsed_invoice["invoice_id"]
    purchase_order_id = parsed_invoice["purchase_order_id"]

    vendor_info = parsed_invoice["vendor_info"]
    line_items = parsed_invoice["line_items"]
    delivery_dates = parsed_invoice.get("delivery_dates", [])

    # Vendor
    vendor = {
        "vendor_id": vendor_id,
        "name": vendor_info["name"],
        "contact": vendor_info["contact"]
    }
    if get_vendor(vendor_id) is None:
        db["vendors"].append(vendor)

    # Invoice
    invoice = {
        "invoice_id": invoice_id,
        "vendor_id": vendor_id,
        "purchase_order_id": purchase_order_id
    }

    db["invoices"].append(invoice)

    # Purchase order
    purchase_order = {
        "purchase_order_id": purchase_order_id,
        "invoice_id": invoice_id,
        "vendor_id": vendor_id,
        "expected_delivery_date": parsed_invoice.get("expected_delivery_date"),
        "status": "PENDING"
    }

    db["purchase_orders"].append(purchase_order)

    delivery_dates = parsed_invoice.get("delivery_dates", [])

    for index, line_item in enumerate(parsed_invoice["line_items"]):
        # Match delivery date to corresponding item
        delivery_date = delivery_dates[index] if index < len(delivery_dates) else None

        order_item = {
            "order_item_id": f"{purchase_order_id}-{index + 1}",
            "purchase_order_id": purchase_order_id,
            "vendor_id": vendor_id,
            "part_number": line_item["part_number"],
            "quantity": line_item["quantity"],
            "unit_price": line_item["unit_price"],
            "delivery_date": delivery_date,
            "status": "PENDING"
        }

        db["order_items"].append(order_item)

# Read vendors
def get_all_vendors() -> list[dict]:
    return db["vendors"]

def get_vendor(vendor_id: str) -> dict | None:
    for vendor in db["vendors"]:
        if vendor["vendor_id"] == vendor_id:
            return vendor
    return None

# Read invoices
def get_all_invoices() -> list[dict]:
    return db["invoices"]

def get_invoice(invoice_id: str) -> dict | None:
    for invoice in db["invoices"]:
        if invoice["invoice_id"] == invoice_id:
            return invoice
    return None

# Purchase orders
def get_all_purchase_orders() -> list[dict]:
    return db["purchase_orders"]

def get_purchase_order(purchase_order_id: str,) -> dict | None:
    for order in db["purchase_orders"]:
        if order["purchase_order_id"] == purchase_order_id:
            return order
    return None

# Read order items
def get_all_order_items() -> list[dict]:
    return db["order_items"]

def get_order_items(purchase_order_id: str) -> list[dict]:
    return [item for item in db["order_items"] if item["purchase_order_id"] == purchase_order_id]

def get_order_item(order_item_id: str) -> dict | None:
    for item in db["order_items"]:
        if item["order_item_id"] == order_item_id:
            return item
    return None

def update_order_item_status(order_item_id: str, status: str) -> bool:
    item = get_order_item(order_item_id)
    if item is None:
        return False
    item["status"] = status
    return True

# Clear
def clear_database() -> None:
    for collection in db.values():
        collection.clear()
