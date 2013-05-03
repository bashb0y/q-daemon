# -*- coding: utf-8 -*-

import sys
import os
import time
import atexit
import signal

import qcomlib.singleton.singleton

_HELP_MSG_TEMPLATE = "Usage: %s start | stop | restart | rmpidfile \n"

class Daemon(qcomlib.singleton.singleton.Singleton):
    """
    使用说明:
        from qcomlib.daemon.daemon import Daemon

        class MyDaemon(Daemon):

            sigStop     = False

            def sigFun(self, signum, frame):
                # 进程被SIGTERM杀死时，daemon会被通知，用户通知程序立即停止所有逻辑
                self.sigStop    = True

            def cleanFun(self):
                print '程序退出时，做的清理工作'

            def run(self):
                self._cnt = 0
                # 当程序接收到SIGTERM信号时，结束程序流程
                while not self.sigStop:
                    self._cnt = self._cnt + 1
                    print str(self._cnt)
                    sleep(1)

        my_daemon = MyDaemon('mydaemon', '/home/dongliang.ma/code/q-daemon/info.pid', True)
        my_daemon.execute(sys.argv)
    """

    def __init__(self, appname, pidfile, show_output = False):
        self.appname        = appname
        self.pidfile        = pidfile
        self.show_output    = show_output

    def run(self):
        """ Daemon回调函数
            需要用户根据自己的业务进行实现 """
        raise NotImplementedError

    def execute(self, argv):
        """
            控制daemon运行，不可override
            argv可以是[start | stop | restart | rmpidfile]
        """
        if len(argv) != 2:
            self._usage()

        action  = argv[1]
        if action == "start":
            self._start()
            self.run()
        elif action == "stop":
            self._stop()
        elif action == "restart":
            self._restart()
            self.run()
        elif action == "rmpidfile":
            self._rmpidfile()
        else:
            self._usage()

    def sigFun(self, signum, frame):
        """ 用户可以自己处理退出前要做的工作 """
        sys.exit(0)

    def cleanFun(self):
        """ 程序正常退出时，用户要做的清理工作 """
        pass

    def _usage(self):
        sys.stderr.write(_HELP_MSG_TEMPLATE % self.appname)
        sys.exit(0)

    def _start(self):
        """ 如果daemon已经运行，则退出；
            否则，创建新的daemon实例
        """
        _pid    = self._readPidFile()
        if _pid is not None:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        else:
            sys.stdout.write("Service starting .. [OK]\n")
            sys.stdout.flush()
            self._createDaemon()
            signal.signal(signal.SIGTERM, self.sigFun)

    def _stop(self):
        """
            如果daemon没有运行，则退出；
            否则，根据pid文件，杀死daemon
        """
        _pid    = self._readPidFile()
        if _pid is None:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        else:
            sys.stdout.write("Service stopping ")
            sys.stdout.flush()
            try:
                while True:
                    os.kill(_pid, signal.SIGTERM)
                    time.sleep(1)
                    sys.stdout.write(".")
                    sys.stdout.flush()
            except OSError, _err:
                err_msg = str(_err.args)
                if err_msg.find("No such process") > 0:
                    if os.path.exists(self.pidfile):
                        self._delPidFile()
                else:
                    sys.stderr.write(err_msg)
                    sys.exit(1)

    def _restart(self):
        """ 重启daemon """
        self._stop()
        self._start()

    def _rmpidfile(self):
        """ 删除因为daemon以外崩溃遗留的pid文件  """
        self._delPidFile()

    def _firstFork(self):
        try:
            _pid = os.fork()
            if _pid > 0:
                sys.exit(0)
        except OSError, _err:
            sys.stderr.write('fork #1 failed: %s\n' % str(_err))
            sys.exit(1)

        os.chdir('/')
        os.setsid()

    def _secondFork(self):
        try:
            _pid = os.fork()
            if _pid > 0:
                sys.exit(0)
        except OSError, _err:
            sys.stderr.write('fork #2 failed: %s\n' % str(_err))
            sys.exit(1)

    def _initOutput(self):
        """ 设置daemon是否回显  """
        if not self.show_output:
            sys.stdout.flush()
            sys.stderr.flush()
            _si = open(os.devnull, 'r')
            _so = open(os.devnull, 'a+')
            _se = open(os.devnull, 'a+')
            os.dup2(_si.fileno(), sys.stdin.fileno())
            os.dup2(_so.fileno(), sys.stdout.fileno())
            os.dup2(_se.fileno(), sys.stderr.fileno())

    def _readPidFile(self):
        try:
            _fp = open(self.pidfile, 'r')
            _pid = int(_fp.read().strip())
            _fp.close()
        except IOError:
            _pid = None
        return _pid

    def _writePidFile(self):
        try:
            _pid = str(os.getpid())
            _fp = open(self.pidfile, 'w+')
            _fp.write(_pid + '\n')
            _fp.close()
        except Exception, _ex:
            sys.stderr.write(str(_ex))

    def _delPidFile(self):
        try:
            os.remove(self.pidfile)
        except Exception, _ex:
            sys.stderr.write(str(_ex))

    def _createDaemon(self):
        """ 连续2次fork()，创建daemon  """
        self._firstFork()
        self._secondFork()
        self._initOutput()

        atexit.register(self._delPidFile)
        atexit.register(self.cleanFun)

        self._writePidFile()

