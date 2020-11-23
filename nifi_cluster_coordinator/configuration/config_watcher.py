import logging
import time
import worker
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from os import path
from configuration import config_loader

logger = logging.getLogger(__name__)


def _on_created(event):
    logger.critical(f'{event.src_path} was created.  This should not happen.')
    raise Exception


def _on_deleted(event):
    logger.critical(f'{event.src_path} was deleted.  Something went wrong.')
    raise Exception


def _on_modifiedfile(event):
    logger.debug(event)
    logger.info(f'{event.src_path} was modified.  Processing changes.')
    configuration = config_loader.load_from_file(event.src_path)
    worker.process(configuration)


def _on_modifiedfolder(event):
    logger.debug(event)
    logger.info(f'{event.src_path} was modified.  Processing changes.')
    directory = path.dirname(event.src_path)
    configuration = config_loader.load_from_folder(directory)
    worker.process(configuration)


def _on_moved(event):
    logger.critical(f'{event.src_path} was moved to {event.dest_path}.  This is probably a problem.')
    raise Exception


def watch_configurationfile(config_file: str):
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
    event_handler.on_modified = _on_modifiedfile
    event_handler.on_moved = _on_moved
    logger.info(f'Starting to watch {config_file}')
    _start_observer(event_handler, directory)


def watch_configurationfolder(config_folder: str):
    directory = path.normpath(config_folder)
    logger.debug(f'Directory: {directory}')

    event_handler = PatternMatchingEventHandler(
        patterns=['*.yaml', '*.yml'],
        ignore_patterns=['*.example.yaml'],
        ignore_directories=True,
        case_sensitive=True
    )
    event_handler.on_created = _on_created
    event_handler.on_deleted = _on_deleted
    event_handler.on_modified = _on_modifiedfolder
    event_handler.on_moved = _on_moved
    logger.info(f'Starting to watch {config_folder}')
    _start_observer(event_handler, directory)


def _start_observer(event_handler, directory):
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()