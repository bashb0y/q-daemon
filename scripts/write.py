#!/usr/bin/env q-python27
# -*- coding: utf-8 -*-

def Writer():
    try:
        file_object = open('/home/dongliang.ma/code/q-daemon/thefile.txt', 'w+')
        file_object.write(str(100))
        file_object.close()
    except Exception, e:
        print str(e)

if __name__ == '__main__':
    Writer()
