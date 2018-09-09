import sys
import logging

logger = logging.getLogger()
formatter = logging.Formatter('%(message)s')
output = logging.StreamHandler(sys.stdout)
output.setFormatter(formatter)
logger.addHandler(output)
logger.setLevel(logging.INFO)

LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}
