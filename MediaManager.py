import sys
import time
import os

import mediamanager
from mediamanager import ui

if sys.version_info < (2,5):
  sys.exit("Sorry, requires Python 2.5, 2.6 or 2.7.")

try:
  import bs4
except ValueError:
  sys.exit("Sorry, requires BeautifulSoup 4.")
except:
  sys.exit("The Python module BeautifulSoup4 is required")

try:
  import av
except ValueError:
  sys.exit("Sorry, requires PyAV.")
except:
  sys.exit("The Python module PyAV is required")

def main():

  mediamanager.initialize()
  mediamanager.start()

  cli = ui.CLI()

  while cli.thread.isAlive():
    time.sleep(10)

  cli.finish()
  cli = None
  mediamanager.shutdown()

  os.exit(0)


if __name__ == "__main__":
  main()
