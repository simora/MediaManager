import datetime
import time

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

      self.action.sort_queue()

      # check if interval has passed
      if len(media.PENDING.keys()) <= mediamanager.SCHEDULER_TRANSCODE_LIMIT or self.action.queue[0].priority == queue_generic.QueuePriorities.HIGH:
        should_run = True
      if should_run:
        self.lastRun = current_time
        try:
          if not self.silent:
            logger.log(u"Starting new thread: " + self.threadName, logger.DEBUG)
            self.action.run()
        except Exception, e:
          logger.log(u"Exception generated in thread " + self.threadName, logger.ERROR)
          logger.log(repr(traceback.format_exc()), logger.DEBUG)

      if self.abort:
        self.abort = False
        self.thread = None
        return

      time.sleep(1)
