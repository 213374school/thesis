#!/usr/bin/env python

import vid_segmenter as segmenter
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
computeFrameStateAnders2 = compute_frame_state.computeFrameStateAnders2
computeFrameStateSquare = compute_frame_state.computeFrameStateSquare
computeFrameStateCubic = compute_frame_state.computeFrameStateCubic
computeFrameStateLauge = compute_frame_state.computeFrameStateLauge
computeFrameStateNaiive = compute_frame_state.computeFrameStateNaiive
computeFrameStateMagnitudeOnly = compute_frame_state.computeFrameStateMagnitudeOnly
computeFrameStateContrastOnly = compute_frame_state.computeFrameStateContrastOnly

help_message = '''
USAGE: tweak.py <'lauge', 'anders' 'naiive', 'magnitude', 'contrast'>'''

def main():

	path = './Tweak/'

	videoIDs = []
	listOfMetaDataFiles = os.listdir(path)
	for metaDataFile in listOfMetaDataFiles:
		parts = metaDataFile.split('.')
		ID = parts[0]
		kind = parts[1]
		if kind == 'm4v_metadata':
			videoIDs.append(ID)

	try:
		arg1 = sys.argv[1]
		if arg1 == '-?':
			print help_message
			return
	except:		
		print help_message
		return

	f = open('./DataSet/ignore.json','r')
	content = f.read()
	ignore = json.loads(content).get('ignore')

	errors = []
	for thisID in videoIDs:
		# print thisID
		if thisID in ignore:
			# print 'ignoring data in %s' % thisID
			continue

		# uncomment to only use "cut" segments
		# if 'part' not in thisID:
		# 	continue

		metadata_filename = path + thisID + '.m4v_metadata.txt'
		answer_filename = path + thisID + '.m4v.txt'
		metadata_exists = os.path.isfile(metadata_filename)
		answer_exists = os.path.isfile(answer_filename)

		if not metadata_exists:
			print 'Metadata for ' + thisID + ' does not exists'
		# if there is no answer file and the filename does not have 'part' in it
		# it is likely missing. otherwise we will create one
		if not answer_exists and ('part' not in thisID):
			print 'Answer-file for ' + thisID + ' does not exists'

		# if metadata_exists and answer_exists:
		if metadata_exists:

			f = open(metadata_filename,'r')
			content = f.read()
			metadata = json.loads(content)
			d = metadata
			f.close()

			if answer_exists:
				f = open(answer_filename,'r')
				content = f.read()
				answer_data = json.loads(content)
				f.close()
			else:
				answer_data = dict(states=[1 for x in metadata.get('shift_vectors')])

			shift_vectors = d['shift_vectors']
			# rmsdiffs = d['rmsdiffs']
			# shift_vectors_sliding = d['shift_vectors_sliding']
			stand_dev = d['stand_dev']

			# degree of smoothness
			degree = 12
			
			try:
				magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
				contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
			except IndexError as e:
				# too little data in segment will cause this error
				continue
			
			# compute if a frame is accepted, and the according value
			if arg1 == 'anders':
				frame_states, frame_values = computeFrameStateAnders(magnitudes, contrast)
			elif arg1 == 'anders2':
				frame_states, frame_values = computeFrameStateAnders2(magnitudes, contrast)				
			elif arg1 == 'square':
				frame_states, frame_values = computeFrameStateSquare(magnitudes, contrast)
			elif arg1 == 'cubic':
				frame_states, frame_values = computeFrameStateCubic(magnitudes, contrast)
			# elif arg1 == 'algox':
			# 	frame_states, frame_values = computeFrameStateX(magnitudes, contrast, 5.0, 0.7)
			elif arg1 == 'lauge':
				frame_states, frame_values = computeFrameStateLauge(magnitudes, contrast, (0.01,0.75))
			elif arg1 == 'naiive':
				frame_states, frame_values = computeFrameStateNaiive(magnitudes, contrast)
			elif arg1 == 'magnitude':
				frame_states, frame_values = computeFrameStateMagnitudeOnly(magnitudes)
			elif arg1 == 'contrast':
				frame_states, frame_values = computeFrameStateContrastOnly(contrast)
			else:
				return

			answer_states = answer_data.get('states')

			# Calculate error
			errors.append(calcErr.simpleCompare(frame_states, answer_states))

	

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