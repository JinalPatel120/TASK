# import django
import datetime
from enum import Enum
import logging

import json_log_formatter
import ujson
from typing import List


logging.addLevelName(logging.CRITICAL, "FATAL")


class CustomizedJSONFormatter(json_log_formatter.JSONFormatter):
    json_lib = ujson

    def json_record(self, message, extra, record):
        extra["level"] = record.__dict__["levelname"]
        extra["msg"] = message
        extra["logger"] = record.__dict__["name"]
        extra["func"] = record.__dict__["funcName"]
        extra["time"] = datetime.datetime.now().isoformat()

        request = extra.pop("request", None)
        if request:
            extra["x_forward_for"] = request.META.get("X-FORWARD-FOR")
        return extra


# Create a custom log formatter that includes a counter
class CounterLogFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.counter = 0

    def format(self, record):
        self.counter += 1
        timestamp = datetime.datetime.fromtimestamp(record.created).isoformat()
        msg = f"Log #{self.counter} - {record.levelname} - {timestamp} - {record.getMessage()}\n"
        return msg
    



class Module(Enum):
    USER = "user"
    PRODUCT = "product"
    ORDER = "order"  # Example additional module



class LoggingService:
    def __init__(self, modules: Enum,log_levels:List[str]):
        """
        Initializes the LoggingService with the given module enum.
        :param module_enum: The enum class representing the modules for which logging should be created.
        """
        self.log_levels =log_levels
        self.module_enum = modules
        self.handlers = {}
        self.loggers = {}
        self.create_log_directories()
        self.logging_config = self.generate_logging_config()

    def create_log_directories(self):
        """
        Ensures that the necessary directories for each module are created.
        """
        # Create log directories for each module and log level
        for module in self.module_enum:
            for level in self.log_levels:
                log_dir = f"logs/{module.value}/{level}"
                os.makedirs(log_dir, exist_ok=True)

    def generate_logging_config(self):
        """
        Generates the dynamic logging configuration.
        :return: A dictionary representing the complete logging configuration.
        """
        handlers = self._create_handlers()
        loggers = self._create_loggers(handlers)

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": self._get_formatters(),
            "handlers": handlers,
            "loggers": loggers,
        }

    def _create_handlers(self):
        """
        Creates logging handlers for each module (debug, info, warning, error).
        :return: A dictionary of handlers.
        """
        handlers = {}
        # Create handlers for each module
        for module in self.module_enum:
            module_str = module.value
            for level in self.log_levels:
                handlers[f"{module_str}_{level}_file"] = {
                    "level": level.upper(),
                    "class": "logging.FileHandler",
                    "filename": f"logs/{module_str}/{level}/{date.today()}_{module_str}_{level}.log",
                    "formatter": "json",
                }

        # Add console handler for real-time logging
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }

        return handlers

    def _create_loggers(self, handlers):
        """
        Creates loggers for each module and adds the necessary handlers.
        :param handlers: The handlers dictionary created in _create_handlers().
        :return: A dictionary of loggers.
        """
        loggers = {
            "": {
                "handlers": ["console"]
                + [f"{module.value}_debug_file" for module in self.module_enum]
                + [f"{module.value}_info_file" for module in self.module_enum],
                "level": "DEBUG",
                "propagate": False,
            }
        }

        for module in self.module_enum:
            module_str = module.value
            loggers[module_str] = {
                "handlers": [
                    f"{module_str}_{level}_file"
                    for level in ["debug", "info", "warning", "error"]
                ],
                "level": "DEBUG",
                "propagate": False,
            }

        return loggers

    def _get_formatters(self):
        """
        Returns a dictionary of formatters.
        :return: A dictionary with formatters for the logs.
        """
        return {
            "json": {
                "()": CustomizedJSONFormatter,  # Replace with your actual formatter class
            },
            "app": {
                "()": ExtraFormatter,  # Replace with your actual formatter class
                "format": 'level: "%(levelname)s"\t msg: "%(message)s"\t logger: "%(name)s"\t func: "%(funcName)s"\t time: "%(asctime)s"',
                "datefmt": "%Y-%m-%dT%H:%M:%S.%z",
                "extra_fmt": "\t extra: %s",
            },
        }

    def get_logging_config(self):
        """
        Returns the full logging configuration dictionary.
        :return: A dictionary representing the complete logging configuration.
        """
        return self.logging_config
