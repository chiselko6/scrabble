import os

LOG_FILE_PATH = '/tmp/scrabble/logs.txt'
# verify the target directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

SIMPLE_FORMATTER = {
    'format': '%(message)s',
}
STREAM_HANDLER = {
    'level': 'INFO',
    'class': 'logging.StreamHandler',
}

_BASE_LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'generic': {
            'format': '%(levelname)-5.5s [%(name)s] %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'log_file': {
            'level': 'NOTSET',
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': LOG_FILE_PATH,
        },
    },
    'loggers': {
        '': {
            'handlers': ('log_file',),
            'level': 'DEBUG',
        },
    },
}

SERVER_LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'generic': {
            'format': '%(levelname)-5.5s [%(name)s] %(message)s',
            'datefmt': '%H:%M:%S',
        },
        'simple': {
            'format': '%(message)s',
        },
    },
    'handlers': {
        'log_file': {
            'level': 'NOTSET',
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': LOG_FILE_PATH,
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ('log_file', 'console'),
            'level': 'DEBUG',
        },
    },
}

CLIENT_LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'generic': {
            'format': '%(levelname)-5.5s [%(name)s] %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'log_file': {
            'level': 'NOTSET',
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': LOG_FILE_PATH,
        },
    },
    'loggers': {'': {'handlers': ('log_file',), 'level': 'DEBUG'}},
}
