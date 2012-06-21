#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import json
from time import clock
import os
import json
import video
import cv2
from common import draw_str

from labeller_lauge import getSVM
from labeller_lauge import getContrast

from labeller_lauge import isDayLabeller
from labeller_lauge import isNightLabeller
from labeller_lauge import verticalOscillationLabeller
from labeller_lauge import isOverviewLabeller


from labeller_anders import getPeopleInFrame
from labeller_anders import getPersonInFocus
from labeller_anders import getBlueChannelMean

from labeller_anders import hasPolicePresenceLabeller
from labeller_anders import hasPersonInFocusLabeller



help_message = '''
USAGE: labeller.py [<video_source>] [<labelling_to_do>]
<labelling_to_do> options:
is_day
is_night
vertical_oscillation
is_overview
is_in_crowd
has_police
has_person_in_focus
'''


def triangleSmooth(lst=[], degree=1):

	if degree < 1:
		print 'degree must be > 1'
		return

	triangle = np.array(range(degree)+[degree]+range(degree)[::-1])+1
	lst = np.array(lst)
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

def calcStd(lst, no_frames=12):

	varianceList = [0] * no_frames
	for i in range(no_frames,len(lst)):
		subList = lst[i-no_frames:i+1]
		varianceList.append(np.std(subList))
	return varianceList


def isInCrowdLabeller(ytid):
	return []



def main():
	import sys
	print help_message
	try:
		video_src = sys.argv[1]
		label = sys.argv[2]
	except:
		return

	ytid = (video_src.split('/'))[-1]
	
	if label == 'is_day':
		intervals = isDayLabeller(ytid)
	elif label == 'is_night':
		intervals = isNightLabeller(ytid)
	elif label == 'vertical_oscillation':
		intervals = verticalOscillationLabeller(ytid)
	elif label == 'is_overview':
		intervals = isOverviewLabeller(ytid)
	elif label == 'is_in_crowd':
		intervals = isInCrowdLabeller(ytid)
	elif label == 'has_police':
		intervals == hasPolicePresenceLabeller(ytid)
	elif label == 'has_person_in_focus':
		intervals == hasPersonInFocusLabeller(ytid)
	else:
		intervals = []


	print 'RESULTS:'
	for interval in intervals:
		humanReadable = []
		for i in range(2):
			pointer = interval[i]
			minute = int(pointer/(24*60))
			if minute > 0:
				second = int((pointer-(minute*24*60))/24)
			else:
				second = int(pointer/24)
			humanReadable.append('%d:%02d' % (minute,second))

		print '%s to %s' % (humanReadable[0], humanReadable[1])


	frame_list = []
	for (start, end) in intervals:
		for i in range(start, end):
			frame_list.append(i)

	cam = video.create_capture(video_src)
	i = 0
	while True:
		
		if i in frame_list:
			status = label
			wait = 1000/24
		else:
			status = ''
			wait = 1000/72

		try:
			ret, frame = cam.read()
			cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_PLAIN, 2.0, (0, 255, 0), thickness = 2)
			cv2.imshow('lk_track', frame)
			ch = cv2.waitKey(wait)
			if ch == 27:
				break
		except:
			break

		i += 1

if __name__ == '__main__':
	main()