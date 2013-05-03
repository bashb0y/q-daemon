# -*- coding: utf-8 -*-

import Queue
import sys
import socket
import select
import threading
import daemon
import time

_COMMAND_COMMUCATION_ADDR = ('localhost', 13412)
_HELP_MSG_TEMPLATE = "Usage: %s [start | stop | restart | rmpidfile] | [command params] \n"


class _CommandReceiver(threading.Thread):
    """
        DynamicDaemon中监听用户指令的线程
    """
    sig_stop    = False
    sock        = None

    def __init__(self, daemon):
        """ daemon是DynamicDaemon的实例，本类需要访问其内部状态 """
        super(self.__class__, self).__init__()
        self.daemon     = daemon

    def _initSockets(self):
        """ 初始化非阻塞套接字 """
        self.sig_stop       = False
        self.sock           = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind(_COMMAND_COMMUCATION_ADDR)
        self.sock.listen(10)

    def _polling(self):
        """ 使用非阻塞IO接收用户的命令 """
        (_infds, _outfds, _errfds) = select.select([self.sock], [], [], 1)
        if _infds is not None:
            for s in _infds:
                if s is self.sock:
                    if self.sig_stop:
                        return
                    else:
                        self._receiveData()

    def _receiveData(self):
        """ 获取用户命令  """
        _conn, _addr = self.sock.accept()
        try:
            _conn.settimeout(1)
            _buf = _conn.recv(1024)
            if _buf is not None:
                _args = _buf.split(' ')
                if _args[0] == "stop":
                    self.stop()
                self.daemon.cmd_queue.put(CmdWrapper(_args[0], _args[1:]), False)
                _conn.close()
        except Exception, _ex:
            print >> sys.stderr, str(_ex)

    def run(self):
        """ 监听用户命令  """
        self._initSockets()

        while not self.sig_stop:
            self._polling()

        self.sock.close()

    def stop(self):
        self.sig_stop   = True


class CmdWrapper:
    """
        用户命令的封装
        cmd为命令名称
        params为参数列表
    """
    cmd     = None
    params  = []

    def __init__(self, cmd, params):
        self.cmd        = cmd
        self.params     = params


class DynamicDaemon(daemon.Daemon):
    """
        可以从外部动态接收用户指令的daemon实现。
    """
    cmd_queue       = None
    cmd_receiver    = None

    def run(self):
        raise NotImplementedError

    def addTask(self, args):
        try:
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _sock.connect(_COMMAND_COMMUCATION_ADDR)
            _args = ""
            for arg in args:
                _args = _args + " " + arg
            _sock.send(_args.strip())
        except Exception, _ex:
            print >> sys.stderr, str(_ex)

    def execute(self, argv):
        """ 启动daemon，不可override """
        if len(argv) < 2:
            self._usage()

        action  = argv[1]
        if len(argv) == 2:
            if action == "start":
                self._startAll()
            elif action == "stop":
                self._stop()
            elif action == "restart":
                self._restartAll(argv)
            elif action == "rmpidfile":
                self._rmpidfile()
            else:
                self._usage()
        else:
            self.addTask(argv[1:])

    def _startAll(self):
        self._start()
        self.cmd_queue      = Queue.Queue()
        self.cmd_receiver   = _CommandReceiver(self)
        self.cmd_receiver.start()
        self.run()

    def _restartAll(self, argv):
        self._restart()
        self.cmd_queue      = Queue.Queue()
        self.cmd_receiver   = _CommandReceiver(self)
        self.cmd_receiver.start()
        self.run()

    def _usage(self):
        sys.stderr.write(_HELP_MSG_TEMPLATE % self.appname)
        sys.exit(0)

