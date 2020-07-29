import yaml
import logging
from typing import List


class CertificateConfig:

    def __init__(self, certificate_config: dict):
        self.ssl_cert_file = certificate_config['ssl_cert_file']
        self.ssl_ca_cert = certificate_config['ssl_ca_cert']
        self.ssl_key_file = certificate_config['ssl_key_file']


class Security:
    use_certificate: bool
    certificate_config: CertificateConfig

    def __init__(self, security: dict):
        self.use_certificate = security['use_certificate']

        if self.use_certificate:
            self.certificate_config = CertificateConfig(security['certificate_config'])


class Cluster:
    name: str
    host_name: str
    security: Security

    def __init__(self, name: str, host_name: str, security: dict):
        self.name = name
        self.host_name = host_name
        self.security = Security(security)


class Configuration:
    clusters: List[Cluster] = []

    def __init__(self, clusters: dict):
        for c in clusters:
            cluster = Cluster(name=c['name'], host_name=c['host_name'], security=c['security'])
            self.clusters.append(cluster)


def load_from_file(config_file_location: str) -> Configuration:
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to load config file from {config_file_location}")
    stream = open(config_file_location, 'r')
    configuration = _build_configuration(yaml.safe_load(stream))
    logger.info(f"Loaded configuration for {configuration.clusters.__len__()} clusters.")
    return configuration


def _build_configuration(config_definition) -> Configuration:
    config = Configuration(config_definition['clusters'])
    return config
