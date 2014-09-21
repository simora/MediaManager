import datetime
import time
import threading
import traceback

from mediamanager import logger

class Scheduler:

    def __init__(self, action, cycleTime=datetime.timedelta(minutes=10), run_delay=datetime.timedelta(minutes=0), start_time=None, threadName="ScheduledThread", silent=False):

        self.lastRun = datetime.datetime.now() + run_delay - cycleTime

        self.action = action
        self.cycleTime = cycleTime
        self.start_time = start_time

        self.thread = None
        self.threadName = threadName
        self.silent = silent

        self.initThread()

        self.abort = False

    def initThread(self):
        if self.thread == None or not self.thread.isAlive():
            self.thread = threading.Thread(None, self.runAction, self.threadName)

    def timeLeft(self):
        return self.cycleTime - (datetime.datetime.now() - self.lastRun)

    def forceRun(self):
        if not self.action.amActive:
            self.lastRun = datetime.datetime.fromordinal(1)
            return True
        return False

    def runAction(self):

        while True:

            current_time = datetime.datetime.now()
            should_run = False

            # check if interval has passed
            if current_time - self.lastRun >= self.cycleTime:
                # check if wanting to start around certain time taking interval into account
                if self.start_time:
                    hour_diff = current_time.time().hour - self.start_time.hour
                    if hour_diff >= 0 and hour_diff < self.cycleTime.seconds / 3600:
                        should_run = True
                    else:
                        # set lastRun to only check start_time after another cycleTime
                        self.lastRun = current_time
                else:
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

            if self.abort:
                self.abort = False
                self.thread = None
                return

            time.sleep(1)
