#!/usr/bin/python

import numpy as np
from lbl_db_intf import _get_with_ytid
from labeller import getVideoLength

def findBestRegion(data, minSpan, maxSpan, interval, spanAlpha):

	best = {'start':-1, 'end':-1, 'score':-1}
	for start in range(0,len(data)-minSpan, interval):

		# Only start from here if it makes sense to do so (span and value-wise)
		# IMPORTANT: THIS CHECK MUST BE UPDATED TO SUPPORT REMOVAL OF REGIONS (if they have already been used in the clip)
		if data[start] > 0 and start < len(data)-maxSpan:
			for end in range(start+minSpan,min(start+maxSpan+1,len(data)), interval):

				# Get region data to work on
				regionData = data[start:end]

				# What is the score of this region
				score = float(sum(regionData)) / len(regionData)

				# How much of the possible extra span of the region are we using
				if (maxSpan > minSpan):
					extraSpanPercentage = float(len(regionData) - minSpan) / (maxSpan-minSpan)
				else:
					extraSpanPercentage = 1.0

				# Calculate adjusted score with respect to the spanAlpha
				finalScore = (1.0-spanAlpha) * score + spanAlpha * extraSpanPercentage

				# Is this score better than our previous best?
				currentBestScore = best.get('score')
				if finalScore > currentBestScore:
					best = {'start':start, 'end':end, 'score':finalScore}
				elif finalScore == currentBestScore:
					currentBestLengt = best.get('end')-best.get('start')
					thisLength = end - start
					if thisLength > currentBestScore:
						best = {'start':start, 'end':end, 'score':finalScore}

	return best

def createLabelQueryFulfilmentGraph(ytid, query):

	# Disect query
	requestedLabels = query.get('labels')
	requiredLabels = query.get('required')
	forbiddenLabels = query.get('forbidden')

	# Load video and label information
	labels = _get_with_ytid(ytid)
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

	return result


def sortCandidates(ytids, query, minSpan, maxSpan, interval, spanAlpha):

	candidates = []
	for ytid in ytids:

		# Create teh fulfilment graph for this video
		graph = createLabelQueryFulfilmentGraph(ytid, query)

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
	query = {'labels': ['vertical_oscillation'], 'required': [], 'forbidden': []}
	minSpan = 48
	maxSpan = 120
	interval = 10
	spanAlpha = 0.05

	result = sortCandidates(ytids, query, minSpan, maxSpan, interval, spanAlpha)
	for r in result:

		print 'Video:\t' + str(r.get('ytid'))
		print 'Score:\t' + str(r.get('score'))
		print 'Length:\t' + str(r.get('end')-r.get('start'))
		print ''


if __name__ == '__main__': 
	main()