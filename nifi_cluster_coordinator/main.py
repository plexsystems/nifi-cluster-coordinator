import logging
import coloredlogs
import argparse
from configuration import config_loader, config_watcher


def main(args):
    logger = logging.getLogger(__name__)

    if args.configfile is None:
        raise ValueError('No configuration file specified')

    configuration = config_loader.load_from_file(args.configfile)

    for cluster in configuration.clusters:
        cluster.test_connectivity()

    for cluster in list(filter(lambda c: c.is_reachable, configuration.clusters)):
        logger.info(f'Setting registry clients for: {cluster.name}')
        cluster.set_registry_entries(configuration.registries)

    # TODO: Figure out state management, commenting out for now
    # configuration.save_to_file(args.statefile)

    if args.watch:
        config_watcher.watch_configuration(args.configfile)
        # TODO: Implement actual reprocessing of configuration on file change


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
    # parser.add_argument(
    #     '--statefile',
    #     help='Set the file name for storing state information.  (.pkl format)',
    #     required=False)
    parser.add_argument(
        '--watch',
        help='Leave application running and watch the configuration file for updates.',
        action='store_true')
    args = parser.parse_args()

    coloredlogs.install(
        level=args.loglevel,
        milliseconds=True,
        fmt='%(asctime)s %(hostname)s %(name)s %(levelname)s: %(funcName)s[%(lineno)s] %(message)s')
    logger = logging.getLogger(__name__)

    logger.debug('Starting program')
    try:
        main(args)
    except Exception as error:
        logger.critical(error)
        logger.critical('Unexpected error, shutting down.')
        exit(1)

    logger.debug('Stopping program')
    exit(0)
