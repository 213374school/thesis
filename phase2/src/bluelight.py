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
import math
import pylab
import numpy as np
import numpy

# Find a JSON parser
try:
	import json
except ImportError:
	try:
		import simplejson as json
	except ImportError:
		print 'ERROR: JSON parser not found!'

from collections import deque

helptxt = """usage:%s video_src""" % __file__

def smoothTriangle(lst=[], degree=1):

	if degree < 1:
		print 'degree must be > 1'
		return

	triangle = numpy.array(range(degree)+[degree]+range(degree)[::-1])+1
	lst = numpy.array(lst)
	lst_lenght = len(lst)
	tri_len = len(triangle)
	_max = lst_lenght - degree
	triangle_normal_sum = float(sum(triangle))
	
	smoothed_lst = []
	for i in range(lst_lenght):

		if i > degree and i < _max:
			new_value = sum(triangle * lst[i-degree:i+degree+1]) / triangle_normal_sum
		else:
			left = degree - min(i, degree)
			right = degree + min(degree, lst_lenght - 1 - i) + 1			
			tri = triangle[left:right]
			triangle_sum = sum(tri)

			new_value = 0.0
			for j in range(len(tri)):

				pos = j + i + left - degree
				new_value += tri[j] * lst[pos]
		
			new_value /= triangle_sum

		smoothed_lst.append(new_value)

	return smoothed_lst

class Simplemovingaverage():
	def __init__(self, period):
		assert period == int(period) and period > 0, "Period must be an integer >0"
		self.period = period
		self.stream = deque()
 
	def __call__(self, n):
		stream = self.stream
		stream.append(n)	# appends on the right
		streamlength = len(stream)
		if streamlength > self.period:
			stream.popleft()
			streamlength -= 1
		if streamlength == 0:
			average = 0
		else:
			average = sum( stream ) / streamlength
 
		return average

def get_local_minmax(data):

	# print 'number of datapoints: ', len(data)

	diff = np.diff
	sign = np.sign

	lmin = (diff(sign(diff(data))) > 0).nonzero()[0] + 1 # local min
	lmax = (diff(sign(diff(data))) < 0).nonzero()[0] + 1 # local max

	# is very first datapoint a local maxima or minima?
	if diff(data[:2])[0] > 0:
		lmin_start = np.array([0])
		lmax_start = np.array([], dtype=np.int64)
	else:
		lmin_start = np.array([], dtype=np.int64)
		lmax_start = np.array([0])

	# is very last datapoint a local maxima or minima?
	if diff(data[-2:])[0] > 0:
		lmin_end = np.array([], dtype=np.int64)
		lmax_end = np.array([len(data)-1])
	else:
		lmin_end = np.array([len(data)-1])
		lmax_end = np.array([], dtype=np.int64)

	lmin = np.concatenate((lmin_start, lmin, lmin_end))
	lmax = np.concatenate((lmax_start, lmax, lmax_end))

	return lmin, lmax

# http://paddy3118.blogspot.dk/2007/02/unzip-un-needed-in-python.html
def unzip(l):

	return zip(*l)

def main():

	try:
		video_src = sys.argv[1]
	except:
		print helptxt
		return
	else:	
		cap = video.create_capture(video_src)		
		capture = cv.CaptureFromFile(video_src)
		fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
		w = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
		h =  int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
		num_frames = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT) - 3 # always 3 too many????

		ytid = video_src.split('/')[-1].split('.')[0]
		metadata_filename = './metadata/blue_channel/%s.json' % ytid
		if os.path.isfile(metadata_filename):
			f = open(metadata_filename,'r')
			content = f.read()
			bclib = json.loads(content)     
			f.close()
		else:
			bclib = dict()

		if not bclib:
			index = 0
			blue_mean = []
			while True:
				ret, frame = cap.read()
				if not ret:
					break
				else:
					# order of channels is reversed in opencv
					blue_chan = frame[:,:,0]
					blue_mean.append(np.mean(blue_chan))
			bclib['blue_mean'] = blue_mean
			content = json.dumps(bclib)

			# do not write a file if json parser fails
			if content:
				# write to disc
				f = open(metadata_filename,'w') 
				f.write(content)
				f.close()					
		else:
			blue_mean = bclib.get('blue_mean')

		pylab.figure(figsize=(10,10))		
		pylab.suptitle('%s' % video_src, fontsize=16)

		# need to make it a numpy array to index it with another numpy array
		# also smooth the data abit
		blue_mean_smooth = np.array(smoothTriangle(blue_mean, 5))
		lmin, lmax = get_local_minmax(blue_mean_smooth)

		# get distance between each minima
		# minima_mov_avr = Simplemovingaverage(1)
		# dist_minima = []
		# for i in range(1,len(lmin)):
		# 	dist_minima.append(abs(lmin[i] - lmin[i-1]))
		# dist_minima = zip(lmin, dist_minima)

		# maxima_mov_avr = Simplemovingaverage(1)
		# dist_maxima = []
		# for i in range(1,len(lmax)):
		# 	dist_maxima.append(abs(lmax[i] - lmax[i-1]))
		# dist_maxima = zip(lmax, dist_maxima)

		# compute linear coefficient for each point
		# dist_minima_coefficients = []
		# for i in range(1, len(dist_minima)):
		# 	x1,y1 = dist_minima[i-1]
		# 	x2,y2 = dist_minima[i]
		# 	c = float(y1-y2) / float(x1-x2)
		# 	dist_minima_coefficients.append((x1,c))

		# print 'local minima coefficients'
		# for x,c in dist_minima_coefficients:
		# 	print '%d: %2.2f' % (x,c)

		# TODO: only looking at distances between local minima
		z = []
		w = []
		for i in range(1, min(len(lmax), len(lmin))-1):
			x1 = lmin[i-1]
			x2 = lmin[i]			
			x3 = lmin[i+1]
			x4 = lmax[i-1]
			x5 = lmax[i]			
			x6 = lmax[i+1]
			h1 = abs(blue_mean_smooth[x1] - blue_mean_smooth[x4])
			h2 = abs(blue_mean_smooth[x3] - blue_mean_smooth[x6])
			d1, d2, d3, d4 = abs(x1-x2), abs(x2-x3), abs(x4-x5), abs(x5-x6)
			# within X% of each other
			b = False
			if d2 < d1 * 1.10 and d2 > d1 * 0.90 and np.mean([h1, h2]) > 1.00:
				# print '%2.2f' % np.mean([h1, h2])
				b = True
				z.append((x1,x3))
			if d4 < d3 * 1.10 and d4 > d3 * 0.90 and np.mean([h1, h2]) > 1.00:
				# print '%2.2f' % np.mean([h1, h2])
				# print x4,d3
				# print x6,d4
				b = True
				w.append((x4,x6))
			if not b:
				# more than a single pair
				if len(z) > 1 or len(w) > 1:
					f1, f2 = min(min(z+w)), max(max(z+w))
					ff = abs(f1-f2)
					f1 -= ff * 0.10
					f2 += ff * 0.10
					print '%2.2f->%2.2f' % (f1/fps, f2/fps)
				z = []
				w = []

		t = np.linspace(0, num_frames/fps, num_frames)

		pylab.subplot(1,1,1, title='')
		# pylab.plot(t, blue_mean_smooth,".b")
		pylab.plot(t, blue_mean_smooth,"-k")  
		pylab.plot(t[lmin], blue_mean_smooth[lmin], "or", label="min")
		pylab.plot(t[lmax], blue_mean_smooth[lmax], "og", label="max")		
		pylab.axis([-1, t[-1]+1, min(blue_mean_smooth) - 1, max(blue_mean_smooth) + 1])
		pylab.xlabel('secs.')
		pylab.grid(True)

		# pylab.subplot(2,1,2, title='')
		# x, dist_minima_coefficients = zip(*dist_minima_coefficients)
		# t = np.linspace(x[0]/fps, x[-1]/fps, len(x))
		# pylab.plot(t, dist_minima_coefficients,"or")
		# pylab.plot(t, dist_minima_coefficients,"-r")
		# # x, dist_maxima = zip(*dist_maxima)
		# # t = np.linspace(x[0]/fps, x[-1]/fps, len(x))		
		# # pylab.plot(t, dist_maxima,"ob")
		# # pylab.plot(t, dist_maxima,"-b")
		# # pylab.axis([-1, t[-1]+1, min(dist_minima + dist_maxima) - 1, max(dist_minima + dist_maxima) + 1])
		# pylab.axis()
		# pylab.xlabel('secs.')
		# pylab.grid(True)

		# pylab.subplot(2,1,2, title='')
		# x, dist_minima = zip(*dist_minima)
		# t = np.linspace(x[0]/fps, x[-1]/fps, len(x))
		# pylab.plot(t, dist_minima,"or")
		# pylab.plot(t, dist_minima,"-r")
		# x, dist_maxima = zip(*dist_maxima)
		# t = np.linspace(x[0]/fps, x[-1]/fps, len(x))		
		# pylab.plot(t, dist_maxima,"ob")
		# pylab.plot(t, dist_maxima,"-b")
		# pylab.axis([-1, t[-1]+1, min(dist_minima + dist_maxima) - 1, max(dist_minima + dist_maxima) + 1])
		# pylab.xlabel('secs.')
		# pylab.grid(True)

		pylab.show()

		# pylab.plot(dist_minima,".b")  
		# pylab.plot(dist_minima,"-b")
		# pylab.plot(dist_maxima,".r")  
		# pylab.plot(dist_maxima,"-r")

		# p = []
		# n = []
		# x = []
		# i = 0
		# for d in diffs:
		# 	if abs(d) < 6: # within acceptable range
		# 		if n:
		# 			# plot values outside acceptable range and reset
		# 			pylab.plot(x, n, ".r")  
		# 			pylab.plot(x, n, "-r")
		# 			n = []
		# 			x = []					
		# 		p.append(d)
		# 		x.append(i)					
			
		# 	else:
		# 		if p: # outside acceptable range
		# 			# plot values in acceptable range and reset
		# 			if len(p) > 2:
		# 				pylab.plot(x, p, ".g")  
		# 				pylab.plot(x, p, "-g")
		# 				print 'frames with bluelight: %d to %d' % (x[0], x[-1])
		# 			else:
		# 				pylab.plot(x, p, ".r")  
		# 				pylab.plot(x, p, "-r")						
		# 			p = []
		# 			x = []
		# 		n.append(d)
		# 		x.append(i)

		# 	i += 1

		# # plot remaining values
		# if p:			
		# 	if len(p) > 2:
		# 		pylab.plot(x, p, ".g")  
		# 		pylab.plot(x, p, "-g")
		# 		print 'frames with bluelight: %d to %d' % (x[0], x[-1])
		# 	else:
		# 		pylab.plot(x, p, ".r")  
		# 		pylab.plot(x, p, "-r")
		# elif n:
		# 	pylab.plot(n,".r")  
		# 	pylab.plot(n,"-r")

		# pylab.axis()
		# pylab.xlabel('secs.')
		# pylab.grid(True)

		# pylab.show()

if __name__ == "__main__":
	 main()