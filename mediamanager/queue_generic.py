import datetime
import threading

from mediamanager import logger

class QueuePriorities:
    LOW = 10
    NORMAL = 20
    HIGH = 30

class GenericQueue(object):

  def __init__(self):

    self.currentItem = None

    self.queue_lock = threading.Lock()
    self.queues = {}
    self.queues[QueuePriorities.LOW] = []
    self.queues[QueuePriorities.NORMAL] = []
    self.queues[QueuePriorities.HIGH] = []

    self.thread = None

    self.queue_name = "QUEUE"

    self.min_priority = 0

    self.currentItem = None

  def pause(self):
    logger.log(u"Pausing queue")
    self.min_priority = 999999999999

  def unpause(self):
    logger.log(u"Unpausing queue")
    self.min_priority = 0

  def add_item(self, item):
    with self.queue_lock:
      item.added = datetime.datetime.now()
      self.queues[item.priority].append(item)
      return item

  def pop_queueitem(self, priority=None):
    def popit(priority):
      retval = self.queues[priority][0]
      del self.queues[priority][0]
      return retval
    with self.queue_lock:
      if priority == None:
        if len(self.queues[QueuePriorities.HIGH]) > 0:
          return popit(QueuePriorities.HIGH)
        elif len(self.queues[QueuePriorities.NORMAL]) > 0:
          return popit(QueuePriorities.NORMAL)
        elif len(self.queues[QueuePriorities.LOW]) > 0:
          return popit(QueuePriorities.LOW)
      elif priority == QueuePriorities.HIGH or priority == QueuePriorities.NORMAL or priority == QueuePriorities.LOW:
        if len(self.queues[priority]) > 0:
          return popit(priority)

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

        # launch the queue item in a thread
        # TODO: improve thread name
        threadName = self.queue_name + '-' + queueItem.get_thread_name()
        self.thread = threading.Thread(None, queueItem.execute, threadName)
        self.thread.start()

        self.currentItem = queueItem

  def stop(self):
    logger.log("%s :: Stop has been called" % self.queue_name, logger.DEBUG)
    try:
      if self.thread.isAlive():
        self.currentItem.finish()
        logger.log("%s :: Waiting for queue thread to stop" % self.queue_name, logger.DEBUG)
        self.thread.join(10)
        self.thread = None
      else:
        logger.log("%s :: Thread is not running" % self.queue_name, logger.DEBUG)
    except Exception, e:
      logger.log("%s :: Exception was caught; %s" % (self.queue_name, e), logger.DEBUG)

class QueueItem:
    def __init__(self, name, action_id = 0):
        self.name = name

        self.inProgress = False

        self.priority = QueuePriorities.NORMAL

        self.thread_name = None

        self.action_id = action_id

        self.added = None

    def get_thread_name(self):
        if self.thread_name:
            return self.thread_name
        else:
            return self.name.replace(" ","-").upper()

    def execute(self):
        """Implementing classes should call this"""

        self.inProgress = True

    def finish(self):
        """Implementing Classes should call this"""

        self.inProgress = False
