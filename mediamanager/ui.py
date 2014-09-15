import simplejson, os, curses
import threading

import mediamanager

import utils.files as Files
import mediamanager.media as Media
from mediamanager.media import Scan
from mediamanager import logger

class MENU_TYPES:
  MENU = 'menu'
  COMMAND = 'command'
  PRINT = 'print'
  FORM = 'form'
  EXITMENU = 'exitmenu'

class CLI():
  def __init__(self):
    self.myscreen = curses.initscr()
    self.thread = None
    self.threadName = 'CLI'

    curses.noecho()
    curses.cbreak()
    curses.start_color()
    self.myscreen.keypad(1)

    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    self.myscreen_highlighted = curses.color_pair(1)
    self.myscreen_normal = curses.A_NORMAL

    self.menus = {
      'title': "Main Menu", 'type': MENU_TYPES.MENU, 'subtitle': "Select an option...", 'options': [
        { 'title': "Status", 'type': MENU_TYPES.MENU, 'subtitle': "Select an option..", 'options': [
          { 'title': "Media Information", 'type': MENU_TYPES.COMMAND, 'command': 'printMediaInfo' },
          { 'title': "Thread Information", 'type': MENU_TYPES.COMMAND, 'command': 'printThreadInfo' }
          ]
        }
      ]
    }

    self.commands = {
      'printMediaInfo': _printMediaInfo(),
      'printThreadInfo': _printThreadInfo()
    }

    self.initThread()

  def initThread(self):
    if self.thread == None or not self.thread.isAlive():
      self.thread = threading.Thread(None, self.processmenu(self.menus), self.threadName)
  def finish(self):
    curses.endwin()

  def runmenu(self, menu, parent):
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
        self.myscreen.border(0)
        self.myscreen.addstr(2, 2, menu['title'], curses.A_STANDOUT)
        self.myscreen.addstr(4, 2, menu['subtitle'], curses.A_BOLD)

        for index in range(optioncount):
          textstyle = self.myscreen_normal
          if pos == index:
            textstyle = self.myscreen_highlighted
          self.myscreen.addstr(5+index, 4, "%d - %s" % (index+1, menu['options'][index]['title']), textstyle)

        textstyle = self.myscreen_normal
        if pos == optioncount:
          textstyle = self.myscreen_highlighted
        self.myscreen.addstr(5+optioncount, 4, "%d - %s" % (optioncount+1, lastoption), textstyle)
        self.myscreen.refresh()

      x = self.myscreen.getch()

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

  def processmenu(self, menu, parent=None):
    optioncount = len(menu['options'])
    exitmenu = False
    while not exitmenu:
      getin = self.runmenu(menu, parent)
      if getin == optioncount:
        exitmenu = True
      elif menu['options'][getin]['type'] == MENU_TYPES.COMMAND:
        val = self.commands[menu['options'][getin]['command']].run()
        newmenu = { 'title': menu['options'][getin]['title'], 'type': MENU_TYPES.MENU, 'subtitle': "Select any item to continue...", 'options': [] }
        for item in val:
          newmenu['options'].append(item)
        self.myscreen.clear()
        self.processmenu(newmenu, menu)
        self.myscreen.clear()
      elif menu['options'][getin]['type'] == MENU_TYPES.PRINT:
        exitmenu = True
      elif menu['options'][getin]['type'] == MENU_TYPES.MENU:
        self.myscreen.clear()
        self.processmenu(menu['options'][getin], menu)
        self.myscreen.clear()
      elif menu['options'][getin]['type'] == MENU_TYPES.EXITMENU:
        exitmenu = True

class _printMediaInfo():
  def __init__(self):
    self.Type = MENU_TYPES.PRINT

  def run(self):
    menu = []
    menu.append('Media Count : %s' % len(Media.MEDIA))
    menu.append('Pending Count : %s' % len(Media.PENDING))
    menu.append('Non-Compliant Count : %s' % len(Media.NONCOMPLIANT))

    return _formatMenuPrint(menu)

class _printThreadInfo():
  def __init__(self):
    self.Type = MENU_TYPES.PRINT

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
    retval.append({ 'title': item, 'type': MENU_TYPES.PRINT })

  return retval
