import simplejson, os, curses
from threading import Lock

import mediamanager

import utils.files as Files
import mediamanager.media as Media
from mediamanager.media import Scan
from mediamanager import logger

__INITIALIZED__ = False
INIT_LOCK = Lock()

CURSES = True
MYSCREEN = None
MYSCREEN_HIGHLIGHTED = None
MYSCREEN_NORMAL = None
MENU = 'menu'
COMMAND = 'command'
PRINT = 'print'
FORM = 'form'
EXITMENU = 'exitmenu'
MENUS = None
COMMANDS = None

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def main():

  initialize()

  mediamanager.initialize()
  mediamanager.start()

  while True:
    if CURSES:
      processmenu(MENUS)
      curses.endwin()
      os.system('clear')
      break

  mediamanager.shutdown()

def runmenu(menu, parent):

  global MYSCREEN

  if parent is None:
    lastoption = "Exit"
  else:
    lastoption = "Return to %s menu" % parent['title']

  optioncount = len(menu['options'])

  pos = 0
  oldpos = None
  x = None

  while x != ord('\n'):
    if pos != oldpos:
      oldpos = pos
      MYSCREEN.border(0)
      MYSCREEN.addstr(2, 2, menu['title'], curses.A_STANDOUT)
      MYSCREEN.addstr(4, 2, menu['subtitle'], curses.A_BOLD)

      for index in range(optioncount):
        textstyle = MYSCREEN_NORMAL
        if pos == index:
          textstyle = MYSCREEN_HIGHLIGHTED
        MYSCREEN.addstr(5+index, 4, "%d - %s" % (index+1, menu['options'][index]['title']), textstyle)

      textstyle = MYSCREEN_NORMAL
      if pos == optioncount:
        textstyle = MYSCREEN_HIGHLIGHTED
      MYSCREEN.addstr(5+optioncount, 4, "%d - %s" % (optioncount+1, lastoption), textstyle)
      MYSCREEN.refresh()

    x = MYSCREEN.getch()

    if x >= ord('1') and x <= ord(str(optioncount+1)):
      pos = x - ord('0') - 1
    elif x == 258:
      if pos < optioncount:
        pos += 1
      else:
        pos = 0
    elif x == 259:
      if pos > 0:
        pos += -1
      else:
        pos = optioncount

  return pos

def processmenu(menu, parent=None):
  optioncount = len(menu['options'])
  exitmenu = False
  while not exitmenu:
    getin = runmenu(menu, parent)
    if getin == optioncount:
      exitmenu = True
    elif menu['options'][getin]['type'] == COMMAND:
      val = COMMANDS[menu['options'][getin]['command']].run()
      newmenu = { 'title': menu['options'][getin]['title'], 'type': MENU, 'subtitle': "Select any item to continue...", 'options': [] }
      for item in val:
        newmenu['options'].append(item)
      MYSCREEN.clear()
      processmenu(newmenu, menu)
      MYSCREEN.clear()
    elif menu['options'][getin]['type'] == PRINT:
      exitmenu = True
    elif menu['options'][getin]['type'] == MENU:
      MYSCREEN.clear()
      processmenu(menu['options'][getin], menu)
      MYSCREEN.clear()
    elif menu['options'][getin]['type'] == EXITMENU:
      exitmenu = True



def initialize():
  with INIT_LOCK:

    global __INITIALIZED__, MYSCREEN, MYSCREEN_HIGHLIGHTED, MYSCREEN_NORMAL, MENUS, COMMANDS

    if __INITIALIZED__:
      return False

    MYSCREEN = curses.initscr()

    curses.noecho()
    curses.cbreak()
    curses.start_color()
    MYSCREEN.keypad(1)

    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    MYSCREEN_HIGHLIGHTED = curses.color_pair(1)
    MYSCREEN_NORMAL = curses.A_NORMAL

    MENUS = {
      'title': "Main Menu", 'type': MENU, 'subtitle': "Select an option...", 'options': [
        { 'title': "Status", 'type': MENU, 'subtitle': "Select an option..", 'options': [
          { 'title': "Media Information", 'type': COMMAND, 'command': 'printMediaInfo' },
          { 'title': "Thread Information", 'type': COMMAND, 'command': 'printThreadInfo' }
          ]
        }
      ]
    }

    COMMANDS = {
      'printMediaInfo': _printMediaInfo(),
      'printThreadInfo': _printThreadInfo()
    }

class _printMediaInfo():
  def __init__(self):
    self.Type = PRINT

  def run(self):
    menu = []
    menu.append('Media Count : %s' % len(Media.MEDIA))
    menu.append('Pending Count : %s' % len(Media.PENDING))
    menu.append('Non-Compliant Count : %s' % len(Media.NONCOMPLIANT))

    return _formatMenuPrint(menu)

class _printThreadInfo():
  def __init__(self):
    self.Type = PRINT

  def run(self):
    menu = []
    if mediamanager.schedulerScanner.action.amActive:
      menu.append('Scanner : Active')
    else:
      menu.append('Scanner : Idle')

    if mediamanager.schedulerTranscode.action.thread == None or mediamanager.schedulerTranscode.action.thread.isAlive() == False:
      menu.append('Transcoder : Idle')
    else:
      menu.append('Transcoder : Active')

    return _formatMenuPrint(menu)

def _formatMenuPrint(listMenus):
  retval = []

  for item in listMenus:
    retval.append({ 'title': item, 'type': PRINT })

  return retval
