import os, sys, threading, logging
from os.path import expanduser

import mediamanager

__INITIALIZED__ = False
ERROR = logging.ERROR
WARNING = logging.WARNING
MESSAGE = logging.INFO
DEBUG = logging.DEBUG
LOG_LOCK = threading.Lock()
INIT_LOCK = threading.Lock()
LOG_HANDLER = None

LOG_FILE = 'mediamanager.log'
LOG_PATH = None
LOG_LEVEL = logging.DEBUG

reverseNames = {u'ERROR': ERROR,
                u'WARNING': WARNING,
                u'INFO': MESSAGE,
                u'DEBUG': DEBUG}

def initialize():
  with INIT_LOCK:

    global __INITIALIZED__, LOG_HANDLER, LOG_PATH

    if __INITIALIZED__:
      return False

    if not LOG_PATH:
      LOG_PATH = expanduser("~")

    LOG_HANDLER = logging.FileHandler(os.path.join(LOG_PATH, LOG_FILE), encoding='utf-8')
    LOG_HANDLER.setLevel(logging.DEBUG)

    LOG_HANDLER.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'))

    logging.getLogger('mediamanager').addHandler(LOG_HANDLER)
    logging.getLogger('mediamanager').setLevel(LOG_LEVEL)

    __INITIALIZED__ = True
    return True

def log(toLog, logLevel=MESSAGE):
  with LOG_LOCK:
    mm_logger = logging.getLogger('mediamanager')

    meThread = threading.currentThread().getName()
    out_line = meThread + u" :: " + toLog

    try:
      if logLevel == DEBUG:
        mm_logger.debug(out_line)
      elif logLevel == MESSAGE:
        mm_logger.info(out_line)
      elif logLevel == WARNING:
        mm_logger.warning(out_line)
      elif logLevel == ERROR:
        mm_logger.error(out_line)
      else:
        mm_logger.log(logLevel, out_line)
    except ValueError:
      pass

def close_log():
  mm_logger = logging.getLogger('mediamanager')
  mm_logger.removeHandler(LOG_HANDLER)
  LOG_HANDLER.flush()
  LOG_HANDLER.close()
