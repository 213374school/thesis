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
	scaleFactor = 1.1
	minNeighbors = 1

	ytid = video_src.split('/')[-1].split('.')[0]
	if mode == 'faces':
		mdpath = 'facedetect'
	elif mode == 'body':
		mdpath = 'bodydetect'
	elif mode == 'profile':
		mdpath = 'profile'
	metadata_filename = './metadata/%s/%s.json' % (mdpath, ytid)
	if os.path.isfile(metadata_filename):
		f = open(metadata_filename,'r')
		content = f.read()
		fdlib = json.loads(content)     
		f.close()
	else:
		fdlib = dict()
	if not fdlib.get(mode):
		fdlib[mode] = []
		fdlib['scale_factor'] = scaleFactor
		fdlib['min_neighbors'] = minNeighbors
		fdlib['ytid'] = ytid

	cap = video.create_capture(video_src)

	capture = cv.CaptureFromFile(video_src)
	fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	num_frames = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT) - 3 # always 3 too many????
	lngth_in_secs = num_frames / 24

	storage = cv.CreateMemStorage()

	# https://code.ros.org/trac/opencv/browser/trunk/opencv/data/haarcascades?rev=128
	if mode == 'faces':
		haar = cv.Load('./data/haarcascade/haarcascade_frontalface_default.xml')
	elif mode == 'body':
		haar = cv.Load('./data/haarcascade/haarcascade_upperbody.xml')
	elif mode == 'profile':
		haar = cv.Load('./data/haarcascade/haarcascade_profileface.xml')

	if not fdlib[mode]:
		index = 0
		while True:
			ret, frame = cap.read()
			if ret:
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			else:
				break
			img = cv.fromarray(frame_gray)
			faces = []
			# if False: # skipping abit :D
			faces = cv.HaarDetectObjects(img, haar, storage, scaleFactor, minNeighbors)
			fdlib[mode].append(faces)
			index += 1        
			
			stdout.write('detecting %s in %s: %2.2f%% done -> (mm:ss): %02d:%02d\r' % (mode, video_src, 100.0 * index / num_frames, (index/24)/60, (index/24)%60))
			stdout.flush()
		print ''
	else:
		print 'metadata for %s already exists' % ytid

	content = json.dumps(fdlib)

	# do not write a file if json parser fails
	if content:
		# write to disc
		f = open(metadata_filename,'w') 
		f.write(content)
		f.close()

	if show:
		index = 0
		font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1.0, 1.0)
		detected_objects = fdlib[mode]
		while True:
			ret, frame = cap.read()
			if ret:
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			else:
				break
			img = cv.fromarray(frame_gray)            
			
			for (x,y,w,h),n in detected_objects[index]:
				color = 255
				if n > 5:                    
					cv.Rectangle(img, (x,y), (x+w,y+h), color)
					# draw the number of neighbors grouped into one rectangle???
					cv.PutText(img, '%d' % n, (x+w/2,y+h/2), font, color)
			ShowImage("object detection demo", img)
			cv2.waitKey(int(1000.0/fps))

			index += 1

if __name__ == "__main__":
	 main()
