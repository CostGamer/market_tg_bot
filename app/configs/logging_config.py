import logging
import sys

from pythonjsonlogger import jsonlogger

from .settings import LoggingSettings


def init_logger(log_settings: LoggingSettings) -> None:
    log_level = log_settings.log_level.upper()
    log_file = log_settings.log_file
    log_encoding = log_settings.log_encoding

    log_format = (
        "%(levelname)s %(asctime)s %(name)s %(funcName)s %(lineno)d "
        "%(process)d %(thread)d %(message)s"
    )
    formatter = jsonlogger.JsonFormatter(log_format)

    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(log_file, encoding=log_encoding)

    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        root_logger.addHandler(stream_handler)
        root_logger.addHandler(file_handler)
