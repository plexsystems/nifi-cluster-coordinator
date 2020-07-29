import logging
import coloredlogs
import argparse
import requests
from configuration import config_loader


def main(args):
    logger = logging.getLogger(__name__)

    if args.configfile is None:
        raise ValueError("No configuration file specified")

    # Load State
    # If no state present, create a new empty state
    # Load cluster definitions
    # Verify connectivity to clusters
    # parse incomming state request file
    # add any new projects
    # update any projects
    # watch for new incomming state changes

    configuration = config_loader.load_from_file(args.configfile)

    for cluster in configuration.clusters:
        logger.info(f"Attempting to connect to {cluster.name}")
        if cluster.security.use_certificate:
            response = requests.get(
                cluster.host_name + '/process-groups/root',
                cert=(cluster.security.certificate_config.ssl_cert_file, cluster.security.certificate_config.ssl_key_file),
                verify=cluster.security.certificate_config.ssl_ca_cert)
        else:
            response = requests.get(cluster.host_name + '/process-groups/root')

        logger.debug(response.json())
        root_pg = response.json()
        logger.info(f'Found process group id: {root_pg["id"]}')


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
        required=False)
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
