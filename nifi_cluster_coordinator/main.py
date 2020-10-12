import logging
import coloredlogs
import argparse
import worker
from configuration import config_watcher


def main(args):
    if args.configfile is None:
        raise ValueError('No configuration file specified')

    worker.process(args.configfile)

    if args.watch:
        config_watcher.watch_configuration(args.configfile)


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
