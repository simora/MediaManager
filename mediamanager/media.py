import re
import threading
import datetime

import mediamanager
from mediamanager import logger, transcode, queue_transcode
import utils.files as Files

__INITIALIZED__ = False
INIT_LOCK = threading.Lock()
MEDIA = None
PENDING_LOCK = threading.Lock()
PENDING_LASTRUN = None
PENDING = {}

def updatePending():

  with PENDING_LOCK:

    global MEDIA, PENDING, PENDING_LASTRUN

    current_time = datetime.datetime.now()
    should_run = False
    if PENDING_LASTRUN is None:
      PENDING_LASTRUN = current_time
      should_run = True

    if current_time - PENDING_LASTRUN >= datetime.timedelta(minutes=mediamanager.MEDIA_PENDING_CYCLETIME):
      should_run = True

    if should_run:
      PENDING_LASTRUN = current_time

      _files = []

      pattern = re.compile('^.*\.(.mmtemp)$', re.I)

      for _source in mediamanager.SOURCES:
        _files.extend(Files.getFilesFromDir(_source, pattern))

      _pending = {}

      for _file in _files:
        _name = re.match('^(.*)\..*$', _file.basename).group(1)
        if _name in MEDIA.keys():
          _pending[_name] = _file

      PENDING = _pending
      return True
    else:
      return False

class Scan(object):
  @classmethod
  def ScanForCompliance(cls, _files):
    retval = []
    for _file in _files:
      if isinstance(_file, Files.VideoInfo):
        append = False
        for audio in _file.audioStreams:
          if (re.match(re.compile('^.*(' + '|'.join(mediamanager.COMPLIANCE['Media']['Audio']['Codec']) + ').*$', re.I), audio['codec']) is None):
            if mediamanager.VERBOSE:
              print('Non-Compliant: File %s has audio stream %s' % (_file.basename, audio['codec']))
            append = True
          else:
            if mediamanager.VERBOSE:
              print('Compliant: File %s has audio stream %s' % (_file.basename, audio['codec']))
        for video in _file.videoStreams:
          if (re.match(re.compile('^.*(' + '|'.join(mediamanager.COMPLIANCE['Media']['Video']['Codec']) + ').*$', re.I), video['codec']) is None):
            if mediamanager.VERBOSE:
              print('Non-Compliant: File %s has video stream %s' % (_file.basename, video['codec']))
            append = True
          else:
            if mediamanager.VERBOSE:
              print('Compliant: File %s has video stream %s' % (_file.basename, video['codec']))
        if (re.match(re.compile('^.*(' + '|'.join(mediamanager.COMPLIANCE['Media']['Container']['Codec']) + ').*$', re.I), _file.container) is None):
          if mediamanager.VERBOSE:
            print('Non-Compliant: File %s has container type %s' % (_file.basename, _file.container))
          append = True
        else:
          if mediamanager.VERBOSE:
            print('Compliant: File %s has container type %s' % (_file.basename, _file.container))
        if append:
          retval.append(_file)
    return retval

  @classmethod
  def ScanForMedia(cls):
    logger.log(u'ScanForMedia :: Starting', logger.DEBUG)
    _files = []
    _media = {}

    for _source in mediamanager.SOURCES:
      logger.log(u'ScanForMedia :: Getting files from source ' + _source, logger.DEBUG)
      _files.extend(Files.getFilesFromDir(_source))

    logger.log(u'ScanForMedia :: Found %d files' % len(_files), logger.DEBUG)

    for item in _files:
      if isinstance(item, Files.VideoInfo):
        match = re.match('^(.*)\..*$',item.basename)
        if match is not None:
          _media[match.group(1)] = item

    logger.log(u'ScanForMedia :: Found %d video files' % len(_media.keys()), logger.DEBUG)
    logger.log(u'ScanForMedia :: Completed', logger.DEBUG)
    return _media

class Scanner():

  def __init__(self):
    self.amActive = False

  def run(self):

    global MEDIA

    if self.amActive == True:
      logger.log(u'Scanner is still running, not starting it again', logger.MESSAGE)
      return

    logger.log(u'Scanner has started', logger.MESSAGE)
    self.amActive = True

    logger.log(u'Scanner is starting ScanForMedia()', logger.DEBUG)
    MEDIA = Scan.ScanForMedia()
    logger.log(u'Scanner has completed ScanForMedia()', logger.DEBUG)
    logger.log(u'Scanner is starting updatePending()', logger.DEBUG)
    if updatePending():
      logger.log(u'Scanner has completed updatePending()', logger.DEBUG)
    else:
      logger.log(u'Scanner is skipping updatePending() due to insufficient time lapse since last update', logger.DEBUG)

    logger.log(u'Scanner is queing items for transcode', logger.DEBUG)
    nonCompliant = []
    for k, v in MEDIA.items():
      if not k in PENDING.keys():
        nonCompliant.append(v)

    for item in nonCompliant:
      job = transcode.TranscodeJob(item)
      queueItem = queue_transcode.QueueItemTranscode(job)

      if mediamanager.schedulerTranscode.action.add_item(queueItem):
        logger.log(u'Scanner has queued item for transcode; %s' % item.path, logger.DEBUG)
      else:
        logger.log(u'Scanner unable to queue item; %s' % item.path, logger.DEBUG)

    logger.log(u'Scanner has completed', logger.MESSAGE)

    self.amActive = False

class Media(object):

  @property
  def path(self):
    return self._path

  def __init__(self, filename):
    self._path = filename
