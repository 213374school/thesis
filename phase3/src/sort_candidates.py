#!/usr/bin/python

import numpy as np
from labeller import getVideoLength

from segment_db import SegmentDatabase

def findBestRegion(data, minSpan, maxSpan, interval, spanAlpha):

	best = {'start':-1, 'end':-1, 'score':-1}
	for start in range(0,len(data)-minSpan, interval):
		for end in range(start+minSpan,min(start+maxSpan+1,len(data)), interval):

			# Get region data to work on
			regionData = data[start:end]

			# Calculate centricity skewing triangle
			distance_to_center = float(len(regionData))/2
			jump = 0.01/distance_to_center
			firstHalf = np.arange(0.99,1,jump)
			if len(firstHalf) * 2 > len(regionData):
				firstHalf = firstHalf[1:]
			lastHalf = firstHalf[::-1]
			skewTriangle = np.concatenate([firstHalf, lastHalf])

			# What is the score of this region (skewed slightly toward rewarding centricity of high numbers)
			score = float(sum(np.array(regionData)*skewTriangle)) / len(regionData)

			# How much of the possible extra span of the region are we using
			if (maxSpan > minSpan):
				extraSpanPercentage = float(len(regionData) - minSpan) / (maxSpan-minSpan)
			else:
				extraSpanPercentage = 1.0

			# Calculate adjusted score with respect to the spanAlpha
			if score < 0:
				# This region covers an already removed area, make sure it doesnt get added
				finalScore = -2
			else:
				# This region is valid, calculate its score
				finalScore = (1.0-spanAlpha) * score + spanAlpha * extraSpanPercentage

			# Is this score better than our previous best?
			currentBestScore = best.get('score')
			if finalScore > currentBestScore:
				best = {'start':start, 'end':end, 'score':finalScore}
			elif finalScore == currentBestScore:
				currentBestLengt = best.get('end')-best.get('start')
				thisLength = end - start
				if thisLength > currentBestLengt:
					best = {'start':start, 'end':end, 'score':finalScore}

	return best

def createLabelQueryFulfilmentGraph(ytid, query, segment_database, ignore):

	# Disect query
	requestedLabels = query.get('labels')
	requiredLabels = query.get('required')
	forbiddenLabels = query.get('forbidden')

	# Load video and label information
	
	labels = segment_database.get_with_ytid(ytid)
	videoLength = getVideoLength(ytid)

	# Create fulfilment graph
	result = np.zeros(videoLength)
	fulfilmentFraction = 1.0 / len(requestedLabels)
	
	# Handle requested labels
	for label in labels:
		_label = (label.get('l'))[0]
		(start,end) = label.get('s')
		if _label in requestedLabels:
			result[start:end] += fulfilmentFraction

	# Handle forbidden labels
	for label in labels:
		_label = (label.get('l'))[0]
		(start,end) = label.get('s')
		if _label in forbiddenLabels:
			result[start:end] = 0.0

	# Handle required labels
	if len(requiredLabels) > 0:
		requiredLabelsList = np.zeros(videoLength)
		for label in labels:
			_label = (label.get('l'))[0]
			(start,end) = label.get('s')
			if _label in requiredLabels:
				requiredLabelsList[start:end] = 1.0
		result *= requiredLabelsList

	# Handle ignore list
	for segment in ignore:
		# print 'ytid: ', ytid, ' segment: ' , segment
		start = segment[0]
		end = segment[1]
		result[start:end] = -9999999999999999.0

	return result


def sortCandidates(ytids, query, minSpan, maxSpan, interval, spanAlpha, segment_database, ignoreList):

	candidates = []
	for ytid in ytids:

		# Make a list of intervals to ignore for this ytid
		ignore = []
		for segment in ignoreList:
			if segment.get('ytid') == ytid:
				ignore.append((segment.get('start'), segment.get('end')))

		# Create the fulfilment graph for this video
		graph = createLabelQueryFulfilmentGraph(ytid, query, segment_database, ignore)

		# Find the best region in the graph
		resultData = findBestRegion(graph, minSpan, maxSpan, interval, spanAlpha)

		# Append the ytid for bookkeeping
		resultData['ytid'] = ytid

		# Add to the list of candidates
		candidates.append(resultData)

	# Sort the result based on score
	return sorted(candidates, key=lambda x: x['score'], reverse=True) 



def main(argv=None):

	ytids = ['7VsnxMa3SCc', '4J-qtGnNdUk', 'c_BgNo9CmjU', 'F9dptMuUiBA', '0Hwpd-tuD7o', 'fFsAgFx8VzE_part011', 'K-rva3BK3-g']
	query = {'labels': ['is_day', 'is_overview'], 'required': [], 'forbidden': []}
	minSpan = 48
	maxSpan = 120
	interval = 10
	spanAlpha = 0.05
	ignoreList = []
	segment_db = SegmentDatabase()

	result = sortCandidates(ytids, query, minSpan, maxSpan, interval, spanAlpha, segment_db, ignoreList)
	for r in result:

		print 'Video:\t' + str(r.get('ytid'))
		print 'Score:\t' + str(r.get('score'))
		print 'Length:\t' + str(r.get('end')-r.get('start'))
		print ''


if __name__ == '__main__': 
	main()