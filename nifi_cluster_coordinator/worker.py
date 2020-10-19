import logging
from configuration import config_loader
import services.registry_service as registry_service
import services.project_service as project_service
import services.parameter_context_service as parameter_context_service


def process(configfile):
    logger = logging.getLogger(__name__)

    configuration = config_loader.load_from_file(configfile)

    for cluster in configuration.clusters:
        cluster.test_connectivity()

    for cluster in list(filter(lambda c: c.is_reachable, configuration.clusters)):
        logger.info(f'Setting registry clients for cluster: {cluster.name}')
        registry_service.sync(cluster, configuration.registries)

        logger.info(f'Setting parameter contexts for cluster: {cluster.name}')
        parameter_context_service.sync(cluster, configuration.parameter_contexts)

        logger.info(f'Setting projects for cluster: {cluster.name}')
        project_service.sync(cluster, configuration.projects, configuration.parameter_contexts)
