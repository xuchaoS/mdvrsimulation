#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'shangxc'

from Tkinter import *

REGNO = r'.*'

class ShangxcGUI(object):
    def __init__(self):
        self._tmp = ''
        self.root = Tk()
        self.runtimebutton = []

    def userbutton(self, name, tips, father, command, state='DISABLED'):
        exec "self.%s = Button(%s, text='%s', command=%s, state=%s, bd=3)" % (name, father, tips, command, state)
        exec "self.%s.pack(side=LEFT)" % (name)
        exec '''if %s == DISABLED:
            self.runtimebutton.append(self.%s)''' % (state, name)

    def inputbox(self, name, tips, father, limit, checkrule, defaultvalue, state='NORMAL'):
        exec "Label(%s, text=' %s:').pack(side=LEFT)" % (father, tips)
        exec "self.%s = Entry(%s, bg='white', justify=CENTER, width=%d)" % (name, father, limit+5)
        exec "self._bind(self.%s, %s, '%s')" % (name, limit, checkrule)
        exec "self.%s.insert(0, '%s')" % (name, defaultvalue)
        exec "self.%s.pack(side=LEFT)" % (name)
        exec "self.%s.config(state=%s)" % (name, state)

    def lenlimit(self, limit, checkrule=REGNO, ev=None):
        widget = ev.widget
        str = widget.get()
        if len(str) > limit:
            widget.delete(0, END)
            widget.insert(0, self._tmp)
        self.check(checkrule,ev)

    def check(self, checkrule, ev=None):
        widget = ev.widget
        str = widget.get()
        if re.match(checkrule, str) == None:
            widget.config(bg='red', fg='white')
        else:
            widget.config(bg='white', fg='black')

    def _bind(self, obj, limit, checkrule):
        obj.bind('<KeyPress>', lambda ev=None: self.record(limit, ev))
        obj.bind('<KeyRelease>', lambda ev=None: self.lenlimit(limit, checkrule, ev))

    def _exchange(self):
        tmp = (float(self.gps1before.get()), float(self.gps2before.get()))
        for i, j in zip((self.gps1after, self.gps2after),(0,1)):
            i.config(state=NORMAL)
            i.delete(1.0, END)
            i.insert(1.0, '%.4f' % (int(tmp[j])*100+(tmp[j]-int(tmp[j]))*60))
            i.config(state=DISABLED)
