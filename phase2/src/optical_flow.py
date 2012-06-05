#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import cv2.cv as cv
from cv2.cv import *
import video
import cv2
# for printing on one line
from sys import stdout
import os

# Find a JSON parser
try:
	import json
	# import simplejson as json 
except ImportError:
	try:
		import simplejson as json
		# import json
	except ImportError:
		print 'ERROR: JSON parser not found!'

helptxt = """usage:\n./object_detection.py video_src_file [mode=faces,body,profile]"""

lk_params = dict( winSize  = (15, 15), 
                  maxLevel = 2, 
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
                  derivLambda = 0.0 )    

feature_params = dict( maxCorners = 500, 
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )

def main():
	
	try:
		cap = video.create_capture(sys.argv[1])
		video_src = sys.argv[1]
	except:
		print helptxt
	else:
		try:
			mode = sys.argv[2]
		except:
			mode = 'faces'
		try:
			show = sys.argv[3]
		except:
			show = False           
		object_detect(video_src, show, mode)

def object_detect(video_src, show=False, mode='faces'):

	# fixed these parameters, we will group detected objects later on
	# The factor by which the search window is scaled between the subsequent scans, 1.1 means increasing window by 10 %
	
	# scaleFactor = 1.1
	# minNeighbors = 1

	# ytid = video_src.split('/')[-1].split('.')[0]
	# if mode == 'faces':
	#     mdpath = 'facedetect'
	# elif mode == 'body':
	#     mdpath = 'bodydetect'
	# elif mode == 'profile':
	#     mdpath = 'profile'
	# metadata_filename = './metadata/%s/%s.json' % (mdpath, ytid)
	# if os.path.isfile(metadata_filename):
	#     f = open(metadata_filename,'r')
	#     content = f.read()
	#     fdlib = json.loads(content)     
	#     f.close()
	# else:
	#     fdlib = dict()
	# if not fdlib.get(mode):
	#     fdlib[mode] = []
	#     fdlib['scale_factor'] = scaleFactor
	#     fdlib['min_neighbors'] = minNeighbors
	#     fdlib['ytid'] = ytid

	cap = video.create_capture(video_src)

	capture = cv.CaptureFromFile(video_src)
	fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	num_frames = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT) - 3 # always 3 too many????
	lngth_in_secs = num_frames / 24

	storage = cv.CreateMemStorage()

	if show:

		index = 0
		font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1.0, 1.0)

		ret, frame = cap.read()
		if ret:
			frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		else:
			return
		previous_img = cv.fromarray(frame_gray)
		prev_pyramid = cv.CreateImage (cv.GetSize (previous_img), 8, 1)

		while True:
			ret, frame = cap.read()
			if ret:
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			else:
				break
			current_img = cv.fromarray(frame_gray)
			pyramid = cv.CreateImage (cv.GetSize (current_img), 8, 1)

			#########################################################

			# we want to search all the good points

			# create the wanted images
			eig = cv.CreateImage (cv.GetSize (current_img), 32, 1)
			temp = cv.CreateImage (cv.GetSize (current_img), 32, 1)

			# the default parameters
			quality = 0.01
			min_distance = 10

			# search the good points
			previous_features = cv.GoodFeaturesToTrack (previous_img, eig, temp, MAX_COUNT, quality, min_distance, None, 3, 0, 0.04)
			current_features = cv.GoodFeaturesToTrack (current_img, eig, temp, MAX_COUNT, quality, min_distance, None, 3, 0, 0.04)

			# refine the corner locations
			previous_features = cv.FindCornerSubPix (previous_img, previous_features, (win_size, win_size),  (-1, -1), (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS, 20, 0.03))
			current_features = cv.FindCornerSubPix (current_img, current_features, (win_size, win_size),  (-1, -1), (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS, 20, 0.03))

			#########################################################
			

			# calculate the optical flow
			features, status, track_error = cv.CalcOpticalFlowPyrLK (
				previous_img, current_img, prev_pyramid, pyramid,
				previous_features,
				(win_size, win_size), 3,
				(cv.CV_TERMCRIT_ITER|cv.CV_TERMCRIT_EPS, 20, 0.03),
				flags)

			print len(features), len(status), len(track_error)
			
			# for (x,y,w,h),n in detected_objects[index]:
			# 	color = 255
			# 	if n > 5:                    
			# 		cv.Rectangle(img, (x,y), (x+w,y+h), color)
			# 		# draw the number of neighbors grouped into one rectangle???
			# 		cv.PutText(img, '%d' % n, (x+w/2,y+h/2), font, color)
			img = current_img
			# draw the points as green circles
			for the_point in features:
				cv.Circle (img, (int(the_point[0]), int(the_point[1])), 3, (0, 255, 0, 0), -1, 8, 0)
			ShowImage("object detection demo", img)
			cv2.waitKey(int(10.0/fps))

			index += 1

			previous_img = current_img
			prev_pyramid = pyramid

if __name__ == "__main__":
	 main()
