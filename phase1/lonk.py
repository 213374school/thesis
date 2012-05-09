#!/usr/bin/env python

import seg_result_comparison as calcErr
import numpy as np
import math
import os
import json
import pylab
import vid_segmenter as segmenter
import os
smoothTriangle = segmenter.smoothTriangle
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

class Tweak():

	def __init__(self, path='./Anders/', sug_path='./Lauge/'):

		self.path = path
		self.sug_path = sug_path
		self.answer_datas = []
		self.suggestion_datas = []

		self.init()

	def init(self):

		listOfAnswerFiles = os.listdir(self.path)
		listOfSuggestionFiles = os.listdir(self.sug_path)
		
		videoIDs_ans = []
		videoIDs_sug = []
		
		for _file in listOfAnswerFiles:
			parts = _file.split('.')
			ID = parts[0]
			try:
				if parts[1] == 'm4v' and parts[2] == 'txt':
					videoIDs_ans.append(ID)
			except Exception, e:
				pass
		
		for _file in listOfSuggestionFiles:
			parts = _file.split('.')
			ID = parts[0]
			try:
				if parts[1] == 'm4v' and parts[2] == 'txt':
					videoIDs_sug.append(ID)
			except Exception, e:
				pass				

		f = open('./DataSet/ignore.json','r')
		content = f.read()
		ignore = json.loads(content).get('ignore')

		for thisID in videoIDs_ans:
			# print thisID
			if thisID in ignore:
				# print 'ignoring data in %s' % thisID
				continue
			if thisID in videoIDs_sug:
				answer_filename = self.path + thisID + '.m4v.txt'

				if not os.path.isfile(answer_filename):
					print 'ERROR!!!'
				else:
					f = open(answer_filename,'r')
					content = f.read()
					answer_data = json.loads(content)
					f.close()

				self.answer_datas.append(answer_data)

		for thisID in videoIDs_sug:
			# print thisID
			if thisID in ignore:
				# print 'ignoring data in %s' % thisID
				continue
			if thisID in videoIDs_ans:
				sugg_filename = self.sug_path + thisID + '.m4v.txt'

				if not os.path.isfile(sugg_filename):
					print 'error, %s does not exist' % sugg_filename
				else:
					f = open(sugg_filename,'r')
					content = f.read()
					sugg_data = json.loads(content)
					f.close()

					self.suggestion_datas.append(sugg_data)

		print len(self.suggestion_datas), len(self.answer_datas)

	def tweak(self):

		errors = []

		for i in range(len(self.answer_datas)):

			# metadata = self.metadatas[i]
			answer_data = self.answer_datas[i]
			sugg_data = self.suggestion_datas[i]

			answer_states = answer_data.get('states')
			frame_states = sugg_data.get('states')
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
		
		return truePositives, falsePositives, trueNegatives, falseNegatives

def main():
	
	tweak = Tweak()
	truePositives, falsePositives, trueNegatives, falseNegatives = tweak.tweak()
	# print 'true pos. %d, false pos. %d, true negs. %d, false negs %d' % (truePositives, falsePositives, trueNegatives, falseNegatives)
	

if __name__ == '__main__':
    main()
