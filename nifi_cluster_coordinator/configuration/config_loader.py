import yaml
import logging
import os
import glob
import hiyapyco
from .cluster import Cluster
from .registry import Registry
from .project import Project
from .parameter_context import ParameterContext
from .security import Security


class Configuration:

    def __init__(self, clusters: dict, registries: dict, projects: dict, parameter_contexts: dict, security: dict):
        self.clusters = [Cluster(name=c['name'], host_name=c['host_name'], security=c['security']) for c in clusters]
        self.registries = [Registry(name=r['name'], uri=r['host_name'], description=r['description']) for r in registries]
        self.projects = [
            Project(
                name=p['name'],
                description=p['description'],
                registry_name=p['registry_name'],
                bucket_id=p['bucket_id'] if 'bucket_id' in p else '',
                flow_id=p['flow_id'] if 'flow_id' in p else '',
                clusters=p['clusters'] if 'clusters' in p else [])
            for p in projects
        ] if not (projects is None) else []

        self.parameter_contexts = [
            ParameterContext(
                name=pc['name'],
                description=pc['description'],
                is_coordinated=pc['is_coordinated'],
                parameters=pc['parameters'] if 'parameters' in pc else [])
            for pc in parameter_contexts
        ] if not (parameter_contexts is None) else []

        self.security = Security(security) if not (security is None) else Security({'is_coordinated': False})


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
    """Build a configuration object."""
    try:
        config = Configuration(
            config_definition['clusters'],
            config_definition['registries'],
            config_definition['projects'] if 'projects' in config_definition else None,
            config_definition['parameter_contexts'] if 'parameter_contexts' in config_definition else None,
            config_definition['security'] if 'security' in config_definition else None)
        return config
    except Exception as e:
        logging.critical(f'Error parsing configuration file: {e}')


def load_from_folder(config_folder_location: str) -> Configuration:
    """Return a configuration based on a folder location.

    :param config_folder_location:
        String of folder path to be read.
    :returns:
        Configuration object.
    """
    logger = logging.getLogger(__name__)
    logger.info(f'Attempting to load config from folder {config_folder_location}')

    if os.path.isdir(config_folder_location) is False:
        logger.critical(f'{config_folder_location} is not a directory')
        raise ValueError('Invalid configuration folder specified.')

    os.chdir(config_folder_location)
    files = glob.glob('*.yaml')
    files.extend(glob.glob('*.yml'))
    files = set(files) - set(glob.glob('*example*'))
    for file in files:
        logger.info(f'Found file {file}')

    # Forcing INFO level logging here, debug will print file contents which might leak secrets
    conf = hiyapyco.load(list(files), method=hiyapyco.METHOD_MERGE, mergelists=False, loglevel='INFO')
    configuration = _build_configuration(yaml.safe_load(hiyapyco.dump(conf)))
    return configuration