import logging
from logging.handlers import TimedRotatingFileHandler

from consts import ENV


def _log_file_path(filename):
    if ENV == 'real':
        return f'/root/arbitrage/log/{filename}'
    return f'C:/Users/skdba/PycharmProjects/arbitrage/log/{filename}'


def _formatter():
    if ENV == 'real':
        return logging.Formatter('[%(asctime)s][%(levelname)s]:%(message)s')
    return logging.Formatter('[%(asctime)s][%(levelname)s]:%(message)s ...(%(filename)s:%(lineno)d)')


def _setup_logging(filename):
    logging.basicConfig(level=logging.INFO)
    file_handler = TimedRotatingFileHandler(
        filename=_log_file_path(filename),
        when='midnight',
        interval=1,
        backupCount=30,
    )
    file_handler.suffix = "%Y%m%d"
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(_formatter())
    logging.getLogger().addHandler(file_handler)


def setup_collect_logging():
    _setup_logging('premium.log')


def setup_order_logging():
    _setup_logging('order.log')
