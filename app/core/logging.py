import os, logging
from logging.config import dictConfig

def setup_logging(log_file: str = "./logs/app.log", level: str = "INFO"):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "std": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"}
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "std", "level": level},
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "std",
                "level": level,
                "filename": log_file,
                "maxBytes": 5_000_000,
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "root": {"handlers": ["console", "file"], "level": level},
        "loggers": {
            "uvicorn.access": {"level": "WARNING"},
            # "sqlalchemy.engine": {"level": "INFO"} # set to "INFO" to see SQL
        },
    })
    return logging.getLogger("app")
