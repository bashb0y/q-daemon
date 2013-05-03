# -*- encoding: utf-8 -*-

import qcomlib.singleton.singleton

class Logger(qcomlib.singleton.singleton.Singleton):
    """ 去哪儿网公共日志库  """

    def fatal(self, *args):
        for var in args:
            print var

    def error(self, *args):
        for var in args:
            print var

    def warn(self, *args):
        for var in args:
            print var

    def info(self, *args):
        for var in args:
            print var

    def debug(self, *args):
        for var in args:
            print var

    def trace(self, *args):
        for var in args:
            print var

