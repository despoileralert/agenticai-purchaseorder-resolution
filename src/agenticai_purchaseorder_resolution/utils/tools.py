from langchain.tools import tool, BaseTool
from agenticai_purchaseorder_resolution.utils.helpers import *
import boto3
import uuid
import re
import os 
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

@tool
def extract_invoice(bucket: str, key: str, task: str) -> dict:
    """
    Extracts structured data (Line Items, Part Numbers, Quantities, Unit Prices, Vendor Info, Delivery Dates) from PDF/Image invoices.
    Tools: OCR (e.g., Tesseract or AWS Textract) + Multimodal LLM / Document AI.

    Args:
        task (str): The task description containing invoice information.
    Returns:
        Standardized dict payload containing line_items, vendor_id, invoice_id, and expected_delivery_date.
    """
    textract = boto3.client(
        "textract",
        aws_access_key_id=os.getenv("LOCAL_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("LOCAL_AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("LOCAL_AWS_SESSION_TOKEN"),
        region_name="ap-southeast-1"
        )
    response = textract.analyze_document(
        Document={
            "S3Object": {
                "Bucket": bucket,
                "Name": key
            }
        },
        FeatureTypes=["TABLES", "FORMS", "QUERIES"],
        QueriesConfig={
            "Queries": [
                {"Text": "What is the vendor name?", "Alias": "VENDOR_NAME"},
                {"Text": "What is the vendor contact email to query to?", "Alias": "VENDOR_EMAIL"},
                {"Text": "What is the vendor ID?", "Alias": "VENDOR_ID"},
                {"Text": "What is the invoice ID that is a long alphanumeric string?", "Alias": "INVOICE_ID"},
                {"Text": "What is the purchase order ID that is a long alphanumeric string?", "Alias": "PO_ID"},
                {"Text": "What is the expected delivery date?", "Alias": "EXPECTED_DELIVERY"},
                {"Text": "What are/were the delivery dates of the goods?", "Alias": "DELIVERY_DATES"}
            ]
        }
    )

    blocks = response["Blocks"]

    # ---------------------------------------------------------
    # 1. Get answers from Textract Queries
    # ---------------------------------------------------------
    answers = {}

    for block in blocks:
        if block["BlockType"] == "QUERY":
            alias = block["Query"].get("Alias")

            for rel in block.get("Relationships", []):
                if rel["Type"] == "ANSWER":
                    answer_id = rel["Ids"][0]

                    answer_block = next(
                        (b for b in blocks if b["Id"] == answer_id),
                        None
                    )

                    if answer_block:
                        answers[alias] = answer_block.get("Text")
    print(answers)

    # ---------------------------------------------------------
    # 2. Extract tables
    # ---------------------------------------------------------
    block_map = {b["Id"]: b for b in blocks}
    line_items = []

    for table in [b for b in blocks if b["BlockType"] == "TABLE"]:

        rows = {}

        for rel in table.get("Relationships", []):
            if rel["Type"] != "CHILD":
                continue

            for cell_id in rel["Ids"]:
                cell = block_map[cell_id]

                if cell["BlockType"] != "CELL":
                    continue

                row = cell["RowIndex"]
                col = cell["ColumnIndex"]

                text = ""

                for cell_rel in cell.get("Relationships", []):
                    if cell_rel["Type"] == "CHILD":
                        words = [
                            block_map[x]["Text"]
                            for x in cell_rel["Ids"]
                            if block_map[x]["BlockType"] == "WORD"
                        ]
                        text = " ".join(words)

                rows.setdefault(row, {})[col] = text

        # Convert table rows to dictionaries
        table_rows = list(rows.values())

        if not table_rows:
            continue

        # Assume first row is header
        headers = [
            normalize_header(x)
            for x in table_rows[0].values()
        ]

        for row in table_rows[1:]:
            values = list(row.values())

            if len(values) < 3:
                continue

            item = dict(zip(headers, values))

            part_number = (
                item.get("part_number")
                or item.get("part")
                or item.get("item")
                or item.get("sku")
            )

            quantity = (
                item.get("quantity")
                or item.get("qty")
            )

            unit_price = (
                item.get("unit_price")
                or item.get("price")
            )

            if part_number:
                line_items.append({
                    "part_number": str(part_number),
                    "quantity": to_number(quantity),
                    "unit_price": to_number(unit_price)
                })

    # ---------------------------------------------------------
    # 3. Build final object
    # ---------------------------------------------------------
    final = {
        "line_items": line_items,

        "vendor_id": answers.get("VENDOR_ID") or str(uuid.uuid4()),

        "invoice_id": answers.get("INVOICE_ID") or str(uuid.uuid4()),

        "expected_delivery_date": parse_date(
            answers.get("EXPECTED_DELIVERY")
        ),

        "purchase_order_id": answers.get("PO_ID") or str(uuid.uuid4()),

        "delivery_dates": answers.get("DELIVERY_DATES"),

        "vendor_info": {
            "name": answers.get("VENDOR_NAME"),
            "contact": answers.get("VENDOR_EMAIL")
        }
    }

    return final
