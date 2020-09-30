import logging
import requests
from .security import Security

revision_0 = {
    'version': 0
}

# For each cluster in our configuration
# Get the list of currently configured registry clients
# For each registry in the confgiuration file
# See if that registry is currently configured
# Verify if the URI is the same
# If the URI does not match update the URI
# If the registry is not found on the configuration list, add it
# TODO: Garbage collect any configured registries which are not part of the master configuration


class Cluster:
    def __init__(self, name: str, host_name: str, security: dict):
        self.name = name
        self.host_name = host_name
        self.security = Security(security)
        self.is_reachable = False

    def _get_connection_details(self, endpoint: str):
        """Return the connection details for the cluster API calls."""
        connection_details = {
            'url': self.host_name + endpoint,
            'cert': (self.security.certificate_config.ssl_cert_file, self.security.certificate_config.ssl_key_file) if self.security.use_certificate else None,
            'verify': self.security.certificate_config.ssl_ca_cert if self.security.use_certificate else None
        }
        return connection_details

    def test_connectivity(self):
        """Determine if cluster is reachable."""
        logger = logging.getLogger(__name__)
        logger.info(f'Connectivity test: {self.name}.')
        try:
            response = requests.get(**self._get_connection_details('/process-groups/root'))
            logger.debug(response.text)
            if response.status_code == 200:
                self.is_reachable = True
                self.root_process_group_id = response.json()['id']
                logger.info(f'found process group id: {self.root_process_group_id}')
            else:
                logger.warn(f'Connection issues with {self.name}: {response.text}')

        except requests.exceptions.RequestException as exception:
            logger.warning(exception)
            logger.info(f'Unable to reach {self.name}, will try again later.')
            self.is_reachable = False

    def _registry_munger(self, registries_desired_configurations, registries_current_configurations):
        """Generator for iterating through the union of the desired & current registry configurations.
        Yields a tuple containing the registry name, desired configuration, & current configuration."""

        for key in registries_desired_configurations.keys() | registries_current_configurations.keys():
            yield (key, registries_desired_configurations.get(key, None), registries_current_configurations.get(key, None))

    def _update_registry(self, desired_registry_configuration, current_registry_configuration):
        """Update the existing registry in the cluster if it has a different URI."""
        logger = logging.getLogger(__name__)
        if (
            desired_registry_configuration.uri != current_registry_configuration['component']['uri']
            or desired_registry_configuration.description != current_registry_configuration['component']['description']
        ):
            logger.warning(f'Registry details mismatch for {desired_registry_configuration.name} and {self.name}, updating.')
            current_registry_configuration['component']['uri'] = desired_registry_configuration.uri
            try:
                response = requests.put(
                    **self._get_connection_details(f'/controller/registry-clients/{current_registry_configuration["id"]}'),
                    json=current_registry_configuration)
                logger.debug(response.text)
            except requests.exceptions.RequestException as exception:
                logger.info(f'Unable to reach {self.name}, will try again later.')
                logger.warning(exception)
                self.is_reachable = False

    def _create_registry(self, desired_registry_configuration, current_registry_configuration):
        """Create the missing registry in the cluster."""
        logger = logging.getLogger(__name__)
        logger.info(f'Adding {desired_registry_configuration.name} to {self.name}')
        data = {
            'revision': revision_0,
            'component': vars(desired_registry_configuration)  # HACK: vars(foo) creates a dictonary of values, need to find a better way to do this
        }

        try:
            response = requests.post(
                **self._get_connection_details('/controller/registry-clients'),
                json=data)
            logger.debug(response.text)
            if response.status_code != 201:
                # NiFi clusters which are not configured with keystore/truststores cannot be configured
                # to talk to https nifi registries.  This will catch
                logger.warning(response.text)
        except requests.exceptions.RequestException as exception:
            logger.info(f'Unable to reach {self.name}, will try again later.')
            logger.warning(exception)
            self.is_reachable = False

    def _delete_registry(self, registry):
        logger = logging.getLogger(__name__)
        logger.info(f'Deleting registry with id {registry["id"]}')
        try:
            response = requests.delete(
                **self._get_connection_details(f'/controller/registry-clients/{registry["id"]}'),
                params={'version': registry['revision']['version']})
            logger.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logger.infi(f'Unable to reach {self.name}, will try again later.')
            logger.warning(exception)

    def set_registry_entries(self, configured_registries):
        """Set the cluster nifi-registry entries to their desired configuration."""
        logger = logging.getLogger(__name__)

        logger.info(f'Collecting currently configure registries for: {self.name}')
        cluster_registries = requests.get(**self._get_connection_details('/controller/registry-clients')).json()

        # Build dictionaries for the desired registry configuration & the current registry configuration.
        # The dictionaries are indexed by name to support efficient lookups & comparisons.
        registries_desired_configuration = {registry.name: registry for registry in configured_registries}
        registries_current_configuration = {registry['component']['name']: registry for registry in cluster_registries['registries']}

        # loop through registries & set appropriate values.
        for name, desired_registry_configuration, configured_registry in self._registry_munger(registries_desired_configuration, registries_current_configuration):
            if configured_registry is None:
                self._create_registry(desired_registry_configuration, configured_registry)
            elif desired_registry_configuration is None:
                # TODO: Delete the registry.
                logger.warn(f'Deleting {configured_registry}')
                self._delete_registry(configured_registry)
            else:
                self._update_registry(desired_registry_configuration, configured_registry)
