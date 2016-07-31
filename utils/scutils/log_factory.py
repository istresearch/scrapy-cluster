import logging
import sys
import datetime
import os
import errno
import copy

from pythonjsonlogger import jsonlogger
from cloghandler import ConcurrentRotatingFileHandler


class LogFactory(object):
    '''
    Goal is to manage Simple LogObject instances
    Like a Singleton
    '''
    _instance = None

    @classmethod
    def get_instance(self, **kwargs):
        if self._instance is None:
            self._instance = LogObject(**kwargs)

        return self._instance


class LogObject(object):
    '''
    Easy wrapper for writing json logs to a rotating file log
    '''

    level_dict = {
        "DEBUG": 0,
        "INFO": 1,
        "WARN": 2,
        "WARNING": 2,
        "ERROR": 3,
        "CRITICAL": 4,
    }

    def __init__(self, json=False, stdout=True, name='scrapy-cluster',
                 dir='logs', file='main.log', bytes=25000000, backups=5,
                 level='INFO',
                 format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                 propagate=False):
        '''
        @param stdout: Flag to write logs to stdout or file
        @param json: Flag to write json logs with objects or just the messages
        @param name: The logger name
        @param dir: The directory to write logs into
        @param file: The file name
        @param bytes: The max file size in bytes
        @param backups: The number of backups to keep of the file
        @param level: The logging level string
        @param format: The log format
        @param propagate: Allow the log to propagate to other ancestor loggers

        '''
        # set up logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = propagate
        self.json = json
        self.log_level = level
        self.format_string = format

        if stdout:
            # set up to std out
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.DEBUG)
            formatter = self._get_formatter(json)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
            self._check_log_level(level)
            self.debug("Logging to stdout")
        else:
            # set up to file
            try:
                # try to make dir
                os.makedirs(dir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

            file_handler = ConcurrentRotatingFileHandler(dir + '/' + file,
                                                         maxBytes=bytes,
                                                         backupCount=backups)
            file_handler.setLevel(logging.DEBUG)
            formatter = self._get_formatter(json)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self._check_log_level(level)
            self.debug("Logging to file: {file}".format(
                    file=dir+'/'+file))

    def _check_log_level(self, level):
        '''
        Ensures a valid log level

        @param level: the asked for level
        '''
        if level not in self.level_dict.keys():
            self.log_level = 'DEBUG'
            self.logger.warn("Unknown log level '{lev}', defaulting to DEBUG"
                             .format(lev=level))

    def _get_formatter(self, json):
        '''
        Return the proper log formatter

        @param json: Boolean value
        '''
        if json:
            return jsonlogger.JsonFormatter()
        else:
            return logging.Formatter(self.format_string)

    def debug(self, message, extra={}):
        '''
        Writes an error message to the log

        @param message: The message to write
        @param extra: The extras object to pass in
        '''
        if self.level_dict['DEBUG'] >= self.level_dict[self.log_level]:
            extras = self.add_extras(extra, "DEBUG")
            self._write_message(message, extras)

    def info(self, message, extra={}):
        '''
        Writes an info message to the log

        @param message: The message to write
        @param extra: The extras object to pass in
        '''
        if self.level_dict['INFO'] >= self.level_dict[self.log_level]:
            extras = self.add_extras(extra, "INFO")
            self._write_message(message, extras)

    def warn(self, message, extra={}):
        '''
        Writes a warning message to the log

        @param message: The message to write
        @param extra: The extras object to pass in
        '''
        self.warning(message, extra)

    def warning(self, message, extra={}):
        '''
        Writes a warning message to the log

        @param message: The message to write
        @param extra: The extras object to pass in
        '''
        if self.level_dict['WARNING'] >= self.level_dict[self.log_level]:
            extras = self.add_extras(extra, "WARNING")
            self._write_message(message, extras)

    def error(self, message, extra={}):
        '''
        Writes an error message to the log

        @param message: The message to write
        @param extra: The extras object to pass in
        '''
        if self.level_dict['ERROR'] >= self.level_dict[self.log_level]:
            extras = self.add_extras(extra, "ERROR")
            self._write_message(message, extras)

    def critical(self, message, extra={}):
        '''
        Writes a critical message to the log

        @param message: The message to write
        @param extra: The extras object to pass in
        '''
        if self.level_dict['CRITICAL'] >= self.level_dict[self.log_level]:
            extras = self.add_extras(extra, "CRITICAL")
            self._write_message(message, extras)

    def _write_message(self, message, extra):
        '''
        Writes the log output
        @param message: The message to write
        @param extra: The potential object to write
        '''
        if not self.json:
            self._write_standard(message, extra)
        else:
            self._write_json(message, extra)

    def _write_standard(self, message, extra):
        '''
        Writes a standard log statement

        @param message: The message to write
        @param extra: The object to pull defaults from
        '''
        if extra['level'] == 'INFO':
            self.logger.info(message)
        elif extra['level'] == 'DEBUG':
            self.logger.debug(message)
        elif extra['level'] == 'WARNING':
            self.logger.warning(message)
        elif extra['level'] == 'ERROR':
            self.logger.error(message)
        elif extra['level'] == 'CRITICAL':
            self.logger.critical(message)
        else:
            self.logger.debug(message)

    def _write_json(self, message, extra):
        '''
        The JSON logger doesn't obey log levels

        @param message: The message to write
        @param extra: The object to write
        '''
        self.logger.info(message, extra=extra)

    def name(self):
        '''
        Returns the logger name
        '''
        return self.logger.name

    def add_extras(self, dict, level):
        '''
        Adds the log level to the dict object
        '''
        my_copy = copy.deepcopy(dict)
        if 'level' not in my_copy:
            my_copy['level'] = level
        if 'timestamp' not in my_copy:
            my_copy['timestamp'] = self._get_time()
        if 'logger' not in my_copy:
            my_copy['logger'] = self.name()
        return my_copy

    def _get_time(self):
        '''
        Returns the system time
        '''
        return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
