from langchain.tools import tool
import uuid #mimic order id generation
import datetime

@tool
def extract_invoice(task: str) -> dict:
    """
    Extracts structured data (Line Items, Part Numbers, Quantities, Unit Prices, Vendor Info, Delivery Dates) from PDF/Image invoices.
    Tools: OCR (e.g., Tesseract or AWS Textract) + Multimodal LLM / Document AI.

    Args:
        task (str): The task description containing invoice information.
    Returns:
        Standardized dict payload containing line_items, vendor_id, invoice_id, and expected_delivery_date.
    """
    # Placeholder implementation for invoice extraction logic
    # In a real scenario, this would involve parsing the task description,
    # extracting relevant invoice details, and returning them in a structured format.
    # For demonstration purposes, we will return a mock response.
    expected_sample_output = {
        "line_items": [
            {
                "part_number": "12345",
                "quantity": 10,
                "unit_price": 15.99
            },
            {
                "part_number": "67890",
                "quantity": 5,
                "unit_price": 9.99
            }
        ],
        "vendor_id": "random_vendor_id",
        "invoice_id": str(uuid.uuid4()),
        "expected_delivery_date": None,
        "purchase_order_id": str(uuid.uuid4()),  # Mimic order ID generation
        "delivery_dates": [datetime.date(2026, 11, 13), datetime.date(2026, 12, 31)],  # Placeholder for delivery dates
        "vendor_info": {
            "name": "Random Vendor Name",
            "contact": "random.vendor@example.com"
        }
    }

    return expected_sample_output