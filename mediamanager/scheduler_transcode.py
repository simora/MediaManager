import datetime
import time
import traceback

import mediamanager
from mediamanager import logger
from mediamanager import scheduler
from mediamanager import media
from mediamanager import queue_generic

class SchedulerTranscode(scheduler.Scheduler):
  def runAction(self):
    while True:

      current_time = datetime.datetime.now()
      should_run = False

      # check if interval has passed
      if (len(self.action.queues[queue_generic.QueuePriorities.HIGH])) > 0:
        should_run = True
      elif (len(self.action.queues[queue_generic.QueuePriorities.NORMAL]) > 0 and len(media.PENDING.keys()) <= mediamanager.TRANSCODER_PENDING_LIMIT):
        should_run = True
      elif (len(self.action.queues[queue_generic.QueuePriorities.LOW]) > 0 and len(media.PENDING.keys()) <= mediamanager.TRANSCODER_PENDING_LIMIT):
        should_run = True
      if should_run:
        self.lastRun = current_time
        try:
          if logger.LOG_EXTRA_DEBUG:
            logger.log(u"Starting new thread: " + self.threadName, logger.DEBUG)
          self.action.run()
        except Exception, e:
          logger.log(u"Exception generated in thread " + self.threadName, logger.ERROR)
          logger.log(repr(traceback.format_exc()), logger.DEBUG)
          self.abort = True

      if self.abort:
        self.abort = False
        try:
          self.action.stop()
        except:
          pass
        finally:
          self.thread = None
        return

      time.sleep(1)
