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


help_message = '''
USAGE: labeller.py [<video_source>] [<labelling_to_do>]
<labelling_to_do> options:
is_day
is_night
'''


def isDayLabeller(metadata):

	threshold = 50

	data = metadata.get('brightness')
	if np.mean(data) >= threshold:
		return [(0,len(data))]
	else:
		return []

def isNightLabeller(metadata):

	threshold = 50

	data = metadata.get('brightness')
	if np.mean(data) < threshold:
		return [(0,len(data))]
	else:
		return []


def main():
	import sys
	print help_message
	try:
		video_src = sys.argv[1]
		label = sys.argv[2]
	except:
		return

	# Get metadata
	videoFileName = (video_src.split('/'))[-1]
	filepath = '../metadata/final/' + videoFileName + '.json'
	if os.path.isfile(filepath):
		f = open(filepath, 'r+')
		metadata = json.loads(f.read())
	else:
		print 'Metadata file: \'%d\', doesnt exist.' % filepath
		return

	if label == 'is_day':
		intervals = isDayLabeller(metadata)
	elif label == 'is_night':
		intervals = isNightLabeller(metadata)
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

if __name__ == '__main__':
	main()