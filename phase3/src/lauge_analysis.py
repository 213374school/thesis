#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import json
import cv
import cv2
import video
from common import anorm2, draw_str
from time import clock
import os
import json


help_message = '''
USAGE: lauge_analysis.py [<video_source_directory>]
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

		directionVectorCalculatorMethod = 'good_features'

		frame_count = 1
		print 'movie length = %d' % (self.num_frames / self.fps)

		videoFileName = (self.video_src.split('/'))[-1]
		if directionVectorCalculatorMethod == 'shift_vector':
			metadataFilename = '../../phase1/DataSet/Metadata/%s_metadata.txt' % videoFileName
			f = open(metadataFilename,'r')
			content = f.read()
			content = json.loads(content)
			shift_vectors = content.get('shift_vectors')
			f.close()

		# Make optical flow tracking grid

		ret, frame = self.cam.read()
		try:
			frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
		colorCounters = []
		videoData = []
		meanVectorLength = [[],[],[],[],[],[],[],[],[]]
		horizontalMovement = [[],[],[],[],[],[],[],[],[]]
		verticalMovement = [[],[],[],[],[],[],[],[],[]]
		brightness = []
		while True:

			if directionVectorCalculatorMethod == 'shift_vector':
				shift_vector = shift_vectors[frame_count]

			frame_count += 1

			ret, frame = self.cam.read()
			try:
				frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				brightness.append(int(np.mean(frame_gray)))
			except:
				print 'error when converting to grayscale. aborting...'
				break

			vis2 = frame.copy()
			vis = np.zeros(shape=(h,w))

			avr_track_dist = 0
			if previous_frame_set:
				img0, img1 = previous_frame, frame_gray

				# Track good features for estimation of overall movement
				good_features = cv2.goodFeaturesToTrack(previous_frame, **feature_params)
				try:
					good_features_result, good_features_st, good_features_err = cv2.calcOpticalFlowPyrLK(img0, img1, good_features, None, **lk_params)
					didFail = False
				except:
					didFail = True

				if didFail:
					print 'Weird OpecCV error in calcOpticalFlowPyrLK, skipping frame'
				else:
					validGoodFeatureVectors = []
					for i in range(len(good_features_result)):
						if good_features_st[i] > 0:
							[[x,y]] = good_features[i]
							[[xr,yr]] = good_features_result[i]

							validGoodFeatureVectors.append((x-xr,y-yr))
					if len(validGoodFeatureVectors) > 0:
						horizontals = [x for (x,y) in validGoodFeatureVectors]
						verticals = [y for (x,y) in validGoodFeatureVectors]
						x = np.median(horizontals)
						y = np.median(verticals)
						overall = (int(x),int(y))
					else:
						overall = (0,0)

					
					# Track grid points
					result, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, grid, None, **lk_params)

					# Calculate data for each optical flow vector
					data = []
					vector_counter = {}
					validVectors = []
					for i in range(len(result)):
						
						# Get the start and end point of each vector
						g = grid[i][0]
						head = (int(np.round(g[0])),int(np.round(g[1])))
						r = result[i][0]
						tail = (int(np.round(r[0])),int(np.round(r[1])))

						#print head, tail

						# Calculate the base vector
						(x,y) = (head[0]-tail[0], head[1]-tail[1])

						data.append({'head': head, 'tail': tail, 'status': st[i], 'error':err[i], 'vector': (x,y), 'length': -1})

						if st[i] > 0:

							# Add the vector to the vector-counter dictionary
							if (x,y) in vector_counter:
								vector_counter[(x,y)] += 1
							else:
								vector_counter[(x,y)] = 1

							validVectors.append((x,y))

					
					# Calculate the general direction of movement (camera movement)
					if directionVectorCalculatorMethod == 'mean':
						overall = sum(np.float32(validVectors)) / len(validVectors)
						overall = (overall[0], overall[1])
					elif directionVectorCalculatorMethod == 'most_common':
						common_vectors = sorted(vector_counter, key = vector_counter.get, reverse = True)
						try:
							overall = common_vectors[0]
						except:
							overall = (0,0)
					elif directionVectorCalculatorMethod == 'shift_vector':
						overall = shift_vector
					elif directionVectorCalculatorMethod == 'lauge':

						if len(validVectors) > 0:
							horizontals = [x for (x,y) in validVectors]
							verticals = [y for (x,y) in validVectors]

							if np.std(horizontals) < 5000:
								x = np.median(horizontals)
							else:
								x = min(horizontals)

							if np.std(verticals) < 50000:
								y = np.median(verticals)
							else:
								y = min(verticals)
							overall = (int(x),int(y))
						else:
							overall = (0,0)
					elif directionVectorCalculatorMethod == 'good_features':
						#print overall
						pass
					else:
						print 'No valid "direction vector calculation method" given'
						return


					# Normalize vectors and their length using the overall direction of movement
					for d in data:
						if d['status']:
							(ox,oy) = overall
							(tx,ty) = d['tail']
							(vx,vy) = d['vector']
							tail = (tx+ox,ty+oy)
							vector = (vx-ox,vy-oy)
							length = distXY((0,0),vector)
							d['tail'] = tail
							d['vector'] = vector
							d['length'] = length


					# # Find the max length of the 95% shortest vectors
					# # The remaining 5% are considered noise and are ignored
					# lengths = [d['length'] for d in data]
					# if len(lengths) > 0:
					# 	lengths.sort()
					# 	index = int(len(lengths) * 0.95)
					# 	max_length = lengths[index]
					# else:
					# 	max_length = 10000000
					# if max_length < 10:
					# 	max_length = 10
					

					# Draw the optical flow vectors
					colorCounter = [0,0,0]
					for d in data:
						head = d['head']
						tail = d['tail']
						length = d['length']
						status = d['status']
						error = d['error']
						if status > 0 and error < 5:
							if length < 1:
								color = (0, 255, 0)
								colorCounter[1] += 1
							elif length > 10:
								color = (0, 0, 255)
								colorCounter[2] += 1
							else:
								color = (255, 0, 0)
								colorCounter[0] += 1

							cv2.line(vis, head, tail, (255, 0, 0))
							cv2.circle(vis, tail, 2, (255, 0, 0), -1)
							cv2.line(vis2, head, tail, color)
							cv2.circle(vis2, tail, 2, color, -1)

						else:
							cv2.circle(vis, head, 2, (255, 0, 0), -1)
							cv2.circle(vis2, head, 2, (255, 0, 0), -1)
					colorCounters.append(colorCounter)


					# Divide the vectors into 9 bins each covering 1/9th of the
					# frame in order to analyse them individually
					bins = [[],[],[],[],[],[],[],[],[]]
					for i in range(len(data)):
						head = data[i]['head']
						tail = data[i]['tail']
						error = data[i]['error']
						(x,y) = head

						if st[i] > 0 and error < 5:
							vector = data[i]['vector']

							if x < w / 3 and y < h / 3:
								bins[0].append(vector)	# Top left
							if x > w / 3 and x < w * 2 / 3 and y < h / 3:
								bins[1].append(vector)	# Top center
							if x > w * 2 / 3 and y < h / 3:
								bins[2].append(vector)	# Top right

							if x < w / 3 and y > h / 3 and y < h * 2 / 3:
								bins[3].append(vector)	# Middle left
							if x > w / 3 and x < w * 2 / 3 and y > h / 3 and y < h * 2 / 3:
								bins[4].append(vector)	# Middle center
							if x > w * 2 / 3 and y > h / 3 and y < h * 2 / 3:
								bins[5].append(vector)	# Middle right

							if x < w / 3 and y > h * 2 / 3:
								bins[6].append(vector)	# Bottom left
							if x > w / 3 and x < w * 2 / 3 and y > h * 2 / 3:
								bins[7].append(vector)	# Bottom center
							if x > w * 2 / 3 and y > h * 2 / 3:
								bins[8].append(vector)	# Bottom right

					for i in range(len(bins)):

						bin = np.array(bins[i])
						if len(bin) > 1:

							mean_length = np.mean([distXY((0,0),(x,y)) for (x,y) in bin])
							vertical = np.mean([y for (x,y) in bin])
							horizontal = np.mean([x for (x,y) in bin])

							if i == 0 or i == 3 or i == 6:
								x = w / 6
							if i == 1 or i == 4 or i == 7:
								x = w / 2
							if i == 2 or i == 5 or i == 8:
								x = w * 5 / 6

							if i <= 2:
								y = h / 6
							if i >= 3 and i <= 5:
								y = h / 2
							if i >= 6:
								y = h * 5 / 6

							center = (x,y)

							if mean_length < 1:
								cv2.circle(vis2, center, 20, (0, 255, 0), -1)
							elif mean_length > 10:
								cv2.circle(vis2, center, 20, (0, 0, 255), -1)
						else:
							mean_length = 0
							vertical = 0
							horizontal = 0

						meanVectorLength[i].append(mean_length)
						verticalMovement[i].append(vertical)
						horizontalMovement[i].append(horizontal)

			previous_frame = frame_gray
			previous_frame_set = True
			if show_video:
				cv2.imshow('lk_track', vis)
				cv2.imshow('lk_track2', vis2)
				ch = cv2.waitKey(24/24)
				if ch == 27:
					break

			if not frame_count % 25:
				print '%2.2f%% done' % (100.0*float(frame_count)/float(self.num_frames))

		# Add information to metadata-file
		ytid = videoFileName.split('.')[0]
		filepath = os.path.dirname(os.path.realpath(__file__)) + '/../metadata/' + ytid + '.json'
		print 'attempting to write to: ' + filepath
		if os.path.isfile(filepath):
			f = open(filepath, 'r+')
			fileContent = json.loads(f.read())
			print 'file already exists, add to it'
		else:
			f = open(filepath,'w')
			fileContent = {}
			print 'file doesnt exist. Create it'
		fileContent['mean_vector_length'] = meanVectorLength
		fileContent['vertical_movement'] = verticalMovement
		fileContent['horizontal_movement'] = horizontalMovement
		fileContent['brightness'] = brightness
		print 'writing'
		f.write(json.dumps(fileContent))
		f.close()
		print 'done'
				
		return self.frame_metadata

def main():
	import sys
	print help_message
	try: video_src_dir = sys.argv[1]
	except: return

	listOfFiles = os.listdir(video_src_dir)
	listOfFilenames = []
	for aFile in listOfFiles:
		if not aFile == '' and not aFile == 'youtube-dl.py' and not aFile == '.DS_Store':
			listOfFilenames.append(aFile)
	
	for aFile in listOfFilenames:
		#print video_src_dir + aFile
		App(video_src_dir + aFile).run(False)

if __name__ == '__main__':
	main()