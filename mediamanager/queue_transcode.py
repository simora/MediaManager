import datetime
import threading

import mediamanager
from mediamanager import queue_generic
from mediamanager import logger
from mediamanager import media

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
      if mediamanager.VERBOSE:
        logger.log(u"Not adding item, it's already in the queue", logger.DEBUG)
      return False

  def is_in_queue(self, item):
    with self.queue_lock:
      for x in self.queues[item.priority]:
        if item.name == x.name:
          return True
    return False

  def run(self):

    # only start a new task if one isn't already going
    if self.thread == None or self.thread.isAlive() == False:

      # if the thread is dead then the current item should be finished
      if self.currentItem != None:
        self.currentItem.finish()
        self.currentItem = None

      # if there's something in the queue then run it in a thread and take it out of the queue
      if len(self.queues[QueuePriorities.HIGH]) > 0 or len(self.queues[QueuePriorities.NORMAL]) > 0 or len(self.queues[QueuePriorities.LOW]) > 0:

        # sort by priority
        queueItem = self.pop_queueitem()

        if queueItem.priority == QueuePriorities.NORMAL and media.is_pending(queueItem.job._file):
          logger.log("Queue_Transcode :: Item is already pending verification. Will remove from queue and continue; %s" % queueItem.name, logger.DEBUG)
          queueItem = None
        elif queueItem.priority == QueuePriorities.HIGH and not media.is_pending(queueItem.job._file):
          logger.log("Queue_Transcode :: Item is no longer pending verification. Will remove from queue and continue; %s" % queueItem.name, logger.DEBUG)
          queueItem = None
        else:

          # launch the queue item in a thread
          # TODO: improve thread name
          threadName = self.queue_name + '-' + queueItem.get_thread_name()
          self.thread = threading.Thread(None, queueItem.execute, threadName)
          self.thread.start()

          self.currentItem = queueItem

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
    logger.log(u"QueueTranscode :: Finish has been called; %s" % self.thread_name, logger.DEBUG)
    self.job.finish()
    self.amActive = False
