import yaml
import logging
import pickle
from .cluster import Cluster
from .registry import Registry


class Configuration:

    def __init__(self, clusters: dict, registries: dict, projects: dict):
        self.clusters = [Cluster(name=c['name'], host_name=c['host_name'], security=c['security']) for c in clusters]
        self.registries = [Registry(name=r['name'], uri=r['host_name'], description=r['description']) for r in registries]
        self.projects = projects

    def save_to_file(self, save_file_location: str):
        with open(save_file_location, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)


def load_from_file(config_file_location: str) -> Configuration:
    """Return a configuration based on a file location.

    :param config_file_location:
        String of file location to be read.
    :returns:
        Configuration object.
    """
    logger = logging.getLogger(__name__)
    logger.info(f'Attempting to load config file from {config_file_location}')
    stream = open(config_file_location, 'r')
    configuration = _build_configuration(yaml.safe_load(stream))
    logger.info(f'Loaded configuration for {configuration.clusters.__len__()} clusters.')
    return configuration


def _build_configuration(config_definition) -> Configuration:
    try:
        config = Configuration(
            config_definition['clusters'],
            config_definition['registries'],
            config_definition['projects'])
        return config
    except Exception as e:
        logging.critical(f'Error parsing configuration file: {e}')
