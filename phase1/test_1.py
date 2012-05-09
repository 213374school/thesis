#!/usr/bin/env python

import vid_segmenter as segmenter
import roc
import compute_frame_state
import seg_result_comparison as calcErr
import sys
import cv
import cv2
import numpy as np
import math
import os
import json
import pylab
from common import draw_str

smoothTriangle = segmenter.smoothTriangle
getVideoMetadata = segmenter.getVideoMetadata
computeFrameStateAnders = compute_frame_state.computeFrameStateAnders
computeFrameStateLauge = compute_frame_state.computeFrameStateLauge
computeFrameStateNaiive = compute_frame_state.computeFrameStateNaiive
computeFrameStateMagnitudeOnly = compute_frame_state.computeFrameStateMagnitudeOnly
computeFrameStateContrastOnly = compute_frame_state.computeFrameStateContrastOnly

help_message = '''
USAGE: test_1.py <'lauge', 'anders' 'naiive', 'magnitude' or 'contrast'> <metadata dir> <answer dir (if any)>'''

def main():

	# Degree of smoothness (doesnt matter very much)
	degree = 12

	metadataDir = None

	try:
		arg1 = sys.argv[1]
		if arg1 == '-?':
			print help_message
			return
		
		metadataDir = sys.argv[2]
		if len(sys.argv) == 4:
			answerDir = sys.argv[3]
		else:
			answerDir = None
	except:		
		print help_message
		return

	f = open('./DataSet/ignore.json','r')
	content = f.read()
	ignore = json.loads(content).get('ignore')

	listOfMetaDataFiles = os.listdir(metadataDir)
	
	errors = []
	for metaDataFile in listOfMetaDataFiles:

		# Get video ID
		thisID = metaDataFile.split('.')[0]

		if thisID in ignore:
			continue

		# Get metadata file for video
		metadata_filename = metadataDir + '/' + thisID + '.m4v_metadata.txt'
		metadata_exists = os.path.isfile(metadata_filename)

		if answerDir:
			answer_filename = answerDir + '/' + thisID + '.m4v.txt'
			answer_exists = os.path.isfile(answer_filename)
		else:
			answer_filename = None
			answer_exists = None

		if (metadata_exists and answer_exists) or (metadata_exists and not answerDir):

			# Read metadata file
			f = open(metadata_filename,'r')
			content = f.read()
			metadata = json.loads(content)
			d = metadata
			f.close()

			shift_vectors = d['shift_vectors']
			# rmsdiffs = d['rmsdiffs']
			# shift_vectors_sliding = d['shift_vectors_sliding']
			stand_dev = d['stand_dev']
			
			# Smooth the data (doesnt matter very much)
			magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
			contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
			
			# Calculate/guess frame states
			if arg1 == 'anders':
				frame_states, frame_values = computeFrameStateAnders(magnitudes, contrast)
			elif arg1 == 'lauge':
				frame_states, frame_values = computeFrameStateLauge(magnitudes, contrast)
			elif arg1 == 'naiive':
				frame_states, frame_values = computeFrameStateNaiive(magnitudes, contrast)
			elif arg1 == 'magnitude':
				frame_states, frame_values = computeFrameStateMagnitudeOnly(magnitudes)
			elif arg1 == 'contrast':
				frame_states, frame_values = computeFrameStateContrastOnly(contrast)
			else:
				return


			# Was an answer directory supplied by the user
			if answerDir is not None:
				
				if answer_exists:
					f = open(answer_filename,'r')
					content = f.read()
					answer_data = json.loads(content)
					f.close()
					answer_states = answer_data.get('states')

					# Calculate error
					errors.append(calcErr.simpleCompare(frame_states, answer_states))
			else:
				# No! Assume that all frames should be GOOD
				errors.append(calcErr.simpleCompare(frame_states))

	totals = 0
	totalPositives = 0
	totalNegatives = 0
	corrects = 0
	truePositives = 0
	trueNegatives = 0
	falsePositives = 0
	falseNegatives = 0
	
	for error in errors:

		totals += int(error.get('total'))
		totalPositives += int(error.get('total positives'))
		totalNegatives += int(error.get('total negatives'))

		corrects += error.get('correct')

		truePositives += error.get('true positives')
		trueNegatives += error.get('true negatives')
		falsePositives += error.get('false positives')
		falseNegatives += error.get('false negatives')

	correctsRatio = float(corrects)/totals
	try:
		positivePrecision = float(truePositives) / (truePositives + falsePositives)
	except:
		positivePrecision = -1
	try:
		positiveRecall = float(truePositives) / totalPositives
	except:
		positiveRecall = -1
	try:
		negativePrecision = float(trueNegatives) / (trueNegatives + falseNegatives)
	except:
		negativePrecision = -1
	try:
		negativeRecall = float(trueNegatives) / totalNegatives
	except:
		negativeRecall = -1

	
	print '\nOverall accuracy: %2.3f%%' % (100.0 * correctsRatio)
	if positivePrecision >= 0:
		print 'Positive precision: %2.3f%%' % (100.0 * positivePrecision)
	else:
		print 'Positive precision: NOT DEFINED'
	if positiveRecall >= 0:
		print 'Positive recall: %2.3f%%' % (100.0 * positiveRecall)
	else:
		print 'Positive recall: NOT DEFINED'
	if negativePrecision >= 0:
		print 'Negative precision: %2.3f%%' % (100.0 * negativePrecision)
	else:
		print 'Negative precision: NOT DEFINED'
	if negativeRecall >= 0:
		print 'Negative recall: %2.3f%%' % (100.0 * negativeRecall)
	else:
		print 'Negative recall: NOT DEFINED'



if __name__ == '__main__':
    main()