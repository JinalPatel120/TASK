# # shopping_site/infrastucture/logger/services.py
import datetime
import logging
import os
from enum import Enum
from typing import List
import json_log_formatter
import ujson

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
    AUTHENTICATION = "authentication"
    PRODUCT = "product"
    ORDER = "order"

# shopping_site/infrastructure/logger/services.py

class LoggingService:
    def __init__(self, modules: Enum, log_levels: List[str]):
        self.log_levels = log_levels
        self.module_enum = modules
        self.handlers = {}
        self.loggers = {}
        self.create_log_directories()
        self.logging_config = self.generate_logging_config()

    def create_log_directories(self):
        for module in self.module_enum:
            for level in self.log_levels:
                log_dir = f"logs/{module.value}/{level}"
                os.makedirs(log_dir, exist_ok=True)
        # Create directories for request and response logs
        os.makedirs('logs/requests', exist_ok=True)
        os.makedirs('logs/responses', exist_ok=True)

    def generate_logging_config(self):
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
        handlers = {}

        # Module-specific log file handlers
        for module in self.module_enum:
            module_str = module.value
            for level in self.log_levels:
                handlers[f"{module_str}_{level}_file"] = {
                    "level": level.upper(),
                    "class": "logging.FileHandler",
                    "filename": f"logs/{module_str}/{level}/{datetime.date.today()}_{module_str}_{level}.log",
                    "formatter": "custom_format_with_counter" if level == "debug" else "json",
                }

        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }

        # Add handlers for request and response logs
        handlers["request_file"] = {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"logs/requests/{datetime.date.today()}_requests.log",
            "formatter": "json",
        }

        handlers["response_file"] = {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"logs/responses/{datetime.date.today()}_responses.log",
            "formatter": "json",
        }

        return handlers

    def _create_loggers(self, handlers):
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

        # Add request and response loggers
        loggers["request_logger"] = {
            "handlers": ["request_file"],
            "level": "INFO",
            "propagate": False,
        }

        loggers["response_logger"] = {
            "handlers": ["response_file"],
            "level": "INFO",
            "propagate": False,
        }

        return loggers

    def _get_formatters(self):
        return {
            "json": {
                "()": CustomizedJSONFormatter,
            },
            "custom_format_with_counter": {
                "()": CounterLogFormatter,
            },
        }

    def get_logging_config(self):
        return self.logging_config

    def add_runtime_log_file(self, module: str, level: str):
        """
        Adds a log file handler at runtime.
        """
        log_dir = f"logs/{module}/{level}"
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f"{log_dir}/{datetime.date.today()}_{module}_{level}.log"
        handler = logging.FileHandler(log_filename)
        handler.setLevel(level.upper())
        handler.setFormatter(self._get_formatters()["json" if level != "debug" else "custom_format_with_counter"])

        logger = logging.getLogger(module)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)  # Adjust as necessary
        self.loggers[module] = logger


# Example Usage
logging_service = LoggingService(modules=Module, log_levels=["debug", "info", "warning", "error"])
logging_config = logging_service.get_logging_config()

LOGGING = logging_config
