import logging
import requests
from .security import ClusterSecurity

revision_0 = {
    'version': 0
}

base_api_path = '/nifi-api'

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
        self.security = ClusterSecurity(security)
        self.is_reachable = False
        self.registeries_json_dict = None

    def _get_connection_details(self, endpoint: str):
        """Return the connection details for the cluster API calls."""
        connection_details = {
            'url': self.host_name + base_api_path + endpoint,
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
