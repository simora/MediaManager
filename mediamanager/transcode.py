import os, re
import av
import time
import shutil
from threading import Lock

import mediamanager
from mediamanager import logger

from lib.ffmpegwrapper import VideoCodec, AudioCodec, FFmpeg, Input, Output

import utils.files as Files

class TranscodeJob():

  __FINISH_LOCK__ = Lock()
  __FINISHED__ = None

  @property
  def name(self):
    return self._file.path
  @property
  def basename(self):
    return self._file.basename
  def __init__(self, fileInfo, audio_stream_id=None, video_stream_id=None, subtitle_stream_id=None):
    self._file = fileInfo
    self._audio_stream_id = audio_stream_id
    self._video_stream_id = video_stream_id
    self._subtitle_stream_id = subtitle_stream_id
    self._outfile_base = None
    self._pending_file_basename = None
    self._pending_file_path = None
    self._pending_file_tempbasename = None
    self._pending_file_temppath = None
    self._process = None
    self.abort = False

    pattern = re.compile('^(.*)\..*$')
    if pattern.match(self._file.basename) is not None:
      self._outfile_base = pattern.match(self._file.basename).group(1)


  def run(self):
    # List of all finalized files that need to be remuxed into final product
    self.finalfiles = []
    logger.log("Entering transcode job; %s" % self._file.path, logger.MESSAGE)

    #Beginning demux operations
    logger.log("Beginning deumx; %s" % self._file.path, logger.DEBUG)
    demux_successful = self.demux_file()
    logger.log("Completed deumx; %s" % self._file.path, logger.DEBUG)
    if not demux_successful:
      logger.log("Demux failed; %s" % self._file.path, logger.MESSAGE)
      logger.log("Exiting transcode job; %s" % self._file.path, logger.MESSAGE)
      return
    else:
      logger.log("Demux successful; %s" % self._file.path, logger.DEBUG)

    # Since we aren't transcoding video just identify the streams and add them to the self.finalfiles list
    for _file in self.demuxfiles:
      if re.match('^.*\.(video.\d)\..*$', _file) is not None:
        self.finalfiles.append(_file)

    # Check if we need to abort before proceeding
    if self.abort:
      self.finish()
      return

    # Begin audio transcoding operation looping over demuxed files where contents is audio
    convert_results = []
    for _file in self.demuxfiles:
      if re.match('^.*\.(audio.\d)\..*$', _file) is not None:
        logger.log("Beginning remediate audio; %s" % _file, logger.DEBUG)
        result = self.remediate_audio(_file)
        if result:
          logger.log("Remediate audio successful; %s" % _file, logger.DEBUG)
        else:
          logger.log("Remediate audio successful; %s" % _file, logger.DEBUG)
        convert_results.append(result)
    if False in convert_results:
      logger.log("Remediation of audio Failed; %s" % _file, logger.DEBUG)
      logger.log("Exiting transcode job; %s" % self._file.path, logger.MESSAGE)
      return

    # Check if we need to abort before proceeding
    if self.abort:
      self.finish()
      return

    # Begin remuxing operation
    logger.log("Beginning remux of sreams; %s" % self._file.path, logger.DEBUG)
    if self.remux_files():
      logger.log("Remuxing of sreams successful; %s" % self._file.path, logger.DEBUG)
    else:
      logger.log("Remuxing of streams unsuccessful; %s" % self._file.path, logger.DEBUG)
      logger.log("Exiting transcode job; %s" % self._file.path, logger.MESSAGE)
      return

    # Perform final operation of copying file from temp to src file's parent directory and renaming according to user set pending extension
    logger.log("Beginning finalization of job; %s" % self._file.path, logger.DEBUG)
    if not self.finalize():
      logger.log("Finalization of job failed; %s" % self._file.path, logger.DEBUG)
      logger.log("Exiting transcode job; %s" % self._file.path, logger.MESSAGE)
      return
    else:
      logger.log("Finalization of job successful; %s" % self._file.path, logger.DEBUG)

    # All done. State some logging.
    logger.log("Completed job execution; %s" % self._file.path, logger.DEBUG)
    logger.log("Exiting transcode job; %s" % self._file.path, logger.MESSAGE)

  def demux_file(self):

    # Return if we couldn't get the base file name without extension from the self._file.basename
    if not self._outfile_base:
      logger.log("Unable to get base file name; %s" % self._file.path, logger.DEBUG)
      return False

    # Create our Input() object to specify the file we will be demuxing
    input_file = Input(self._file.path)

    # Create a list of the codecs with maps or input stream to output file
    codecs = []

    # Create a list to contain the paths of all the output files
    self.demuxfiles = []

    # Iterate over self._file.videoStreams and create codecs for each video stream with 'copy' specified so no transcoding is done
    for i, stream in enumerate(self._file.videoStreams):
      stream_id = int(stream['track_id']) - 1
      outfile_path = os.path.join(mediamanager.TRANSCODER_TEMPDIR, self._outfile_base + '.video.' + str(stream_id) + '.mkv')
      video_codec = VideoCodec('copy')
      video_codec = video_codec.mapstream("0:%d" % stream_id, outfile_path)
      self.demuxfiles.append(outfile_path)
      codecs.append(video_codec)

    # Iterate over self._file.audioStreams and create codecs for each audio stream with 'copy' specified so no transcoding is done
    for i, stream in enumerate(self._file.audioStreams):
      stream_id = int(stream['track_id']) - 1
      outfile_path = os.path.join(mediamanager.TRANSCODER_TEMPDIR, self._outfile_base + '.audio.' + str(stream_id) + '.mkv')
      audio_codec = AudioCodec('copy')
      audio_codec = audio_codec.mapstream("0:%d" % stream_id, outfile_path)
      self.demuxfiles.append(outfile_path)
      codecs.append(audio_codec)

    # Create FFmpeg() object to begin demux operation
    demux_job = FFmpeg('/usr/bin/ffmpeg', input_file)

    # Iterate over items in codecs list and insert them at the end of the FFmpeg() object's list
    for codec in codecs:
      demux_job.insert(len(demux_job), codec)

    # Begin demux operation and iterate over piped stdout from the popen process
    logger.log("demux_job: %s" % demux_job, logger.DEBUG)
    with demux_job as self._process:
      while  not self.abort and self._process.running:
        for line in self._process.readlines():
          if mediamanager.VERBOSE:
            logger.log(line, logger.DEBUG)
      if self._process.failed:
        return False
      elif self._process.successful:
        return True
      else:
        return False

  def remediate_audio(self, path):

    # Create our Input() object to specify file we will be transcoding
    input_file = Input(path)

    # Create variables we will be using in the following code
    codec = None
    output_path = re.match('^(.*)\.audio\.\d\.mkv$', path).group(1) + '.final.audio.' + re.match('^.*\.audio\.(\d)\.mkv$', path).group(1) + '.mkv'
    output_file = Output(output_path)

    # Check if self.finalfiles is not none and if so create a list object. This is so we don't lose files already in the list
    if self.finalfiles is None:
      self.finalfiles = []

    # Create our AudioCodec() object to define the output codec and bitrate
    codec = AudioCodec('ac3')
    codec = codec.bitrate('448k')

    # Instance our FFmpeg() object to begin processing
    remediate_audio_job = FFmpeg('/usr/bin/ffmpeg', input_file, codec, output_file)

    # Begin the transcoding operation iterating over the piped stdout from the command
    with remediate_audio_job as self._process:
      while not self.abort and self._process.running:
        for line in self._process.readlines():
          if mediamanager.VERBOSE:
            logger.log(line, logger.DEBUG)
      if self._process.failed:
        return False
      elif self._process.successful:
        self.finalfiles.append(output_path)
        return True
      else:
        return False

  def remux_files(self):

    # Create our output file object for ffmpegwrapper
    if mediamanager.COMPLIANCE['Media']['Container']['Codec'] == 'Matroska':
      self._muxed_file_basename = self._outfile_base + '.' + 'mkv'
    elif mediamanager.COMPLIANCE['Media']['Container']['Codec'] == 'MPEG-4':
      self._muxed_file_basename = self._outfile_base + '.' + 'mp4'
    self._muxed_file_path = os.path.join(mediamanager.TRANSCODER_TEMPDIR, self._muxed_file_basename)
    output_file = Output(self._muxed_file_path)

    # Create our FFmpeg job object with path to ffmpeg binary
    remux_job = FFmpeg('/usr/bin/ffmpeg')

    # Iterate for self.finalfiles and create Input() objects for input files and insert at the end of the list
    for _file in self.finalfiles:
      input_file = Input(_file)
      remux_job.insert(len(remux_job), input_file)

    # Add video codec object with 'copy' as the codec specified so it just muxes the streams
    remux_job.insert(len(remux_job), VideoCodec('copy'))

    # Add audio codec object with 'copy' as the codec specified so it just muxes the streams
    remux_job.insert(len(remux_job), AudioCodec('copy'))

    # Add Output() object to specify the output path and container
    remux_job.insert(len(remux_job), output_file)

    # Begin remux job and iterate over the piped stdout from the command logging it to debug
    with remux_job as self._process:
      while not self.abort and self._process.running:
        for line in self._process.readlines():
          if mediamanager.VERBOSE:
            logger.log(line, logger.DEBUG)
      if self._process.failed:
        return False
      elif self._process.successful:
        return True
      else:
        return False

  def finalize(self):

    # Create some variables to contain all the paths and basenames
    self._pending_file_tempbasename = self._outfile_base + '.' + 'copytemp'
    self._pending_file_temppath = os.path.join(os.path.dirname(self._file.path), self._pending_file_tempbasename)
    self._pending_file_basename = self._outfile_base + '.' + mediamanager.TRANSCODER_PENDING_EXTENSION
    self._pending_file_path = os.path.join(os.path.dirname(self._file.path), self._pending_file_basename)

    # First copy file to final destination directory with a temporary name
    try:
      shutil.copyfile(self._muxed_file_path, self._pending_file_temppath)
    except IOError, e:
      logger.log("finalize() :: Exception raised during copy to temp location, not writable; %s" % self._file.path, logger.DEBUG)
      return False
    except Exception, e:
      logger.log("finalize() :: Exception raised during copy to temp location, unknown; %s" % self._file.path, logger.DEBUG)
      logger.log("finalize() :: Exception :: %s" % e, logger.DEBUG)
      try:
        if os.path.isfile(self._pending_file_temppath):
          os.remove(self._pending_file_temppath)
      except Exception, e:
        logger.log("finalize() :: Exception raised cleaing up partially copied file; %s" % self._file.path, logger.DEBUG)
      return False

    # Second do a move operation from temp basename to final basename
    try:
      shutil.move(self._pending_file_temppath, self._pending_file_path)
    except Exception, e:
      logger.log("finalize() :: Exception raised during move to final location, unknown; %s" % self._file.path, logger.DEBUG)
      logger.log("finalize() :: Exception :: %s" % e, logger.DEBUG)
      try:
        if os.path.isfile(self._pending_file_temppath):
          os.remove(self._pending_file_temppath)
      except Exception, e:
        logger.log("finalize() :: Exception raised cleaing up partially copied file; %s" % self._file.path, logger.DEBUG)
      try:
        if os.path.isfile(self._pending_file_path):
          os.remove(self._pending_file_path)
      except Exception, e:
        logger.log("finalize() :: Exception raised cleaing up partially moved file; %s" % self._file.path, logger.DEBUG)
      return False

    return True

  def finish(self):

    # Lock the finish operation so only one thread can cleanup at a time
    with self.__FINISH_LOCK__:

      # If another thread cleaned up while waiting for the lock than just return
      if self.__FINISHED__:
        return

      # Save the current self.abort value so we can late determine if finish() was called because of an abort
      wasaborted = self.abort

      logger.log("TranscodeJob :: Finish has been called", logger.DEBUG)
      try:
        self.abort = True

        # Check if self.process exists and running
        if self._process is not None and self._process.poll() is None:
          # Kill the popen process
          self._process.terminate()
          # Release the reference to the process
          self._process = None
      except Exception, e:
        logger.log("TranscodeJob :: Exception caught in finish(); %s" % e, logger.DEBUG)

      # Delete all contents from tempdir since we are either done or aborted
      filelist = os.listdir(mediamanager.TRANSCODER_TEMPDIR)
      for f in filelist:
        os.remove(os.path.join(mediamanager.TRANSCODER_TEMPDIR ,f))

      # If finish() was called and being aborted during operation than check if a pending file was created and delete it
      outfile_basename = self._outfile_base + '.' + mediamanager.TRANSCODER_PENDING_EXTENSION
      if wasaborted and os.path.isfile(os.path.join(os.path.dirname(self._file.path), outfile_basename)):
        os.remove(os.path.join(os.path.dirname(self._file.path), outfile_basename))

      self.__FINISHED__ = True

class VerificationAcceptJob(TranscodeJob):

  def __init__(self, fileInfo):
    self._file = fileInfo

  def run(self):
    logger.log(u'VerificationAcceptJob :: Job run for file %s' % self.name)

class VerificationJob(TranscodeJob):

  def __init__(self, fileInfo):
    self._file = fileInfo

  def run(self):
    logger.log(u'VerificationDeclineJob :: Job run for file %s' % self.name)

class Factory():
  @classmethod
  def TranscodeJobFactory(cls, fileInfo, audio_stream_id=None, video_stream_id=None, subtitle_stream_id=None):
    if not isinstance(fileInfo, Files.VideoInfo):
      return None
    elif mediamanager.media.is_compliant(fileInfo):
      return None
    else:
      return TranscodeJob(fileInfo)

  @classmethod
  def VerificationAcceptJob(cls, fileInfo):
    if not isinstance(fileInfo, Files.VideoInfo):
      return None
    else:
      return VerificationAcceptJob(fileInfo)

  @classmethod
  def VerificationDeclineJob(cls, fileInfo):
    if not isinstance(fileInfo, Files.VideoInfo):
      return None
    else:
      return VerificationDeclineJob(fileInfo)
