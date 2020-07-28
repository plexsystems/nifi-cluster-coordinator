import yaml
import logging


def load(config_file_location):
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to load config file from {config_file_location}")
    stream = open(config_file_location, 'r')
    return yaml.safe_load(stream)
