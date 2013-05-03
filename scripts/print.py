#!/usr/bin/env q-python27
# -*- coding: utf-8 -*-

import time

def Print():
    for i in range(5):
        print '[Print] %d ' % i
        time.sleep(1)

if __name__ == '__main__':
    Print()
