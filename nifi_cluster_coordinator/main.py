import logging
import coloredlogs
import argparse
import worker
from configuration import config_watcher
from configuration import config_loader


def main(args):
    if args.configfile is None and args.configfolder is None:
        raise ValueError('No configuration file(s) specified')
    if args.configfile is not None and args.configfolder is not None:
        raise ValueError('Please specify either a single config file or a folder.')

    if args.configfile is not None:
        try:
            configuration = config_loader.load_from_file(args.configfile)
        except Exception as exception:
            logger.critical(f'Error loading configuration: {exception}')
            raise

    if args.configfolder is not None:
        try:
            configuration = config_loader.load_from_folder(args.configfolder)
        except Exception as exception:
            logger.crigial(f'Error loading configuration: {exception}')
            raise

    worker.process(configuration)

    if args.watch and args.configfile is not None:
        config_watcher.watch_configurationfile(args.configfile)

    if args.watch and args.configfolder is not None:
        config_watcher.watch_configurationfolder(args.configfolder)


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
    parser.add_argument(
        '--watch',
        help='Leave application running and watch the configuration file for updates.',
        action='store_true')
    parser.add_argument(
        '--configfolder',
        help='Set the folder to watch for config files.',
        required=False)
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
