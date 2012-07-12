#!/usr/bin/env python
# -*- coding: utf-8 -*-

from labeller import *
import os
import json

def main():
	
	daywrong = []
	nightwrong = []
	counter = 0

	# Go through all videos in all buckets
	for bucket in ['core1', 'core2', 'core3', 'core4']:

		# Generate directory path
		dirpath = os.path.dirname(os.path.realpath(__file__)) + '/../data/' + bucket + '/'

		# Generate list of files
		dirList=os.listdir(dirpath)
		for fname in dirList:
			if not fname == '.DS_Store':
				counter += 1
				ytid = (fname.split('.'))[0]
				
				intervals = isDayLabeller(ytid)

				if not len(intervals) > 0 and bucket == 'core2':
					nightwrong.append(ytid)
				if len(intervals) > 0 and bucket == 'core3':
					daywrong.append(ytid)

	wrong = daywrong + nightwrong
	print '%d wrong out of %d total' % (len(wrong), counter)
	print 'Wrong night (should be day):' 
	for w in nightwrong:
		print w
	print 'Wrong day (should be night):' 
	for w in daywrong:
		print w

if __name__ == '__main__':
	main()