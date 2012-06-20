#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


import pylab
import numpy as np
import numpy

def triangleSmooth(lst=[], degree=1):

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

def exponentialMovingAvg(lst, days=3):
	if len(lst) >= days and days > 0:
		alpha = 2.0/(days+1) 
		new_list = []
		new_list.append(lst[0])
		for i in range(1,len(lst)):
			today = lst[i] * alpha
			yesterday = new_list[i-1]
			new_list.append(today + (1-alpha) * yesterday)
		return new_list
	else:
		return -1

def calcStd(lst, no_frames=12):

	varianceList = [0] * no_frames
	for i in range(no_frames,len(lst)):
		subList = lst[i-no_frames:i+1]
		varianceList.append(np.std(subList))
	return varianceList


smoothingDegree = 100
data_type = 'mean_vector_length'	# vertical_movement, horizontal_movement, mean_vector_length or brightness

videoFileName = 'gbZl6ULwBTU.m4v'
filepath = '../metadata/final/' + videoFileName + '.json'

f = open(filepath,'r')
metadata = json.loads(f.read())  
f.close()


if data_type == 'brightness':

	splitValue = 50

	dataArray = metadata.get('brightness')
	no_frames = len(dataArray)

	# Plot the data
	pylab.figure(figsize=(10,10))
	pylab.subplot2grid((1,1), (0,0))
	pylab.plot(range(no_frames), dataArray, '-b', linewidth=2.0)
	pylab.axis([0,no_frames,0,255])
else:

	bins = metadata.get(data_type)
	no_frames = len(bins[0])
	maxValue = 0

	# Smooth data in bins
	for i in range(len(bins)):
		stdArray = calcStd(bins[i])
		smoothed = triangleSmooth(stdArray, degree=60)
		bins[i] = smoothed
		stdMax = max(smoothed)
		if stdMax > maxValue:
			maxValue = stdMax
	maxValue = int(maxValue + 1)


	pylab.figure(figsize=(10,10))

	# Plot the data
	for y in [0,1,2]:
		for x in [0,1,2]:
			bin_no = 3 * y + x
			pylab.subplot2grid((3,3), (y,x))
			pylab.plot(range(no_frames), bins[bin_no], '-b', linewidth=2.0)
			pylab.axis([0,no_frames,0,maxValue])


	# Calc the sections where vertical movement happens
	pointers = []
	state = 0
	value_threshold = 5
	no_bin_threshold = 2

	for i in range(no_frames):
		counter = 0
		for bin in bins:
			if bin[i] >= value_threshold:
				counter += 1

		if counter >= no_bin_threshold:
			if state == 0:
				state = 1
				pointers.append(i)
		else:
			if state == 1:
				state = 0
				pointers.append(i)

	state = 0
	for pointer in pointers:
		minute = int(pointer/(24*60))
		if minute > 0:
			second = int((pointer-(minute*24*60))/24)
		else:
			second = int(pointer/24)
		if state == 0:
			state = 1
			print 'begins at %d:%02d' % (minute,second)
		else:
			state = 0
			print 'ends at: %d:%02d' % (minute,second)

pylab.show()