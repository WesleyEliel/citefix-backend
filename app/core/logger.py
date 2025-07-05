import logging
from logging.config import dictConfig

from app.core.configs import settings

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s - %(filename)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "formatter": "verbose",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if settings.DEBUG else "INFO",
            "propagate": False
        },
        "motor": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "urllib3": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING"
    }
}


def configure_logging():
    dictConfig(LOG_CONFIG)
    logging.captureWarnings(True)
