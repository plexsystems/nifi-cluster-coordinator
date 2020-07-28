import logging
import coloredlogs
import argparse


def main(args):
    logger = logging.getLogger(__name__)
    logger.info("Hello world")

    # Load State
    # If no state present, create a new empty state
    # Load cluster definitions
    # Verify connectivity to clusters
    # parse incomming state request file
    # add any new projects
    # update any projects
    # watch for new incomming state changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--loglevel',
        help='Set the log level, default is WARNING.',
        default='WARNING',
        nargs='?')
    args = parser.parse_args()

    coloredlogs.install(
        level=args.loglevel,
        milliseconds=True,
        fmt="%(asctime)s %(hostname)s %(name)s %(levelname)s: %(funcName)s[%(lineno)s] %(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting program")
    main(args)
    logger.info("Stopping program")
    exit(0)
