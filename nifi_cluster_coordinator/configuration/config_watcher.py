import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import time
from os import path

logger = logging.getLogger(__name__)


def _on_created(event):
    logger.critical(f'{event.src_path} was created.  This should not happen.')
    raise Exception


def _on_deleted(event):
    logger.critical(f'{event.src_path} was deleted.  Something went wrong.')
    raise Exception


def _on_modified(event):
    logger.debug(event)
    logger.info(f'{event.src_path} was modified.  Processing changes.')


def _on_moved(event):
    logger.critical(f'{event.src_path} was moved to {event.dest_path}.  This is probably a problem.')
    raise Exception


def watch_configuration(config_file: str):
    directory = path.dirname(config_file)
    logger.debug(f'Directory: {directory}')
    filename = path.basename(config_file)
    logger.debug(f'File: {filename}')

    event_handler = PatternMatchingEventHandler(
        patterns=[f'*{filename}'],
        ignore_patterns=['*.example.yaml'],
        ignore_directories=True,
        case_sensitive=True
    )
    event_handler.on_created = _on_created
    event_handler.on_deleted = _on_deleted
    event_handler.on_modified = _on_modified
    event_handler.on_moved = _on_moved
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    logger.info(f'Starting to watch {config_file}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
