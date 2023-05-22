"""Custom Thoas logger"""

import logging

from pymongo import monitoring


class ThoasLogging:
    def __init__(self, logging_file, logger_name="generic_logging"):

        self.logger_name = logger_name
        self.logging_file = logging_file
        self.logging_handler = logging.FileHandler(self.logging_file)

        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.logging_handler)

        # Set generic format
        formatter = logging.Formatter("*****\n%(levelname)s \n%(message)s \n*****")

        self.logging_handler.setFormatter(formatter)
        self.logging_handler.setLevel(logging.DEBUG)

    def url_logger(self, **kwargs):

        logger = logging.getLogger(self.logger_name)

        message = ""
        for key, value in kwargs.items():
            message += f"{key}:{value}\n"

        # Override logging format specific to URLs logging
        formatter = logging.Formatter(
            "*****\n%(levelname)s - URL problems \n%(message)s*****"
        )
        self.logging_handler.setFormatter(formatter)
        logger.warning(message)

    def some_other_logger(self, message):

        logger = logging.getLogger(self.logger_name)

        # Override Logging format specific to some_other_logger
        formatter = logging.Formatter(
            "*****\n XYZ debug details \n %(message)s \n*****"
        )
        self.logging_handler.setFormatter(formatter)
        logger.warning(message)

    def log_client_info(self, log_scope):
        """
        Logs everything we would like to capture during the query execution
            * HTTP code and message (TODO)
            * Client IP address
            * Referer and user-agent
            * Method (POST, GET..)
        log_scope: is and 'info.context['request'].scope' where all the info
        mentioned above (and more!) are stored
        """
        # Override Logging format specific to some_other_logger
        formatter = logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
        )
        self.logging_handler.setFormatter(formatter)

        method = log_scope.get("method")
        # turn {"client": ("127.0.0.1", 58017)} to "127.0.0.1:58017"
        client_ip_address = ":".join(map(str, log_scope["client"]))
        user_agent = log_scope["headers"][1][1].decode().split("/")[0]
        # referer may not exist, I'll keep it commented for now
        # referer = log_scope["headers"][5][1].decode()

        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        logger.debug(
            f"Client_IP: {client_ip_address} "
            f"- Method: {method} "
            f"- User_Agent: {user_agent} "
            # f"- Referer: {referer}"
        )


class CommandLogger(monitoring.CommandListener):
    """Logger for MongoDB transactions"""

    def __init__(self, log):
        self.log = log

    def started(self, event):
        self.log.debug(
            "[Request id: %s] Command %s started on server %s",
            event.request_id,
            event.command_name,
            event.connection_id,
        )
        if event.command_name == "find":
            self.log.debug(
                "[Request id: %s] Running query %s",
                event.request_id,
                event.command["filter"],
            )

    def succeeded(self, event):
        self.log.debug(
            "[Request id: %s] Command %s on server %s succeeded in %s milliseconds",
            event.request_id,
            event.command_name,
            event.connection_id,
            round(event.duration_micros / 1000000, 5),
        )

    def failed(self, event):
        self.log.debug(
            "[Request id: %s] Command %s on server %s failed in %s milliseconds",
            event.request_id,
            event.command_name,
            event.connection_id,
            round(event.duration_micros / 1000000, 5),
        )
