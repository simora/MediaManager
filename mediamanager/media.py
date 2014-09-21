import re, os
import threading
import datetime

import mediamanager
from mediamanager import logger, transcode
import utils.files as Files

__INITIALIZED__ = False
INIT_LOCK = threading.Lock()
PENDING_LOCK = threading.Lock()
PENDING_LASTRUN = None
MEDIA = {}
NONCOMPLIANT = {}
PENDING = {}

def updatePending(force=False):

  with PENDING_LOCK:

    global MEDIA, PENDING, PENDING_LASTRUN

    current_time = datetime.datetime.now()
    should_run = False
    if force or PENDING_LASTRUN is None or current_time - PENDING_LASTRUN >= datetime.timedelta(minutes=mediamanager.MEDIA_PENDING_CYCLETIME):
      should_run = True

    if should_run:
      PENDING_LASTRUN = current_time

      _files = []

      pattern = re.compile('^.*\.(' + mediamanager.TRANSCODER_PENDING_EXTENSION + ')$', re.I)

      for _source in mediamanager.SOURCES:
        if re.match('^(~).*$', _source) is not None:
          _files.extend(Files.getFilesFromDir(os.path.join(os.path.expanduser("~"), re.match('^~\/(.*)$', _source).group(1)), pattern))
        else:
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

def cleanPending():
  with PENDING_LOCK:

    _files = []

    pattern = re.compile('^.*\.(' + mediamanager.TRANSCODER_PENDING_EXTENSION + ')$', re.I)

    for _source in mediamanager.SOURCES:
      if re.match('^(~).*$', _source) is not None:
        _files.extend(Files.getFilesFromDir(os.path.join(os.path.expanduser("~"), re.match('^~\/(.*)$', _source).group(1)), pattern))
      else:
        _files.extend(Files.getFilesFromDir(_source, pattern))

    for _file in _files:
      try:
        logger.log("CleanPending :: Removing pending file; %s" % _file.path, logger.DEBUG)
        os.remove(_file.path)
      except Exception, e:
        logger.log("CleanPending :: Exception raised cleaing up pending file; %s" % _file.path, logger.DEBUG)
        logger.log("CleanPending :: Exception :: %s" % e, logger.DEBUG)


def is_pending(fileInfo):
  pattern = re.compile('^.*\.(' + mediamanager.TRANSCODER_PENDING_EXTENSION + ')$', re.I)

  _files = Files.getFilesFromDir(os.path.dirname(fileInfo.path), pattern)

  for _file in _files:
    _name = re.match('^(.*)\..*$', _file.basename).group(1)
    if _name == re.match('^(.*)\..*$', fileInfo.basename).group(1):
      return True
    else:
      return False

def is_compliant_container(fileInfo):
  if (re.match(re.compile('^.*(' + mediamanager.COMPLIANCE['Media']['Container']['Codec'] + ').*$', re.I), fileInfo.container) is None):
    return False
  else:
    return True

def is_compliant_audio(fileInfo, stream_id=None):
  if stream_id == None:
    for stream in fileInfo.audioStreams:
      if (re.match(re.compile('^.*(' + mediamanager.COMPLIANCE['Media']['Audio']['Codec'] + ').*$', re.I), stream['codec']) is None):
        return False
    return True
  else:
    try:
      if (re.match(re.compile('^.*(' + mediamanager.COMPLIANCE['Media']['Audio']['Codec'] + ').*$', re.I), fileInfo.audioStreams[stream_id]['codec']) is None):
        return False
      else:
        return True
    except Exception, e:
      logger.log(u"is_compliant_audio :: Exception caught; %s" % e, logger.DEBUG)
      return False

def is_compliant_video(fileInfo, stream_id=None):
  if stream_id == None:
    for stream in fileInfo.videoStreams:
      if (re.match(re.compile('^.*(' + mediamanager.COMPLIANCE['Media']['Video']['Codec'] + ').*$', re.I), stream['codec']) is None):
        return False
    return True
  else:
    try:
      if (re.match(re.compile('^.*(' + mediamanager.COMPLIANCE['Media']['Video']['Codec'] + ').*$', re.I), fileInfo.videoStreams[stream_id]['codec']) is None):
        return False
      else:
        return True
    except Exception, e:
      logger.log(u"is_compliant_video :: Exception caught; %s" % e, logger.DEBUG)
      return False

def is_compliant(fileInfo):
  if is_compliant_container(fileInfo) and is_compliant_audio(fileInfo) and is_compliant_video(fileInfo):
    return True
  else:
    return False

class Scan(object):
  @classmethod
  def ScanForCompliance(cls, files):
    retval = []
    if mediamanager.SCANNER_VERBOSE:
      logger.log(u"ScanForCompliance :: Starting", logger.DEBUG)
    for fileInfo in files:
      if isinstance(fileInfo, Files.VideoInfo):
        compliant = True
        if is_compliant_container(fileInfo):
          if mediamanager.SCANNER_VERBOSE:
            logger.log(u"ScanForCompliance :: File has compliant container; %s" % fileInfo.path, logger.DEBUG)
        else:
          if mediamanager.SCANNER_VERBOSE:
            logger.log(u"ScanForCompliance :: File has non-compliant container %s; %s" % (fileInfo.container, fileInfo.path))
          compliant = False
        for i, stream in enumerate(fileInfo.videoStreams):
          if is_compliant_video(fileInfo, stream_id=i):
            if mediamanager.SCANNER_VERBOSE:
              logger.log(u"ScanForCompliance :: File has compliant video stream at ID %s; %s" % (i, fileInfo.path), logger.DEBUG)
          else:
            if mediamanager.SCANNER_VERBOSE:
              logger.log(u"ScanForCompliance :: File has non-compliant video stream at ID %s of codec %s; %s" % (i, stream['codec'], fileInfo.path), logger.DEBUG)
            compliant = False
        for i, stream in enumerate(fileInfo.audioStreams):
          if is_compliant_audio(fileInfo, stream_id=i):
            if mediamanager.SCANNER_VERBOSE:
              logger.log(u"ScanForCompliance :: File has compliant audio stream at ID %s; %s" % (i, fileInfo.path), logger.DEBUG)
          else:
            if mediamanager.SCANNER_VERBOSE:
              logger.log(u"ScanForCompliance :: File has non-compliant audio stream at ID %s of codec %s; %s" % (i, stream['codec'], fileInfo.path), logger.DEBUG)
            compliant = False
        if not compliant:
          retval.append(fileInfo)
    if mediamanager.SCANNER_VERBOSE:
      logger.log(u"ScanForCompliance :: Completed", logger.DEBUG)
    return retval

  @classmethod
  def ScanForMedia(cls):
    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'ScanForMedia :: Starting', logger.DEBUG)
    _files = []
    _media = {}

    for _source in mediamanager.SOURCES:
      if mediamanager.SCANNER_VERBOSE:
        logger.log(u'ScanForMedia :: Getting files from source ' + _source, logger.DEBUG)
      if re.match('^(~).*$', _source) is not None:
        _files.extend(Files.getFilesFromDir(os.path.join(os.path.expanduser("~"), re.match('^~\/(.*)$', _source).group(1))))
      else:
        _files.extend(Files.getFilesFromDir(_source))

    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'ScanForMedia :: Found %d files' % len(_files), logger.DEBUG)

    for item in _files:
      if isinstance(item, Files.VideoInfo):
        match = re.match('^(.*)\..*$',item.basename)
        if match is not None:
          _media[match.group(1)] = item

    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'ScanForMedia :: Found %d video files' % len(_media.keys()), logger.DEBUG)
      logger.log(u'ScanForMedia :: Completed', logger.DEBUG)
    return _media

class Scanner():

  def __init__(self):
    self.amActive = False

  def run(self):

    global MEDIA, NONCOMPLIANT

    if self.amActive == True:
      if mediamanager.SCANNER_VERBOSE:
        logger.log(u'Scanner is still running, not starting it again', logger.MESSAGE)
      return

    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'Scanner has started', logger.MESSAGE)
    self.amActive = True

    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'Scanner is starting ScanForMedia()', logger.DEBUG)
    MEDIA = Scan.ScanForMedia()
    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'Scanner has completed ScanForMedia()', logger.DEBUG)
      logger.log(u'Scanner is starting updatePending()', logger.DEBUG)
    if updatePending():
      if mediamanager.SCANNER_VERBOSE:
        logger.log(u'Scanner has completed updatePending()', logger.DEBUG)
    else:
      if mediamanager.SCANNER_VERBOSE:
        logger.log(u'Scanner is skipping updatePending() due to insufficient time lapse since last update', logger.DEBUG)

    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'Scanner is queing items for transcode', logger.DEBUG)
    NONCOMPLIANT = Scan.ScanForCompliance(MEDIA.values())
    transcode_files = []

    for _file in NONCOMPLIANT:
      if not re.match('^(.*)\..*$', _file.basename).group(1) in PENDING.keys():
        transcode_files.append(_file)

    for _file in transcode_files:
      queueItem = None
      job = transcode.Factory.TranscodeJobFactory(_file)
      if job is not None:
        queueItem = mediamanager.queue_transcode.QueueItemTranscode(job)
      else:
        if mediamanager.SCANNER_VERBOSE:
          logger.log(u"Scanner TranscodeJob is None; %s" % _file.path, logger.DEBUG)

      if queueItem is not None and mediamanager.schedulerTranscode.action.add_item(queueItem):
        if mediamanager.SCANNER_VERBOSE:
          logger.log(u'Scanner has queued item for transcode; %s' % _file.path, logger.DEBUG)
      else:
        if queueItem is None:
          if mediamanager.SCANNER_VERBOSE:
            logger.log(u'Scanner unable to queue item, queueItem is None; %s' % _file.path, logger.DEBUG)

    if mediamanager.SCANNER_VERBOSE:
      logger.log(u'Scanner has completed', logger.MESSAGE)

    self.amActive = False

class Media(object):

  @property
  def path(self):
    return self._path

  def __init__(self, filename):
    self._path = filename
