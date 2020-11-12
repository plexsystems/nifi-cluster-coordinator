import logging
from configuration import config_loader
import services.registry_service as registry_service
import services.project_service as project_service
import services.parameter_context_service as parameter_context_service
import services.user_service as user_service
import services.user_group_service as user_group_service
import services.access_policy_service as access_policy_service


def process(configfile):
    logger = logging.getLogger(__name__)

    configuration = config_loader.load_from_file(configfile)

    if configuration.security.is_coordinated:
        access_policy_service.init_access_policies_descriptors()

    for cluster in configuration.clusters:
        cluster.test_connectivity()

    for cluster in list(filter(lambda c: c.is_reachable, configuration.clusters)):
        logger.info(f'Setting registry clients for cluster: {cluster.name}')
        registry_service.sync(cluster, configuration.registries)

        if configuration.security.is_coordinated:
            logger.info(f'Setting users for cluster: {cluster.name}')
            user_service.sync(cluster, configuration.security.users)

            logger.info(f'Setting user groups for cluster: {cluster.name}')
            user_group_service.sync(cluster, configuration.security.user_groups, configuration.security.users)

            logger.info(f'Setting global access policies for cluster: {cluster.name}')
            access_policy_service.sync_global_policies(cluster, configuration.security)

        logger.info(f'Setting parameter contexts for cluster: {cluster.name}')
        parameter_context_service.sync(cluster, configuration.parameter_contexts)

        logger.info(f'Setting projects for cluster: {cluster.name}')
        project_service.sync(cluster, configuration.projects, configuration.parameter_contexts)

        if configuration.security.is_coordinated:
            logger.info(f'Setting component access policies for cluster: {cluster.name}')
            access_policy_service.sync_component_policies(cluster, configuration.security, configuration.projects)
