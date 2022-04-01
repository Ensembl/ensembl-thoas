"""Custom Thoas logger"""

import logging

from pymongo import monitoring


class ThoasLogging:

    def __init__(self, logging_file, logger_name='generic_logging'):

        self.logger_name = logger_name
        self.logging_file = logging_file
        self.logging_handler = logging.FileHandler(self.logging_file)

        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.logging_handler)

        # Set generic format
        formatter = logging.Formatter('*****\n%(levelname)s \n%(message)s \n*****')

        self.logging_handler.setFormatter(formatter)
        self.logging_handler.setLevel(logging.INFO)

    def url_logger(self, **kwargs):

        logger = logging.getLogger(self.logger_name)

        message = ""
        for key, value in kwargs.items():
            message += f"{key}:{value}\n"

        # Override logging format specific to URLs logging
        formatter = logging.Formatter('*****\n%(levelname)s - URL problems \n%(message)s*****')
        self.logging_handler.setFormatter(formatter)
        logger.warning(message)

    def some_other_logger(self, message):

        logger = logging.getLogger(self.logger_name)

        # Override Logging format specific to some_other_logger
        formatter = logging.Formatter('*****\n XYZ debug details \n %(message)s \n*****')
        self.logging_handler.setFormatter(formatter)
        logger.warning(message)


class CommandLogger(monitoring.CommandListener):
    """Logger for MongoDB transactions"""

    def __init__(self, log):
        self.log = log

    def started(self, event):
        self.log.debug(
            "Command %s with request id %s started on server %s",
            event.command_name, event.request_id, event.connection_id)

    def succeeded(self, event):
        self.log.debug("Command %s with request id %s on server %s succeeded in %s microseconds",
                  event.command_name, event.request_id, event.connection_id, event.duration_micros)

    def failed(self, event):
        self.log.debug("Command %s with request id %s on server %s failed in %s microseconds",
                  event.request_id, event.request_id, event.connection_id, event.duration_micros)
