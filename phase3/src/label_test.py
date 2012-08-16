#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import random
import numpy as np
from collections import *
import os
import pylab
import sys
from segment_db import SegmentDatabase
try:
	import cv
	import cv2
	from common import draw_str
except Exception as e:
	print e

def get_capture(filename):

	video_src = 'data/%s.m4v' % filename
	try:
		cap = cv2.VideoCapture(video_src)
	except:
		video_src = 'data/%s.avi' % filename
		cap = cv2.VideoCapture(video_src)
	return cap

def get_num_frames(cap):

	return cap.get(cv.CV_CAP_PROP_FRAME_COUNT)

def get_fps(cap):

	return cap.get(cv.CV_CAP_PROP_FPS)

def show_video(filename, start_frame, end_frame, label):

	cap = get_capture(filename)
	fps = get_fps(cap)
	assert(fps == 24)
	keyDown = False
	first_frame = True
	state = 'YES!'
	if cap.set(cv.CV_CAP_PROP_POS_FRAMES, start_frame):
		length = end_frame - start_frame
		for i in range(length):
			ret, frame = cap.read()
			if ret:
				# draw_str(frame, (20, 40), label)
				if first_frame:
					# show first frame and let user decide if it is good or bad
					draw_str(frame, (20, 20), '%s? %s' % (label, state))
					cv2.imshow('', frame)
					ch = cv2.waitKey(2000)
				else:
					ch = cv2.waitKey(int(1000/fps))		
				first_frame = False
				state = 'NO!' if keyDown else 'YES!'
				draw_str(frame, (20, 20), '%s? %s' % (label, state))
				cv2.imshow('', frame)
				# ch = cv2.waitKey(int(1000/fps))
				if ch != -1: # key pressed
					keyDown = True if not keyDown else False
			else:
				break
	else:
		raise Exception('unable to set position to %d' % start_frame)
	if state == 'NO!':
		return 0
	return 1

def main():
	segment_database = SegmentDatabase()
	# print segment_database.db
	label = 'has_police'
	segments = segment_database.get_with_label(label)
	tp = 0
	fp = 0
	for segment in segments:
		filename = segment.get('ytid')
		start_frame, end_frame = segment.get('s')
		print 'showing %s from %d to %d' % (filename, start_frame, end_frame)
		result = show_video(filename, start_frame, end_frame, label)
		if result:
			tp += 1
		else:
			fp += 1

	print 'Label: %s' % label
	print 'True positives: %d' % tp
	print 'False positives: %d' % fp

if __name__ == '__main__':
	main()
