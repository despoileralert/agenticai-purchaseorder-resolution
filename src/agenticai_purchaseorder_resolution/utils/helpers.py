from datetime import datetime
import logging, logging.config
import yaml
import re

def basicLogger(name: str) -> logging.Logger:
    """
    Create a basic logger with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: A configured logger instance.
    """
    loggingconfig = read_yaml("config/helper_config.yaml")
    logging.config.dictConfig(loggingconfig)
    return logging.getLogger(name)


def read_yaml(file_path: str) -> dict:
    """
    Read a YAML Configuration file and return its contents as a dictionary.

    Args:
        file_path (str): The path to the YAML file.
    """
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

"""
Helper functions for the invoice extraction agent.
"""
def normalize_header(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")

    mappings = {
        "part_no": "part_number",
        "part_number": "part_number",
        "part": "part_number",
        "sku": "part_number",

        "qty": "quantity",
        "quantity": "quantity",

        "unit_price": "unit_price",
        "unit_cost": "unit_price",
        "price": "unit_price"
    }

    return mappings.get(value, value)


def to_number(value):
    if not value:
        return None

    value = str(value).replace(",", "").replace("$", "").strip()

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return None


def parse_date(value):
    if not value:
        return None

    value = value.strip()

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass

    return None