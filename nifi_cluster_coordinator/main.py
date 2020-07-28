import logging
import coloredlogs
import argparse
import nipyapi
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

    configuration = config_loader.load(args.configfile)
    logging.info(f"Configuration {configuration}")

    for cluster in configuration['clusters']:
        logger.info(f"Attempting to connect to {cluster['name']}")
        nipyapi.config.nifi_config.host = cluster['host_name']
        nipyapi.config.nifi_config.cert_file = cluster['ssl_cert_file']
        nipyapi.config.nifi_config.ssl_ca_cert = cluster['ssl_ca_cert']
        nipyapi.config.nifi_config.key_file = cluster['ssl_key_file']
        # nipyapi.config.nifi_config.verify_ssl = False
        # nipyapi.config.nifi_config.debug = True

        root_id = nipyapi.canvas.get_root_pg_id()
        logger.info(f"Found root process group with id {root_id}")


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
