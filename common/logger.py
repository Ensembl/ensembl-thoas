import logging
import sys


class ThoasLogging:

    def __init__(self, logging_file, logger_name='generic_logging'):

        self.logger_name = logger_name
        self.logging_file = logging_file
        self.logging_handler = logging.FileHandler(self.logging_file)

        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.logging_handler)

        # Set generic format
        format = logging.Formatter('*****\n%(levelname)s \n%(message)s \n*****')

        self.logging_handler.setFormatter(format)
        self.logging_handler.setLevel(logging.INFO)

    def url_logger(self, **kwargs):

        logger = logging.getLogger(self.logger_name)

        message = ""
        for key, value in kwargs.items():
            message += "{}:{}\n".format(key, value)

        # Override logging format specific to URLs logging
        format = logging.Formatter('*****\n%(levelname)s - URL problems \n%(message)s*****')
        self.logging_handler.setFormatter(format)
        logger.warning(message)

    def some_other_logger(self, message):

        logger = logging.getLogger(self.logger_name)

        # Override Logging format specific to some_other_logger
        format = logging.Formatter('*****\n XYZ debug details \n %(message)s \n*****')
        self.logging_handler.setFormatter(format)
        logger.warning(message)
