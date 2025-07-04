import logging
from logging.handlers import RotatingFileHandler
import sys
import os

def get_logger():
    if not hasattr(get_logger, "_logger"):
        logger = logging.getLogger('home-media-torrent-util')
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] -- %(message)s')

        if os.name != 'nt':  # Check if the OS is not Windows
            log_file_path = '/var/log/home-media-torrent-util/info.log'
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)  # Create directories if they don't exist
            # Rotating file handler (5MB max size, keep 3 backups)
            fh = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(formatter)

        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)

        get_logger._logger = logger
    return get_logger._logger