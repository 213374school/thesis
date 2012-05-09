#!/usr/bin/env python

import vid_segmenter as segmenter
import compute_frame_state
import sys
import cv
import cv2
import numpy as np
import math
import pylab
from common import draw_str

smoothTriangle = segmenter.smoothTriangle
getVideoMetadata = segmenter.getVideoMetadata
computeFrameStateAnders = compute_frame_state.computeFrameStateAnders
computeFrameStateLauge = compute_frame_state.computeFrameStateLauge

help_message = '''
USAGE: show.py <video_source> <'lauge' or 'anders'>'''

def main():
	video_src = None
	try:
		arg1 = sys.argv[1]
		arg2 = sys.argv[2]
		if arg1 == '-?':
			print help_message
			return
		else:
			video_src = arg1	
	except:		
		if video_src is None:
			print help_message
			return

	d,frames = getVideoMetadata(video_src, True)

	shift_vectors = d['shift_vectors']
	rmsdiffs = d['rmsdiffs']
	shift_vectors_sliding = d['shift_vectors_sliding']
	stand_dev = d['stand_dev']

	capture = cv.CaptureFromFile(video_src)
	fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	num_frames = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT))

	# degree of smoothness
	degree = 12
	# time in seconds
	t = np.linspace(0, num_frames/fps, len(frames))
	# values are normalized to [0...1]
	# the magnitude of the vector - apply weights according to the direction of the vector? ie. vertical panning is worse than horizontal
	magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
	# a measure of variation/contrast in the frame - a high value indicated less contrast and vice versa
	contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
	# compute if a frame is accepted, and the according value
	if arg2 == 'anders':
		frame_states, frame_values = computeFrameStateAnders(magnitudes, contrast)
	elif arg2 == 'lauge':
		frame_states, frame_values = computeFrameStateLauge(magnitudes, contrast)
	else:
		return

	print 'video playback...'

	index = 0
	for frame in frames:
		frame_state = 'BAD' if not frame_states[index] else 'GOOD'
		frame_value = frame_values[index]
		draw_str(frame, (20, 20), 'time: %2.1f:%2.1f, magnitude: %2.2f%%, contrast^-1: %2.2f' % (t[index], t[-1], 100 * magnitudes[index], contrast[index]))						
		draw_str(frame, (20, 40), '%s (%2.3f)' % (frame_state, frame_value))

		index += 1
		cv2.imshow('final cut', frame)
		cv2.waitKey(int(1000/fps))

if __name__ == '__main__':
    main()