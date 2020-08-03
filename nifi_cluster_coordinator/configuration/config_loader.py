import yaml
import logging
import pickle


class CertificateConfig:

    def __init__(self, certificate_config: dict):
        self.ssl_cert_file = certificate_config['ssl_cert_file']
        self.ssl_ca_cert = certificate_config['ssl_ca_cert']
        self.ssl_key_file = certificate_config['ssl_key_file']


class Security:

    def __init__(self, security: dict):
        self.use_certificate = security['use_certificate']

        if self.use_certificate:
            self.certificate_config = CertificateConfig(security['certificate_config'])


class Registry:

    def __init__(self, name, uri, description):
        self.name = name
        self.uri = uri
        self.description = description


class Cluster:
    def __init__(self, name: str, host_name: str, security: dict):
        self.name = name
        self.host_name = host_name
        self.security = Security(security)
        self.registries = []


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
    logger.info(f"Attempting to load config file from {config_file_location}")
    stream = open(config_file_location, 'r')
    configuration = _build_configuration(yaml.safe_load(stream))
    logger.info(f"Loaded configuration for {configuration.clusters.__len__()} clusters.")
    return configuration


def _build_configuration(config_definition) -> Configuration:
    try:
        config = Configuration(
            config_definition['clusters'],
            config_definition['registries'],
            config_definition['projects'])
        return config
    except Exception as e:
        logging.critical(f"Error parsing configuration file: {e}")
