import datetime

import mediamanager
from mediamanager import queue_generic
from mediamanager import logger

class QueuePriorities:
    LOW = 10
    NORMAL = 20
    HIGH = 30


class QueueTranscode(queue_generic.GenericQueue):
  def add_item(self, item):
    if not self.is_in_queue(item):
      with self.queue_lock:
        item.added = datetime.datetime.now()
        self.queues[item.priority].append(item)
      return True
    else:
      logger.log(u"Not adding item, it's already in the queue", logger.DEBUG)
      return False

  def is_in_queue(self, item):
    with self.queue_lock:
      for x in self.queues[item.priority]:
        if item.name == x.name:
          return True
    return False

class QueueItemTranscode(queue_generic.QueueItem):
  def __init__(self, transcodeJob, priority=QueuePriorities.NORMAL):
    self.job = transcodeJob

    self.name = self.job.name

    self.inProgress = False

    self.priority = priority

    self.thread_name = self.job.basename.replace(" ","-").upper()

    self.added = None

    self.amActive = False

  def execute(self):
    self.amActive = True

    try:
      self.job.run()
    except Exception, e:
      logger.log(u"QueueTranscode :: Exception caught running job; %s" % e, logger.DEBUG)

    self.finish()

  def finish(self):
    self.amActive = False
