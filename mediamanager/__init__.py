import os
import datetime
import threading

from mediamanager import logger
from mediamanager import scheduler, media, scheduler_transcode

import utils.files as Files

__INITIALIZED__ = False
INIT_LOCK = threading.Lock()
SOURCES = None
COMPLIANCE = None
VERBOSE = False

SCANNER_FREQUENCY = 5


MEDIA_PENDING_CYCLETIME = 10

schedulerScanner = None
schedulerTranscode = None

TRANSCODER_TEMPDIR = '~/temp_conversion'
TRANSCODER_PENDING_EXTENSION = 'mmtemp' # Extension with no leading period
TRANSCODER_PENDING_LIMIT = 20

def initialize():

  with INIT_LOCK:

    global __INITIALIZED__, SOURCES, COMPLIANCE, schedulerScanner, schedulerTranscode

    if __INITIALIZED__:
      return False

    logger.initialize()

    SOURCES = ["~/SampleData/Films", "~/SampleData/Series"]

    COMPLIANCE = {}
    COMPLIANCE['Media'] = {}
    COMPLIANCE['Media']['Container'] = {}
    COMPLIANCE['Media']['Container']['Codec'] = 'Matroska'
    COMPLIANCE['Media']['Video'] = {}
    COMPLIANCE['Media']['Video']['Codec'] = 'AVC'
    COMPLIANCE['Media']['Audio'] = {}
    COMPLIANCE['Media']['Audio']['Codec'] = 'AC3'
    COMPLIANCE['Media']['Audio']['Rate'] = 48000
    COMPLIANCE['Media']['Subtitles'] = {}
    COMPLIANCE['Media']['Subtitles']['Codec'] = 'SSA'
    COMPLIANCE['Media']['Subtitles']['BurnIn'] = False

    schedulerScanner = scheduler.Scheduler(media.Scanner(),
                                          cycleTime=datetime.timedelta(minutes=SCANNER_FREQUENCY),
                                          threadName='SCANNER',
                                          run_delay=datetime.timedelta(minutes=0)
                                          )

    schedulerTranscode = scheduler_transcode.SchedulerTranscode(queue_transcode.QueueTranscode(),
                                                               threadName="TRANSCODER")

    __INITIALIZED__ = True
    return True

def start():

  global __INITIALIZED__, schedulerScanner

  with INIT_LOCK:

    if __INITIALIZED__:

      schedulerTranscode.thread.start()

      schedulerScanner.thread.start()

def halt():

  global __INITIALIZED__, schedulerScanner

  with INIT_LOCK:

    if __INITIALIZED__:

      logger.log(u'Aborting all threads')

      schedulerScanner.abort = True
      logger.log(u'Waiting for the SCANNER thread to exit')
      try:
        schedulerScanner.thread.join(10)
      except:
        pass

      __INITIALIZED__ = False

def shutdown():

  halt()

  logger.log(u'Exiting MediaManager')

  os._exit(0)
