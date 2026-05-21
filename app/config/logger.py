import datetime
import logging
import sys

import colorlog
import pytz

from config.config import LOG_LEVEL


class Formatter(colorlog.ColoredFormatter):
    @staticmethod
    def converter(timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        return dt.astimezone(pytz.timezone('Asia/Colombo'))

    def formatTime(self, record, date_format=None):
        dt = self.converter(record.created)
        if date_format:
            s = dt.strftime(date_format)
        else:
            try:
                s = dt.isoformat(timespec='milliseconds')
            except TypeError:
                s = dt.isoformat()
        return s


FORMAT = '%(log_color)s%(levelname)-9s %(asctime)s.%(msecs)03d %(name)s:%(lineno)s %(message)s'


def setup_logger():
    formatter = Formatter(FORMAT, log_colors={
        'DEBUG': 'green',
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }, datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.propagate = False
    logger.setLevel(LOG_LEVEL)
