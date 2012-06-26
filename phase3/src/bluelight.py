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
	# if diff(data[:2])[0] > 0:
	# 	lmin_start = np.array([0])
	# 	lmax_start = np.array([], dtype=np.int64)
	# else:
	# 	lmin_start = np.array([], dtype=np.int64)
	# 	lmax_start = np.array([0])

	# # is very last datapoint a local maxima or minima?
	# if diff(data[-2:])[0] > 0:
	# 	lmin_end = np.array([], dtype=np.int64)
	# 	lmax_end = np.array([len(data)-1])
	# else:
	# 	lmin_end = np.array([len(data)-1])
	# 	lmax_end = np.array([], dtype=np.int64)

	# lmin = np.concatenate((lmin_start, lmin, lmin_end))
	# lmax = np.concatenate((lmax_start, lmax, lmax_end))

	return lmin, lmax

# http://paddy3118.blogspot.dk/2007/02/unzip-un-needed-in-python.html
def unzip(l):

	return zip(*l)

helptxt = """usage:%s video_src [show_plot]""" % __file__
DEBUG_MODE = False

def main():

	try:
		video_src = sys.argv[1]
	except:
		print helptxt
		return
	else:
		try:
			sys.argv[2]
		except:
			show_plot = False
		else:
			try:
				show_plot = int(sys.argv[2])
			except:
				show_plot = True

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
					index += 1

					stdout.write('detecting bluelight in %s: %2.2f%% done -> (mm:ss): %02d:%02d\r' % (video_src, 100.0 * index / num_frames, (index/24)/60, (index/24)%60))
					stdout.flush()

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

		# need to make it a numpy array to index it with another numpy array
		# also smooth the data abit
		blue_mean_smooth = np.array(smoothTriangle(blue_mean, 5))
		lmin, lmax = get_local_minmax(blue_mean_smooth)

		z = []
		# triangle treshold
		v = 0.125 # 0.25

		# for formating output
		red = '\033[91m'
		green = '\033[92m'
		black = '\033[0m'

		# save interval(s) to this
		ffs = []
		zz = []
		out = 1

		def commitZ(z):
			f1, f2 = min(min(z)), max(max(z))
			ffs.append((f1,f2))
			# clear z for next interval
			del z[:]

		for i in range(1, min(len(lmax), len(lmin))-1):
			mi1 = lmin[i-1]
			mi2 = lmin[i]			
			mi3 = lmin[i+1]
			ma1 = lmax[i-1]
			ma2 = lmax[i]			
			ma3 = lmax[i+1]
			
			# we want the two minimas between ma1 and ma3 (and ma2 in the middle)
			if mi1 < ma1:
				mi1 = mi2
				mi2 = mi3

			x1,x2,x3,x4,x5 = ma1,mi1,ma2,mi2,ma3
			y1,y2,y3,y4,y5 = blue_mean_smooth[np.array([x1,x2,x3,x4,x5])]

			# the following must now be true
			try:
				assert(x1 < x2)
				assert(x2 < x3)
				assert(x3 < x4)
				assert(x4 < x5)
			except:
				# print i,' of ', min(len(lmax), len(lmin))-1
				# print red, mi1/fps, black
				# print 'ma1,ma2,ma3, mi1,mi2,mi3: ',ma1,ma2,ma3, mi1,mi2,mi3

				# there are some cases of multiple local minima/maxima. we will play along with this anomaly
				# commit z if there are any values in it and continue
				if z:
					commitZ(z)
				continue

			# compute vector magnitudes
			sqrt = math.sqrt
			# a = sqrt((x1-x2)**2 + (y1-y2)**2)
			# b = sqrt((x2-x3)**2 + (y2-y3)**2)
			# c = sqrt((x3-x4)**2 + (y3-y4)**2)
			# d = sqrt((x4-x5)**2 + (y4-y5)**2)

			z1,z2,z3,z4,z5 = np.array([x1,x2,x3,x4,x5], dtype=np.float64) / fps
			a = sqrt((z1-z2)**2 + (y1-y2)**2)
			b = sqrt((z2-z3)**2 + (y2-y3)**2)
			c = sqrt((z3-z4)**2 + (y3-y4)**2)
			d = sqrt((z4-z5)**2 + (y4-y5)**2)

			zz = []
			
			# basically what we want to do is to look at how much the two triangles look alike
			# if the relative standard deviation for all 4 vectors is less than v then we accept the "two triangles"
			xx = [x3-x1, x5-x3]
			yy = [abs(y1-y2), abs(y2-y3), abs(y3-y4), abs(y4-y5)]
			if np.std([a,b,c,d]) / np.mean([a,b,c,d]) < v and np.std(xx) / np.mean(xx) < v/2:
				zz.append((x1,x5))

				if DEBUG_MODE:
					print 'xx: ', xx
					print 'yy: ', yy
					print 'vector magnitudes: ',a,b,c,d
					xs = [x1,x2,x3,x4,x5]
					for x in xs:
						print '(%2.2f,%2.2f)' % (float(x)/fps,blue_mean_smooth[x])
					print 'vert. std.dev. %2.2f%%' % float(100.0 * np.std([a,b,c,d]) / np.mean([a,b,c,d]))
					print 'hor. std.dev. %2.2f%%' % float(100.0 * np.std(xx) / np.mean(xx))

				# plug'n'play into spotlight
				# for i in range(len(xs)-1):
				# 	print '((%f-%f)**2 + (%f-%f)**2)**.5' % (float(xs[i])/fps,float(xs[i+1])/fps, blue_mean_smooth[xs[i]],blue_mean_smooth[xs[i+1]])

				# pylab.figure(figsize=(10,10))
				# pylab.suptitle('%s' % video_src, fontsize=16)
				# pylab.subplot(1,1,1, title='')
				# # t = np.linspace(0, num_frames/fps, num_frames)		
				# # pylab.plot(t, blue_mean_smooth,"-k")
				# # pylab.plot(t[lmin], blue_mean_smooth[lmin], "or", label="min")
				# # pylab.plot(t[lmax], blue_mean_smooth[lmax], "og", label="max")	
				# # pylab.xlabel('secs.')
				# # axis = [float(x1)/fps-.1, float(x5)/fps+.1, min([y2,y4])-.1, max([y1,y3,y5])+0.1]

				# t = np.array(range(len(blue_mean_smooth)))
				# pylab.plot(t, blue_mean_smooth,"-k")
				# pylab.plot(t[lmin], blue_mean_smooth[lmin], "or", label="min")
				# pylab.plot(t[lmax], blue_mean_smooth[lmax], "og", label="max")				
				# pylab.xlabel('frames')
				# axis = [float(x1)-1, float(x5)+1, min([y2,y4])-.1, max([y1,y3,y5])+0.1]

				# pylab.grid(True)
				# pylab.axis(axis)
				# pylab.show()

			if zz:
				# transfer points to z
				z.append((min(min(zz)), max(max(zz))))
			elif z:
				commitZ(z)

		if z:
			commitZ(z)

		if ffs and DEBUG_MODE:
			print 'police presence in %s:' % video_src
		pp = dict()
		pp['police_presence'] = []
		for f1,f2 in ffs:
			pp['police_presence'].append((int(f1),int(f2)))
			if DEBUG_MODE:
				print '%s%02d:%02d->%02d:%02d\033[0m' % (green, f1/fps/60, int(f1/fps) % 60, f2/fps/60, int(f2/fps) % 60)
				if out:
					print '%2.2f->%2.2f\n' % (f1/fps, f2/fps)
				else:
					print '\n'

		content = json.dumps(pp)
		# do not write a file if json parser fails
		if content:
			metadata_filename = './metadata/police_presence/%s.json' % ytid
			# write to disc
			f = open(metadata_filename,'w') 
			f.write(content)
			f.close()

		if show_plot:
			pylab.figure(figsize=(10,10))		
			pylab.suptitle('%s' % video_src, fontsize=16)
			pylab.subplot(1,1,1, title='')
			t = np.linspace(0, num_frames/fps, num_frames)		
			pylab.plot(t, blue_mean_smooth,"-k")  
			pylab.plot(t[lmin], blue_mean_smooth[lmin], "or", label="min")
			pylab.plot(t[lmax], blue_mean_smooth[lmax], "og", label="max")		
			pylab.axis([-1, t[-1]+1, min(blue_mean_smooth) - 1, max(blue_mean_smooth) + 1])
			# x1,x2,y1,y2 = 1, 6, 120, 140
			# axis = [x1, x2, y1,y2]
			# pylab.axis(axis)
			pylab.xlabel('secs.')
			pylab.grid(True)
			pylab.show()

if __name__ == "__main__":
	 main()