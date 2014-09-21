import os, re
import datetime
import threading

from mediamanager import logger
from mediamanager import scheduler, media, scheduler_transcode, queue_transcode

import utils.files as Files

__INITIALIZED__ = False
INIT_LOCK = threading.Lock()
#SOURCES = ["~/SampleData/Films", "~/SampleData/Series"]
SOURCES = ["~/SampleData/Series"]
COMPLIANCE = None
VERBOSE = False
CLEAN_PENDING_ON_INITIALIZE = True

SCANNER_FREQUENCY = 1
SCANNER_VERBOSE = False


MEDIA_PENDING_CYCLETIME = 6000

schedulerScanner = None
schedulerTranscode = None

TRANSCODER_TEMPDIR = '~/temp_conversion'
TRANSCODER_PENDING_EXTENSION = 'mmtemp' # Extension with no leading period
TRANSCODER_PENDING_LIMIT = 100

def initialize():

  with INIT_LOCK:

    global __INITIALIZED__, SOURCES, COMPLIANCE, schedulerScanner, schedulerTranscode, TRANSCODER_TEMPDIR

    if __INITIALIZED__:
      return False

    logger.initialize()

    tempSOURCES = []
    for source in SOURCES:
      if re.match('^(~).*$', source) is not None:
        tempSOURCES.append(os.path.join(os.path.expanduser("~"), re.match('^~\/(.*)$', source).group(1)))
      else:
        tempSOURCES.append(source)
    SOURCES = tempSOURCES

    tempTRANSCODER_TEMPDIR = None
    if re.match('^(~).*$', TRANSCODER_TEMPDIR) is not None:
      tempTRANSCODER_TEMPDIR = os.path.join(os.path.expanduser("~"), re.match('^~\/(.*)$', TRANSCODER_TEMPDIR).group(1))
    else:
      tempTRANSCODER_TEMPDIR = TRANSCODER_TEMPDIR
    TRANSCODER_TEMPDIR = tempTRANSCODER_TEMPDIR



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

    if CLEAN_PENDING_ON_INITIALIZE:
      media.cleanPending()

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
      schedulerTranscode.abort = True
      logger.log(u'Waiting for the TRANSCODER thread to exit')
      try:
        schedulerTranscode.thread.join(10)
      except:
        pass

      __INITIALIZED__ = False

def shutdown():

  halt()

  logger.log(u'Exiting MediaManager')

  os._exit(0)
