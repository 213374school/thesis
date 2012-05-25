#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

helptxt = """usage:\n./batch_object_detection.py folder [mode=faces,body,profile]"""

def main():
    os.system('clear')
    try:
        path = sys.argv[1]
    except:
        print helptxt
    else:
        try:
            mode = sys.argv[2]
        except:
            mode = 'faces'
        files = [filename for filename in os.listdir(path) if filename.split('.')[-1] in ['m4v','avi']]
        for f in files:
            command = './object_detection.py "./%s/%s %s"' % (path, f, mode)
            os.system(command)

if __name__ == "__main__":
     main()
