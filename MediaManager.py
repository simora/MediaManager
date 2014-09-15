import sys

import mediamanager
from mediamanager import cli

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
  cli.main()

  return


if __name__ == "__main__":
  main()
