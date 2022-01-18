# -*- coding: utf-8 -*-

LOGGING_DICT = {
    "version": 1,
    "formatters": {
        "default":{
            "format":"%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt":"%Y-%m-%d %H:%M:%S"
        },
        "short":{
            "format":"%(asctime)s - %(levelname)s - %(message)s",
            "datefmt":"%y-%M-%d %H:%M:%S"
        },
    },
    "handlers":{
        "file":{
            "class":"logging.handlers.RotatingFileHandler",
            "level":"INFO",
            "formatter":"default",
            "filename": "filelog.log",
            "mode":"a",
            "encoding": "utf8",
            "maxBytes":100000,
            "backupCount":7
        },
        "console":{
            "class":"logging.StreamHandler",
            "level":"INFO",
            "formatter":"short",
            "stream":"ext://sys.stdout"
        }
    },
    "loggers":{
        "console_logger":{
            "handlers":["console"],
            "level":"INFO",
        },
        "file_logger":{
            "handlers":["file"],
            "level":"INFO",
        },
        "double_logger": {
            "handlers": ["console","file"],
            "level": "INFO",
        },
    }
}