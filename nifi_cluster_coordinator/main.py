import logging
import coloredlogs
import argparse
import requests
import json
from configuration import config_loader


revision_0 = {
    "version": 0
}


def main(args):
    logger = logging.getLogger(__name__)

    if args.configfile is None:
        raise ValueError("No configuration file specified")

    # Load State
    # If no state present, create a new empty state
    # Load cluster definitions
        # Verify connectivity to clusters
        # Verify registry entries are created
    # parse incomming state request file
    # add any new projects
    # update any projects
    # watch for new incomming state changes

    configuration = config_loader.load_from_file(args.configfile)

    for cluster in configuration.clusters:
        logger.info(f"Attempting to connect to {cluster.name}")
        try:
            if cluster.security.use_certificate:
                response = requests.get(
                    cluster.host_name + '/process-groups/root',
                    cert=(cluster.security.certificate_config.ssl_cert_file, cluster.security.certificate_config.ssl_key_file),
                    verify=cluster.security.certificate_config.ssl_ca_cert)
                cluster.is_reachable = True
            else:
                response = requests.get(cluster.host_name + '/process-groups/root')
                cluster.is_reachable = True
        except requests.exceptions.RequestException as exception:
            logger.info(f"Unable to reach {cluster.name}, will try again later.")
            logger.warning(exception)
            cluster.is_reachable = False

        if cluster.is_reachable:
            logger.debug(response.json())
            root_pg = response.json()
            logger.info(f'Found process group id: {root_pg["id"]}')

    for cluster in list(filter(lambda c: c.is_reachable, configuration.clusters)):
        logger.info("Setting registry clients.")
        logger.debug(f"Setting registry clients for: {cluster.name}")

        for registry in configuration.registries:
            # TODO: Need to check for registry existing before trying to create it
            data = {
                "revision": revision_0,
                "component": vars(registry)  # HACK: vars(foo) creates a dictonary of values, need to find a better way to do this
            }
            logger.debug(json.dumps(data))

            try:
                if cluster.security.use_certificate:
                    response = requests.post(
                        cluster.host_name + '/controller/registry-clients',
                        cert=(cluster.security.certificate_config.ssl_cert_file, cluster.security.certificate_config.ssl_key_file),
                        verify=cluster.security.certificate_config.ssl_ca_cert,
                        json=data)
                    cluster.is_reachable = True
                else:
                    response = requests.post(cluster.host_name + '/controller/registry-clients', json=json.dumps(data))
                    cluster.is_reachable = True
            except requests.exceptions.RequestException as exception:
                logger.info(f"Unable to reach {cluster.name}, will try again later.")
                logger.warning(exception)
                cluster.is_reachable = False

            logger.debug(response.text)
            registry.id = response.json()['id']
            logger.info(f"Registry {registry.name} created with id {registry.id}")



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
        logger.warning("Unexpected error, shutting down.")
        exit(1)

    logger.debug("Stopping program")
    exit(0)