import logging
import coloredlogs
import argparse
import requests
from configuration import config_loader
import copy
import config_file_watcher

revision_0 = {
    "version": 0
}


def get_connection_details(cluster, endpoint: str):
    connection_details = {
        "url": cluster.host_name + endpoint,
        "cert": (cluster.security.certificate_config.ssl_cert_file, cluster.security.certificate_config.ssl_key_file) if cluster.security.use_certificate else None,
        "verify": cluster.security.certificate_config.ssl_ca_cert if cluster.security.use_certificate else None
    }
    return connection_details


def _test_cluster_connectivity(configuration):
    """Determin if each configured cluster is reachable."""
    logger = logging.getLogger(__name__)
    for cluster in configuration.clusters:
        logger.info(f"Attempting to connect to {cluster.name}")
        try:
            response = requests.get(**get_connection_details(cluster, '/process-groups/root'))
            cluster.is_reachable = True
        except requests.exceptions.RequestException as exception:
            logger.info(f"Unable to reach {cluster.name}, will try again later.")
            logger.warning(exception)
            cluster.is_reachable = False

        if cluster.is_reachable:
            logger.debug(response.json())
            root_pg = response.json()
            logger.info(f'Found process group id: {root_pg["id"]}')


def main(args):
    logger = logging.getLogger(__name__)

    if args.configfile is None:
        raise ValueError("No configuration file specified")

    # add any new projects
    # update any projects
    # watch for new incomming state changes

    configuration = config_loader.load_from_file(args.configfile)
    _test_cluster_connectivity(configuration)

    # For each cluster in our configuration
    # Get the list of currently configured registry clients
    # For each registry in the confgiuration file
    # See if that registry is currently configured
    # Verify if the URI is the same
    # If the URI does not match update the URI
    # If the registry is not found on the configuration list, add it
    # TODO: Garbage collect any configured registries which are not part of the master configuration
    for cluster in list(filter(lambda c: c.is_reachable, configuration.clusters)):
        logger.info(f"Setting registry clients for: {cluster.name}")

        cluster_registries = requests.get(**get_connection_details(cluster, '/controller/registry-clients')).json()

        for registry in configuration.registries:
            for configured_registry in cluster_registries['registries']:
                if registry.name == configured_registry['component']['name']:
                    if registry.uri != configured_registry['component']['uri']:
                        logger.warning(f"Registry URI missmatch for {registry.name} and {cluster.name}, updating")
                        configured_registry['component']['uri'] = registry.uri
                        try:
                            response = requests.put(
                                **get_connection_details(cluster, f'/controller/registry-clients/{configured_registry["id"]}'),
                                json=configured_registry
                            )
                            logger.debug(response.text)
                        except requests.exceptions.RequestException as exception:
                            logger.info(f"Unable to reach {cluster.name}, will try again later.")
                            logger.warning(exception)
                            cluster.is_reachable = False

                    # registry.id = configured_registry['component']['id']
                    r = copy.copy(registry)
                    r.id = configured_registry['component']['id']
                    cluster.registries.append(r)
                    logger.debug(f'Found configured {r.name} configured for {cluster.name}')

        for registry in configuration.registries:
            if next((x for x in cluster.registries if x.name == registry.name), None) is None:
                logger.info(f'Adding {registry.name} to {cluster.name}')
                data = {
                    "revision": revision_0,
                    "component": vars(registry)  # HACK: vars(foo) creates a dictonary of values, need to find a better way to do this
                }

                try:
                    response = requests.post(
                        **get_connection_details(cluster, '/controller/registry-clients'),
                        json=data)
                    logger.debug(response.text)
                except requests.exceptions.RequestException as exception:
                    logger.info(f"Unable to reach {cluster.name}, will try again later.")
                    logger.warning(exception)
                    cluster.is_reachable = False

                if response.status_code == 201:
                    r = copy.copy(registry)
                    r.id = response.json()['id']
                    cluster.registries.append(r)
                    logger.info(f"Cluster {cluster.name} added registry {r.name} with id {r.id}")
                else:
                    # NiFi clusters which are not configured with keystore/truststores cannot be configured
                    # to talk to https nifi registries.  This will catch
                    logger.warning(response.text)

    configuration.save_to_file(args.statefile)
    config_file_watcher.watch_configuration(args.configfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--loglevel',
        help='Set the log level (DEBUG, INFORMATION, WARNING, CRITICAL), default is INFORMATION.',
        default='INFORMATION',
        required=False)
    parser.add_argument(
        '--configfile',
        help='Set the config file location.',
        required=True)
    parser.add_argument(
        '--statefile',
        help='Set the file name for storing state information.  (.pkl format)',
        required=True
    )
    args = parser.parse_args()

    coloredlogs.install(
        level=args.loglevel,
        milliseconds=True,
        fmt="%(asctime)s %(hostname)s %(name)s %(levelname)s: %(funcName)s[%(lineno)s] %(message)s")
    logger = logging.getLogger(__name__)

    logger.debug("Starting program")
    try:
        main(args)
    except Exception as error:
        logger.critical(error)
        logger.critical("Unexpected error, shutting down.")
        exit(1)

    logger.debug("Stopping program")
    exit(0)
