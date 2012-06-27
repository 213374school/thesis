#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

helptxt = """usage:\n%s folder """ % __file__

def main():
	# os.system('clear')
	try:
		path = sys.argv[1]
	except:
		print helptxt
	else:
		files = [filename for filename in os.listdir(path) if filename.split('.')[-1] in ['m4v','avi']]
		for f in files:
			command = './src/peopledetect.py ./%s/%s 0' % (path, f)
			# print command
			os.system(command)

if __name__ == "__main__":
	 main()
