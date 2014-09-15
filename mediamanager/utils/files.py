import re, os
from lib.pymediainfo import MediaInfo

VIDEO_EXTENSIONS = [ 'mp4', 'mkv', 'm4v', 'avi' ]
AUDIO_EXTENSIONS = [ 'mp3', 'ogg' ]

def getFilesFromDir(dirname, pattern=None):
  retval = []
  if os.path.isdir(dirname):
    if pattern is not None:
      for root, dirs, files in os.walk(dirname):
        for x in files:
          if pattern.match(x) is not None:
            info = FileFactory.Factory(os.path.join(root,x))
            if info is not None:
              retval.append(info)
    else:
      for root, dirs, files in os.walk(dirname):
        for x in files:
          info = FileFactory.Factory(os.path.join(root,x))
          if info is not None:
            retval.append(info)
  return retval

def isVideo(filename):
  pattern = re.compile('^((?!\.).*\.(' + '|'.join(VIDEO_EXTENSIONS) + '))$', re.I)
  if os.path.isfile(filename):
    if pattern.match(filename) is not None:
      return True
    else:
      return False
  else:
    return False

def isAudio(filename):
  pattern = re.compile('^((?!\.).*\.(' + '|'.join(AUDIO_EXTENSIONS) + '))$', re.I)
  if os.path.isfile(filename):
    if pattern.match(filename) is not None:
      return True
    else:
      return False
  else:
    return False

class FileFactory(object):
  @classmethod
  def Factory(cls, filename):
    if os.path.isfile(filename):
      if isVideo(filename):
        return VideoInfo(filename)
      else:
        return FileInfo(filename)

class FileInfo(object):
  @property
  def mode(self):
    return self._st[ST_MODE]
  @property
  def ino(self):
    return self._st[ST_INO]
  @property
  def dev(self):
    return self._st[ST_DEV]
  @property
  def nlink(self):
    return self._st[ST_NTLINK]
  @property
  def uid(self):
    return self._st[ST_UID]
  @property
  def gid(self):
    return self._st[ST_GID]
  @property
  def size(self):
    return self._st[ST_SIZE]
  @property
  def atime(self):
    return self._st[ST_ATIME]
  @property
  def mtime(self):
    return self._st[ST_MTIME]
  @property
  def ctime(self):
    return self._st[ST_CTIME]
  @property
  def path(self):
    return self._path
  @property
  def basename(self):
    return os.path.basename(self._path)
  @property
  def checksum(self):
    try:
      return self._checksum
    except:
      pass
    return None

  def __init__(self, filename):
    if os.path.isfile(filename):
      self._path = filename
      self._getFileInfo()
    else:
      raise ValueError('Is not a file')

  def _getFileInfo(self):
    self._st = os.stat(self._path)



class VideoInfo(FileInfo):
  @property
  def tracks(self):
    try:
      return self._tracks
    except:
      pass
    return None

  @property
  def container(self):
    return self._container
  @property
  def duration(self):
    return self._duration
  @property
  def videoStreams(self):
    return self._videoStreams
  @property
  def audioStreams(self):
    return self._audioStreams
  @property
  def subtitleStreams(self):
    return self._subtitleStreams
  @property
  def chapters(self):
    return self._chapters
  @property
  def isPending(self):
    return self._isPending
  @isPending.setter
  def isPending(self, value):
    if isinstance(value, bool):
      _isPending = value
    else:
      raise ValueError('Is not bool')

  def __init__(self, filename):
    super(VideoInfo, self).__init__(filename)
    self._videoStreams = []
    self._audioStreams = []
    self._subtitleStreams = []
    self._chapters = []
    self._isPending = None
    if not isVideo(self._path):
      raise ValueError('File %s is not a valid video file' % self._path)
    self._tracks = MediaInfo.parse(os.path.join(self._path)).to_data()['tracks']
    for track in self._tracks:
      if track['track_type'] == 'General':
        self._container = track.get('codec', '')
        self._duration = track.get('duration', '')
      elif track['track_type'] == 'Video':
        self._videoStreams.append(track)
      elif track['track_type'] == 'Audio':
        self._audioStreams.append(track)
      elif track['track_type'] == 'Menu' and track.get('chapters_pos_begin', None) is not None:
        self._chapters.append(track)


#class AudioFile(object):
