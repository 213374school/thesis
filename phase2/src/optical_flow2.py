#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import cv
import cv2
import video
from common import anorm2, draw_str
from time import clock

help_message = '''
USAGE: optical_flow2.py [<video_source>]

Keys:
  SPACE - reset features
'''

NO_HORIZONTAL_POINTS = 24
NO_VERTICAL_POINTS = 16

lk_params = dict( winSize  = (30, 30), 
				  maxLevel = 2, 
				  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict( maxCorners = 500, 
					   qualityLevel = 0.3,
					   minDistance = 7,
					   blockSize = 7 )

def distXY(x,y):

	res = np.sqrt(np.sum((np.linalg.norm(x)-np.linalg.norm(y))**2))    
	return res

def dist(tr):
	d = 0
	for i in range(0, len(tr)-1):
		d += distXY(tr[i], tr[i+1])
	return d

class FrameMetadata:
	def __init__(self):
		self.tracks = []
		self.brightness = 0
		self.avr_track_dist = 0
		self.frame_gray = None
		self.good_features_to_track = 0

class App:
	def __init__(self, video_src):
		self.track_len = 10
		self.detect_interval = 5
		self.tracks = []
		self.cam = video.create_capture(video_src)
		self.frame_idx = 0
		self.video_src = video_src
		capture = cv.CaptureFromFile(video_src)
		self.num_frames = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT))
		self.fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
		self.frame_metadata = []

	def run(self, show_video = False):

		frame_count = 1
		print 'movie length = %d' % (self.num_frames / self.fps)

		# Make optical flow tracking grid

		ret, frame = self.cam.read()
		try:
			frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			brightness = int(np.mean(frame_gray))
		except:
			print 'error when converting to grayscale. aborting...'
			return
		(w,h) = cv.GetSize(cv.fromarray(frame_gray))

		tmp = []
		x = 1
		y = 1
		while x < NO_HORIZONTAL_POINTS + 1:
			realX = w * x / (NO_HORIZONTAL_POINTS + 1)
			while  y < NO_VERTICAL_POINTS + 1:
				realY = h * y / (NO_VERTICAL_POINTS + 1)
				tmp.append([[realX,realY]])
				y += 1
			x += 1
			y = 1

		grid = np.float32(np.array(tmp))
		

		# Do optical flow tracking
		previous_frame = None
		previous_frame_set = False
		while True:

			frame_count += 1

			ret, frame = self.cam.read()
			try:
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				brightness = int(np.mean(frame_gray))
			except:
				print 'error when converting to grayscale. aborting...'
				break

			vis = frame.copy()

			avr_track_dist = 0
			if previous_frame_set:
				img0, img1 = previous_frame, frame_gray
				
				result, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, grid, None, **lk_params)
				
				if show_video:
					#_tracks = self.tracks
					#cv2.polylines(vis, [np.int32(tr[len(tr)-2:]) for tr in _tracks], False, (0, 255, 0))
					heads = []
					tails = []
					allVectors = []
					for i in range(len(result)):
						
						g = grid[i][0]
						head = (g[0],g[1])
						heads.append(head)
						r = result[i][0]
						tail = (r[0],r[1])
						tails.append(tail)

						if st[i] > 0:
							allVectors.append((head[0]-tail[0],head[1]-tail[1]))

					allVectors = np.float32(np.int32(np.array(allVectors) * 10))
					print allVectors
					word_counter = {}
					for word in allVectors:
						w = (word[0], word[1])
						if w in word_counter:
							word_counter[w] += 1
						else:
							word_counter[w] = 1

					#print word_counter
					popular_words = sorted(word_counter, key = word_counter.get, reverse = True)
					overall = popular_words[0]

					print overall

					meanMovement = sum(np.float32(allVectors)) / len(allVectors)
					meanMovement = (meanMovement[0], meanMovement[1])
					
					for i in range(len(heads)):
						head = heads[i]
						if st[i] > 0:
							_t = tails[i]
							#print _t, meanMovement
							tail = (_t[0]+meanMovement[0], _t[1]+meanMovement[1])
							cv2.line(vis, head, tail, (255, 0, 0))
							cv2.circle(vis, head, 2, (255, 0, 0), -1)
						else:
							cv2.circle(vis, head, 2, (0, 0, 255), -1)
			
			previous_frame = frame_gray
			previous_frame_set = True
			if show_video:
				#draw_str(vis, (20, 20), '#tracks: %d, brightness: %d, avr. track dist.: %2.2f, time: %2.2f' % (len(self.tracks), brightness, avr_track_dist, (frame_count / self.fps)))
				#draw_str(vis, (20, 40), '# good features to track %d' % (num_good_feat))
				cv2.imshow('lk_track', vis)
				ch = cv2.waitKey(1000/24)
				if ch == 27:
					break

			if not frame_count % 25:
				print '%2.2f%% done' % (100.0*float(frame_count)/float(self.num_frames))   
				
		return self.frame_metadata

def main():
	import sys
	try: video_src = sys.argv[1]
	except: video_src = video.presets['chess']

	print help_message
	App(video_src).run(True)

if __name__ == '__main__':
	main()