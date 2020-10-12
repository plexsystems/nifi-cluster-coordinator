import logging
import requests
from configuration.cluster import Cluster
from configuration.registry import Registry

revision_0 = {
    'version': 0
}


def sync(cluster: Cluster, configured_registries: list):
    """Set the cluster nifi-registry entries to their desired configuration."""
    logger = logging.getLogger(__name__)

    logger.info(f'Collecting currently configure registries for cluster: {cluster.name}')
    cluster_registries_json = requests.get(**cluster._get_connection_details('/controller/registry-clients')).json()

    # Build dictionaries for the desired registry configuration & the current registry configuration.
    # The dictionaries are indexed by name to support efficient lookups & comparisons.
    desired_registries_dict = {registry.name: registry for registry in configured_registries}
    current_registries_json_dict = {registry['component']['name']: registry for registry in cluster_registries_json['registries']}

    # loop through registries & set appropriate values.
    for name, desired_registry, current_registry_json in _registry_munger(desired_registries_dict, current_registries_json_dict):
        if current_registry_json is None:
            _create(cluster, desired_registry)
        elif desired_registry is None:
            # TODO: Delete the registry.
            logger.warn(f'Deleting {current_registry_json}')
            _delete(cluster, current_registry_json)
        else:
            _update(cluster, desired_registry, current_registry_json)

    cluster_registries_json = requests.get(**cluster._get_connection_details('/controller/registry-clients')).json()
    cluster.registeries_json_dict = {registry['component']['name']: registry for registry in cluster_registries_json['registries']}


def _create(cluster: Cluster, registry: Registry):
    """Create the missing registry in the cluster."""
    logger = logging.getLogger(__name__)
    logger.info(f'Adding {registry.name} to cluster: {cluster.name}')
    data = {
        'revision': revision_0,
        'component': vars(registry)  # HACK: vars(foo) creates a dictonary of values, need to find a better way to do this
    }

    try:
        response = requests.post(**cluster._get_connection_details('/controller/registry-clients'), json=data)
        logger.debug(response.text)
        if response.status_code != 201:
            # NiFi clusters which are not configured with keystore/truststores cannot be configured
            # to talk to https nifi registries.  This will catch
            logger.warning(response.text)
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to reach {cluster.name}, will try again later.')
        logger.warning(exception)


def _update(cluster: Cluster, registry: Registry, current_registry_json):
    """Update the existing registry in the cluster if it has a different URI."""
    logger = logging.getLogger(__name__)
    if (
        registry.uri.lower() != current_registry_json['component']['uri'].lower()
        or registry.description.lower() != current_registry_json['component']['description'].lower()
    ):
        logger.warning(f'Registry details mismatch for {registry.name} and {cluster.name}, updating.')
        current_registry_json['component']['uri'] = registry.uri
        try:
            response = requests.put(
                **cluster._get_connection_details(f'/controller/registry-clients/{current_registry_json["id"]}'),
                json=current_registry_json)
            logger.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logger.warning(f'Unable to reach {cluster.name}, will try again later.')
            logger.warning(exception)


def _delete(cluster: Cluster, registry: Registry):
    logger = logging.getLogger(__name__)
    logger.info(f'Deleting registry with id {registry["id"]}')
    try:
        response = requests.delete(
            **cluster._get_connection_details(f'/controller/registry-clients/{registry["id"]}'),
            params={'version': registry['revision']['version']})
        logger.debug(response.text)
    except requests.exceptions.RequestException as exception:
        logger.warning(f'Unable to reach {cluster.name}, will try again later.')
        logger.warning(exception)


def _registry_munger(desired_registries_dict, current_registries_json_dict):
    """Generator for iterating through the union of the desired & current registry configurations.
    Yields a tuple containing the registry name, desired configuration, & current configuration."""

    for key in desired_registries_dict.keys() | current_registries_json_dict.keys():
        yield (key, desired_registries_dict.get(key, None), current_registries_json_dict.get(key, None))
