import numpy as np
import os
import json
from labeller_anders import *


# FUNCTIONS FOR DOING VARIOUS KINDS OF DATA PROCESSING

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

def distXY(x,y):
	res = np.sqrt(np.sum((np.linalg.norm(x)-np.linalg.norm(y))**2))    
	return res




# FUNCTIONS FOR RETRIEVING METADATA

def getSVM(ytid):
	metadata = loadPhase1MetaData(ytid)
	shiftVectors = metadata.get('shift_vectors')
	return [distXY((0,0),(x,y)) for [x,y] in shiftVectors]

def getContrast(ytid):
	metadata = loadPhase1MetaData(ytid)
	return metadata.get('stand_dev')

def getBrightness(ytid):
	metadata = loadFinalMetadata(ytid)
	return metadata.get('brightness')

def getVerticalMovement(ytid):
	metadata = loadFinalMetadata(ytid)
	return metadata.get('vertical_movement')

def getMeanVectorLength(ytid):
	metadata = loadFinalMetadata(ytid)
	return metadata.get('mean_vector_length')


def loadFinalMetadata(ytid):
	
	# Get metadata
	filepath = os.path.dirname(os.path.realpath(__file__)) + '/../metadata/' + ytid + '.json'
	if os.path.isfile(filepath):
		f = open(filepath, 'r+')
		return json.loads(f.read())
	else:
		raise Exception('Metadata file: "%s", does not exist.' % filepath)

def loadPhase1MetaData(ytid):

	return (loadFinalMetadata(ytid)).get('phase1')

	filepath = os.path.dirname(os.path.realpath(__file__)) + '/../../phase1/DataSet/Metadata/' + ytid + '_metadata.txt'
	if os.path.isfile(filepath):
		f = open(filepath, 'r+')
		return json.loads(f.read())
	else:
		print 'Metadata file: \'%d\', doesnt exist.' % filepath
		return




# THE ACTUAL LABELERS

def isDayLabeller(ytid):

	threshold = 60
	ratio = 0.2

	brightness = getBrightness(ytid)
	blueness = getBlueChannelMean(ytid)

	# Make sure both have same length
	length = min(len(brightness), len(blueness))
	brightness = brightness[0:length]
	blueness = blueness[0:length]

	(brightnessHist, tmp) = np.histogram(brightness, range=(0,255))
	(bluenessHist, tmp) = np.histogram(blueness, range=(0,255))

	brightnessHist = [float(h) / sum(brightnessHist) for h in brightnessHist]
	bluenessHist = [float(h) / sum(bluenessHist) for h in bluenessHist]

	corrolation = (np.array(np.float32(blueness))/np.array(brightness)) - 1

	print np.mean(corrolation)
	print brightnessHist

	if np.mean(corrolation) > 0 or sum(brightnessHist[0:4]) < sum(brightnessHist[4:]):
		return [(0,len(brightness))]
	else:
		return []

def isNightLabeller(ytid):

	if len(isDayLabeller(ytid)) == 0:
		brightness = getBrightness(ytid)
		return [(0,len(brightness))]
	else:
		return []

def verticalOscillationLabeller(ytid):

	value_threshold = 5
	no_bin_threshold = 2
	std_width = 12
	triangle_smoothing_width = 60

	bins = getVerticalMovement(ytid)
	no_frames = len(bins[0])

	# Calculate smoothed standard deviations of the data in the bins
	for i in range(len(bins)):
		stdArray = calcStd(bins[i], std_width)
		smoothed = triangleSmooth(stdArray, degree=triangle_smoothing_width)
		bins[i] = smoothed

	# Calc sections
	startPointers = []
	endPointers = []
	state = 0
	for i in range(no_frames):
		counter = 0
		for bin in bins:
			if bin[i] >= value_threshold:
				counter += 1

		if counter >= no_bin_threshold:
			if state == 0:
				state = 1
				startPointers.append(i)
		else:
			if state == 1:
				state = 0
				endPointers.append(i)

	if not len(startPointers) == len(endPointers):
		endPointers.append(no_frames)

	return zip(startPointers, endPointers)

def isOverviewLabeller(ytid):

	flow_threshold = 2
	no_bin_threshold = 7

	svm_threshold = 10
	triangle_smoothing_width = 60

	bins = getMeanVectorLength(ytid)
	svms = getSVM(ytid)
	person_in_focus = getPersonInFocus(ytid)
	no_frames = min([len(bins[0]), len(svms), len(person_in_focus)])


	# Smooth the data
	svms = triangleSmooth(svms, degree=triangle_smoothing_width)
	for i in range(len(bins)):
		smoothed = triangleSmooth(bins[i], degree=triangle_smoothing_width)
		bins[i] = smoothed

	# Calc sections
	startPointers = []
	endPointers = []
	state = 0
	for i in range(no_frames):
		
		counter = 0
		for bin in bins:
			if bin[i] <= flow_threshold:
				counter += 1

		if counter >= no_bin_threshold and svms[i] < svm_threshold and not person_in_focus[i]:
			if state == 0:
				state = 1
				startPointers.append(i)
		else:
			if state == 1:
				state = 0
				endPointers.append(i)

	if not len(startPointers) == len(endPointers):
		endPointers.append(no_frames)

	return zip(startPointers, endPointers)