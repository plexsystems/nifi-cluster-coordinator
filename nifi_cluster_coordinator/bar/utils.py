import logging


def is_false(foo: bool) -> bool:
    """This is always false."""
    logger = logging.getLogger(__name__)
    logger.info("This is false")
    return False
