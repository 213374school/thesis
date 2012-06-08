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

helptxt = """usage:\n./blueblink.py video_src"""

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

	diff = np.diff
	sign = np.sign
	# a = diff(sign(diff(data))).nonzero()[0] + 1 # local min+max
	b = (diff(sign(diff(data))) > 0).nonzero()[0] + 1 # local min
	c = (diff(sign(diff(data))) < 0).nonzero()[0] + 1 # local max	

	return np.array(b), np.array(c)

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
				index += 1

				# img = cv.fromarray(blue_chan)
				# ShowImage("", img)
				# cv2.waitKey(int(1000.0/fps))

		pylab.figure(figsize=(10,10))		
		pylab.suptitle('%s' % video_src, fontsize=16)

		# need to make it a numpy array to index it with another numpy array
		blue_mean_smooth = np.array(smoothTriangle(blue_mean, 6))

		lmin, lmax = get_local_minmax(blue_mean_smooth)

		### compute the running std. dev. for distances between each minima/maxima

		# get distance between each minima
		minima_mov_avr = Simplemovingaverage(1)
		dist_minima = []
		for i in range(1,len(lmin)):
			dist_minima.append(minima_mov_avr(lmin[i] - lmin[i-1]))

		maxima_mov_avr = Simplemovingaverage(1)
		dist_maxima = []
		for i in range(1,len(lmax)):
			dist_maxima.append(maxima_mov_avr(lmax[i] - lmax[i-1]))

		# avr. of both
		dist_min_maxima = []
		for i in range(min(len(dist_minima), len(dist_maxima))):
			dist_min_maxima.append(np.mean([dist_minima[i], dist_maxima[i]]))

		# all that is left is find the ones matching a local straight horizontal line
		diffs = [dist_min_maxima[i] - dist_min_maxima[i-1] for i in range(1,len(dist_min_maxima))]
		

		avr_dist = np.mean(dist_min_maxima)
		std_dev_dist = np.mean(dist_min_maxima)

		t = np.linspace(0, num_frames/fps, num_frames)

		pylab.subplot(2,1,1, title='')
		pylab.plot(t, blue_mean_smooth,".b")  
		pylab.plot(t, blue_mean_smooth,"-b")  
		pylab.plot(t[lmin], blue_mean_smooth[lmin], "o", label="min")
		pylab.plot(t[lmax], blue_mean_smooth[lmax], "o", label="max")		
		pylab.axis()
		pylab.xlabel('secs.')
		pylab.grid(True)

		pylab.subplot(2,1,2, title='')
		# pylab.plot(dist_minima,".b")  
		# pylab.plot(dist_minima,"-b")
		# pylab.plot(dist_maxima,".r")  
		# pylab.plot(dist_maxima,"-r")

		p = []
		n = []
		x = []
		i = 0
		for d in diffs:
			if abs(d) < 6: # within acceptable range
				if n:
					# plot values outside acceptable range and reset
					pylab.plot(x, n, ".r")  
					pylab.plot(x, n, "-r")
					n = []
					x = []					
				p.append(d)
				x.append(i)					
			
			else:
				if p: # outside acceptable range
					# plot values in acceptable range and reset
					if len(p) > 2:
						pylab.plot(x, p, ".g")  
						pylab.plot(x, p, "-g")
					else:
						pylab.plot(x, p, ".r")  
						pylab.plot(x, p, "-r")						
					p = []
					x = []
				n.append(d)
				x.append(i)

			i += 1

		# plot remaining values
		if p:			
			if len(p) > 2:
				pylab.plot(x, p, ".g")  
				pylab.plot(x, p, "-g")
			else:
				pylab.plot(x, p, ".r")  
				pylab.plot(x, p, "-r")
		elif n:
			pylab.plot(n,".r")  
			pylab.plot(n,"-r")

		pylab.axis()
		pylab.xlabel('secs.')
		pylab.grid(True)

		pylab.show()

if __name__ == "__main__":
	 main()