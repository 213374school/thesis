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
	num_frames = end_frame - start_frame
	if cap.set(cv.CV_CAP_PROP_POS_FRAMES, start_frame):
		length = end_frame - start_frame
		for i in range(length):
			ret, frame = cap.read()
			if ret:
				if first_frame:
					draw_str(frame, (20, 20), '%s? %s' % (label, state))
					cv2.imshow('', frame)
					ch = cv2.waitKey(2000)
				else:
					ch = cv2.waitKey(int(1000/fps))
				if ch == 113:
					break
				first_frame = False
				state = 'NO!' if keyDown else 'YES!'
				draw_str(frame, (20, 20), '%s? %s' % (label, state))
				cv2.imshow('', frame)
				if ch != -1: # key pressed
					keyDown = True if not keyDown else False
			else:
				break
	else:
		raise Exception('unable to set position to %d' % start_frame)
	if state == 'NO!':
		return 0, num_frames
	return 1, num_frames

def main():
	segment_database = SegmentDatabase()
	label = 'vertical_oscillation'
	segments = segment_database.get_with_label(label)
	print '#segments for label %s: %d' % (label, len(segments))
	tp = 0
	fp = 0
	segment_count = 0
	for segment in segments:
		try:
			segment_count += 1
			filename = segment.get('ytid')
			start_frame, end_frame = segment.get('s')
			# print 'showing %s from %d to %d' % (filename, start_frame, end_frame)
			print 'segment length: %d' % (end_frame-start_frame)
			result, num_frames = show_video(filename, start_frame, end_frame, label)
			if result:
				tp += num_frames
			else:
				fp += num_frames
			print '%2.2f%% done' % (100.0 * segment_count / float(len(segments)))
		except Exception as e:
			print e

	print 'Label: %s' % label
	print 'True positives: %d' % tp
	print 'False positives: %d' % fp

if __name__ == '__main__':
	main()
