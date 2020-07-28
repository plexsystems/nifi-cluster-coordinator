import logging
import coloredlogs
import argparse


def main(args):
    logger = logging.getLogger(__name__)

    # Load State
    # If no state present, create a new empty state

    # Load Cluster definitions
    # some other stuff
    # some blah blah
    # some blah blah
    # some balh balh
    # some blah blah
    # some blah balah
    # trim trailing
    # some
    # some
    # some


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
