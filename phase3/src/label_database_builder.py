#!/usr/bin/env python
# -*- coding: utf-8 -*-

from labeller import *
import os
import json

def main():
	
	database = []

	# Go through all videos in all buckets
	for bucket in ['core1', 'core2', 'core3', 'core4']:

		# Generate directory path
		dirpath = os.path.dirname(os.path.realpath(__file__)) + '/../data/' + bucket + '/'

		# Generate list of files
		dirList=os.listdir(dirpath)
		for fname in dirList:
			if not fname == '.DS_Store':
				ytid = (fname.split('.'))[0]
				print 'GENERATING LABELS FOR VIDEO: ' + ytid

				for label in ['is_day', 'is_night', 'vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']:
					
					if label == 'is_day':
						intervals = isDayLabeller(ytid)
					elif label == 'is_night':
						intervals = isNightLabeller(ytid)
					elif label == 'vertical_oscillation':
						intervals = verticalOscillationLabeller(ytid)
					elif label == 'is_overview':
						intervals = isOverviewLabeller(ytid)
					elif label == 'is_in_crowd':
						intervals, labels = isInCrowdLabeller(ytid)
					elif label in 'has_police':
						intervals = hasPolicePresenceLabeller(ytid)
						print intervals
					elif label in 'has_person_in_focus':
						intervals = hasPersonInFocusLabeller(ytid)
					else:
						print 'INVALID LABEL: ' + label
						return

					for (start,end) in intervals:

						segment = {'ytid': ytid, 's':(start,end), 'l':label}
						database.append(segment)

	f = open('database.json','w')
	f.write(json.dumps(database))
	f.close()


						

if __name__ == '__main__':
	main()