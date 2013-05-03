#/usr/bin/env q-python27
# -*- coding: utf-8 -*-

import os
import sys
import thread
import atexit
import signal
import Queue
import multiprocessing
import qcomlib.logger.logger
from time import sleep
from qcomlib.daemon.daemon import Daemon
from qcomlib.daemon.dynamicdaemon import CmdWrapper
from qcomlib.daemon.dynamicdaemon import DynamicDaemon

log = qcomlib.logger.logger.Logger()

#class MyDaemon(Daemon):

    #sigStop     = False

    #def sigFun(self, signum, frame):
        ## 进程被SIGTERM杀死时，daemon会被通知，用户通知程序立即停止所有逻辑
        #self.sigStop    = True

    #def cleanFun(self):
        #print '程序退出时，做的清理工作'

    #def run(self):
        #self._cnt = 0
        ## 当程序接收到SIGTERM信号时，结束程序流程
        #while not self.sigStop:
            #self._cnt = self._cnt + 1
            #print str(self._cnt)
            #sleep(1)

#my_daemon = MyDaemon('mydaemon', '/home/dongliang.ma/code/q-daemon/info.pid', True)
#my_daemon.execute(sys.argv)
#help(Daemon)


def taskWorkerWrapper(script_path):
    os.execlp(script_path, script_path)

class MyDynamicDaemon(DynamicDaemon):
    script_path     = os.getcwd() + '/scripts/'
    tasklist        = {}
    sigStop         = False

    def sigFun(self, signum, frame):
        # 进程被SIGTERM杀死时，daemon会被通知，用户通知程序立即停止所有逻辑
        self.sigStop    = True

    def cleanFun(self):
        sys.stdout.write('程序退出时，做的清理工作\n')
        self._stopScripts()

    def run(self):
        while True:
            try:
                if self.sigStop:
                    break
                self._updateTasks()
                _cmd = self.cmd_queue.get(block = True, timeout = 1)
                sys.stdout.write('执行用户命令: %s %s\n' % (_cmd.cmd, _cmd.params))
                if _cmd.cmd == "RUN":
                    self._runTask(_cmd)
                elif _cmd.cmd == "KILL":
                    self._killTask(_cmd)
                elif _cmd.cmd == "RESTART":
                    self._restartTask(_cmd)
                else:
                    sys.stderr.write('未知命令: %s %s\n' % (_cmd.cmd, _cmd.params))
            except Queue.Empty:
                pass
            except Exception, _ex:
                sys.stderr.write(str(_ex) + '\n')

    def _updateTasks(self):
        _done_task_list = []
        for _task_name, _task_process in self.tasklist.items():
            try:
                if not _task_process.is_alive():
                    _done_task_list.append(_task_name)
            except Exception, _ex:
                sys.stderr.write('更新任务列表错误：' + str(_ex) + '\n')

        for _task_name in _done_task_list:
            try:
                del self.tasklist[_task_name]
                sys.stdout.write('Task %s done\n' % _task_name)
            except Exception, _ex:
                sys.stderr.write('更新任务列表错误：' + str(_ex) + '\n')

    def _stopScripts(self):
        for _task_name, _task_process in self.tasklist.items():
            try:
                _task_process.terminate()
            except Exception:
                pass

    def _runTask(self, cmd):
        if len(cmd.params) != 1:
            return
        _script_name    = cmd.params[0]
        _script_path    = self.script_path + cmd.params[0]
        if not self.tasklist.has_key(_script_name):
            _task_process = multiprocessing.Process(
                target = taskWorkerWrapper,
                args = (_script_path, ))
            self.tasklist[_script_name]     = _task_process
            _task_process.start()
            sys.stdout.write('Task add %s done \n' % _script_name)

    def _killTask(self, cmd):
        try:
            if len(cmd.params) != 1:
                return
            _script_name    = cmd.params[0]
            sys.stdout.write('Kill task %s \n' % _script_name)
            if self.tasklist.has_key(_script_name):
                _task_process   = self.tasklist.get(_script_name)
                del self.tasklist[_script_name]
                _task_process.terminate()
                sys.stdout.write('Kill task %s done \n' % _script_name)
        except Exception:
            pass

    def _restartTask(self, cmd):
        if len(cmd.params) != 1:
            return
        self._killTask(CmdWrapper("RESTART", cmd.params))
        self._runTask(CmdWrapper("RESTART", cmd.params))
        sys.stdout.write('Task restart %s done\n' % cmd.params[0] )

my_dynamic_daemon = MyDynamicDaemon('mydynamicdaemon', '/home/dongliang.ma/code/q-daemon/mydynamicdaemon.pid', True)
my_dynamic_daemon.execute(sys.argv)

