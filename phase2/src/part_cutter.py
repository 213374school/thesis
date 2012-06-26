#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import json
from time import clock
import os
import json
import video
import cv2
import cv
from common import draw_str

help_message = """USAGE: %s <video_source_folder> <frames to remove>""" % __file__

def main():
	import sys
	
	try:
		video_src_folder = sys.argv[1]
		frames_to_remove = int(sys.argv[2])
	except:
		print help_message
		return

	out_path = '%sout/' % video_src_folder
	if not os.path.exists(out_path):
		os.system('mkdir %s' % out_path)

	video_srcs = ['%s%s' % (video_src_folder, filename) for filename in os.listdir(video_src_folder) if filename.split('.')[-1] in ['m4v','avi'] and 'part' in filename]
	print video_srcs

	for video_src in video_srcs:
		capture = cv.CaptureFromFile(video_src)
		cam = video.create_capture(video_src)

		frame_count = 0
		while True:
			ret, frame = cam.read()
			if ret:
				frame_count += 1
			else:
				break
		frame_count -= frames_to_remove

		filename = video_src.split('/')[-1].split('.')[0]
		out = "%s%s.avi" % (out_path, filename)
		# print out

		fps = 24
		fourcc = cv.CV_FOURCC('D','I','V','3') # MPEG-4.3
		width = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
		height =  int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
		frame_size = (int(width), int(height))		

		writer = cv.CreateVideoWriter(out, fourcc, fps, frame_size, 1)
		while frame_count > 0:
			frame_count -= 1
			try:
				frame = cv.QueryFrame(capture)
				cv.WriteFrame(writer, frame)
			except Exception as e:
				pass

if __name__ == '__main__':
	main()