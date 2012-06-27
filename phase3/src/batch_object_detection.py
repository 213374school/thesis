#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import object_detection
object_detect = object_detection.object_detect

helptxt = """usage:\n%s video_src_folder""" % __file__

def main():
	os.system('clear')
	try:
		video_src_folder = sys.argv[1]
	except:
		print helptxt
	else:
		files = [filename for filename in os.listdir(video_src_folder) if filename.split('.')[-1] in ['m4v','avi']]
		for f in files:
			video_src = '%s%s' % (video_src_folder, f)
			for mode in ['faces', 'body', 'profile']:
				object_detect(video_src=video_src, mode=mode)
				
if __name__ == "__main__":
	 main()
