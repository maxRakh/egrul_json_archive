DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            'level': 'INFO',
            "formatter": "default"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "app.log",
            "level": "INFO",
            "formatter": "default"
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"]
    }
}