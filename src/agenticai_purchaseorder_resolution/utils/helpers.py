import logging, logging.config
import yaml

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
    