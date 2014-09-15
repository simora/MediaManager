import mediamanager
from mediamanager import logger

class TranscodeJob:
  @property
  def name(self):
    return self._file.path
  @property
  def basename(self):
    return self._file.basename
  def __init__(self, fileInfo):
    self._file = fileInfo

  def run(self):
    logger.log(u'TranscodeJob :: Job run for file %s' % self.name)

class VerificationAcceptJob(TranscodeJob):

  def __init__(self, fileInfo):
    self._file = fileInfo

  def run(self):
    logger.log(u'VerificationAcceptJob :: Job run for file %s' % self.name)

class VerificationDeclineJob(TranscodeJob):

  def __init__(self, fileInfo):
    self._file = fileInfo

  def run(self):
    logger.log(u'VerificationDeclineJob :: Job run for file %s' % self.name)

class WorkTranscode():

  def __init__(self, fileinfo):
    self._file = fileinfo

class WorkVerificationDecline():

  def __init__(self, fileinfo):
    self._file = fileinfo

class WorkVerificationAccept():

  def __init__(self, fileinfo):
    self._file = fileinfo
