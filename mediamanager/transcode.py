import os, re
import av

import mediamanager
from mediamanager import logger

import utils.files as Files

class TranscodeJob():
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

  def run(self):
    basename_noext = re.match('^(.*)\..*$', self._file.basename).group(1)
    outfile_basename = basename_noext + '.' + mediamanager.TRANSCODER_PENDING_EXTENSION
    outfile_path = os.path.join(os.path.dirname(self._file.path), outfile_basename)
    if mediamanager.COMPLIANCE['Media']['Container']['Codec'] == 'Matroska':
      tempfile_ext = 'mkv'
    else:
      tempfile_ext = 'mp4'
    tempfile_basename = basename_noext + '.' + tempfile_ext
    if re.match('^(~).*$', mediamanager.TRANSCODER_TEMPDIR) is not None:
      fixed_path = re.match('^~\/(.*)$', mediamanager.TRANSCODER_TEMPDIR).group(1)
      tempfile_path = os.path.join(os.path.expanduser("~"), fixed_path, tempfile_basename)
    else:
      tempfile_path = os.path.join(mediamanager.TRANSCODER_TEMPDIR, tempfile_basename)

    output_audio_codec = None

    logger.log(u"TranscodeJob :: Opening input file; %s" % self._file.path, logger.DEBUG)
    av_input_file = av.open(self._file.path)
    logger.log(u"TranscodeJob :: Opening output file; %s" % tempfile_path, logger.DEBUG)
    av_output_file = av.open(tempfile_path, 'w')
    av_output_file_streams = {}

    # Need to write something to only handle audio_stream_id, video_stream_id, subtitle_stream_id if not None
    for i, stream in enumerate(av_input_file.streams):
      if (stream.type == b'video'):
        av_output_file_streams[stream] = av_output_file.add_stream(template=stream)
      elif (stream.type == b'audio'):
        av_output_file_streams[stream] = av_output_file.add_stream(template=stream)
      elif (stream.type == b'subtitle'):
        av_output_file_streams[stream] = av_output_file.add_stream(template=stream)
      elif (stream.type == b'data'):
        av_output_file_streams[stream] = av_output_file.add_stream(template=stream)

    for i, in_packet in enumerate(av_input_file.demux(av_output_file_streams.keys())):
      if logger.LOG_EXTRA_DEBUG:
        logger.log(u"TranscodeJob :: %02d %r" % (i, in_packet), logger.DEBUG)
        logger.log(u"TranscodeJob :: \tin: %s" % in_packet.stream, logger.DEBUG)

      #if in_packet.stream.type == b'audio':
        #for frame in in_packet.decode():
        #  output_packet = av_output_file_streams[in_packet.stream].encode(frame)
        #
        #  if output_packet:
        #    logger.log(u"TranscodeJob :: \tout: %s" % output_packet.stream, logger.DEBUG)
        #    av_output_file.mux(output_packet)
      if in_packet.stream.type == b'audio' or in_packet.stream.type == b'video' or in_packet.stream.type == b'subtitle' or in_packet.stream.type == b'data':
        in_packet.dts = in_packet.dts or 0
        in_packet.stream = av_output_file_streams[in_packet.stream]
        if logger.LOG_EXTRA_DEBUG:
          logger.log(u"TranscodeJob :: \tout: %s" % in_packet.stream, logger.DEBUG)
        try:
          av_output_file.mux(in_packet)
        except Exception, e:
          logger.log(u"TranscodeJob :: av_output_file.mux() threw exception; %s" % e, logger.DEBUG)
          logger.log(u"TranscodeJob :: i = %s, in_packet = %s" % (i, in_packet), logger.DEBUG)

    #for stream in av_output_file_streams.values():
    #  if stream.type == b'audio':
    #    logger.log(u"TranscodeJob :: Flushing encoder for stream %s" % stream, logger.DEBUG)
    #
    #    while True:
    #      output_packet = stream.encode(None)
    #      if output_packet:
    #        if logger.LOG_EXTRA_DEBUG:
    #          logger.log(u"TranscodeJob :: <<< %s" % output_packet, logger.DEBUG)
    #        av_output_file.mux(output_packet)
    #      else:
    #        logger.log(u"TranscodeJob :: Done flushing encoder for stream %s" % stream, logger.DEBUG)
    #        break

    logger.log(u"TranscodeJob :: Closing file", logger.DEBUG)
    av_output_file.close()

    logger.log(u'TranscodeJob :: Job run for file %s' % self.name, logger.DEBUG)

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
