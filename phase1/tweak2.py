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

	def __init__(self, method, path='./Tweakfinal/', smoothness_degree=0, videoIDs=[], compare_method=calcErr.simpleCompare, tolerance=None):

		self.method = method
		self.path = path
		self.smoothness_degree = smoothness_degree
		self.metadatas = []
		self.answer_datas = []
		self.videoIDs = videoIDs
		self.compare_method = compare_method
		self.tolerance = tolerance

		self.init()

	def init(self):

		path = self.path

		if not self.videoIDs:
			videoIDs = []
			listOfMetaDataFiles = os.listdir(path)
			for metaDataFile in listOfMetaDataFiles:
				parts = metaDataFile.split('.')
				ID = parts[0]
				kind = parts[1]
				if kind == 'm4v_metadata':
					videoIDs.append(ID)
		else:
			videoIDs = self.videoIDs
			self.videoIDs = []

		f = open('./DataSet/ignore.json','r')
		content = f.read()
		ignore = json.loads(content).get('ignore')

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
				metadata['yt_id'] = thisID
				self.metadatas.append(metadata)
				f.close()
			else:
				print 'metadata for %s does not exist' % thisID
				continue

			if answer_exists:
				f = open(answer_filename,'r')
				content = f.read()
				answer_data = json.loads(content)
				f.close()
			else:
				answer_data = dict(states=[1 for x in metadata.get('shift_vectors')])
			self.answer_datas.append(answer_data)
			self.videoIDs.append(thisID)

	def tweak(self, p):

		errors = []

		for i in range(len(self.metadatas)):

			metadata = self.metadatas[i]
			answer_data = self.answer_datas[i]
			method = self.method
			videoID = self.videoIDs[i]

			shift_vectors = metadata['shift_vectors']
			stand_dev = metadata['stand_dev']

			# degree of smoothness
			degree = 12

			out_filename = '%s.%s.smoo%d.txt' % (videoID, str(p), self.smoothness_degree)
			path = './DataSet/frame_states/%s' % (method.__name__)
			out_filename = '%s/%s' % (path, out_filename)

			if os.path.isfile(out_filename):
				f = open(out_filename,'r')
				content = f.read()
				d = json.loads(content)	
				frame_states = d.get('frame_states', [])
				frame_values = d.get('frame_values', [])
			else:
				print 'computing data for video ID %s, method %s, parameter %s, smoothness: %d' % (videoID, method.__name__, str(p), self.smoothness_degree)
				try:
					magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
					contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
				except IndexError as e:
					# too little data in segment will cause this error
					continue
				
				frame_states, frame_values = method(magnitudes, contrast, p)

				smoothness_degree = self.smoothness_degree
				if smoothness_degree:
					frame_states = [round(x) for x in smoothTriangle(frame_states, smoothness_degree)]

				content = json.dumps(dict(frame_states=frame_states, frame_values=frame_values))
				# write to disc
				f = open(out_filename,'w')	
				f.write(content)
				f.close()

			answer_states = answer_data.get('states')

			# Calculate error
			errors.append(self.compare_method(frame_states, answer_states, tolerance=self.tolerance))

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

		return truePositives, falsePositives, trueNegatives, falseNegatives

	def fold(self, buckets=5, debug_mode=False):

		metadatas_sorted = sorted(self.metadatas, key=lambda x: len(x['shift_vectors']))
		# for metadata in metadatas_sorted: print len(metadata['shift_vectors'])
		if debug_mode:
			for metadata in metadatas_sorted: print '#frames: ', len(metadata['shift_vectors'])
		# inspired by: http://code.activestate.com/recipes/439095-iterator-to-return-items-n-at-a-time/
		def group(iterator, count):
			itr = iter(iterator)
			stop = False
			while not stop:
				l = []
				for i in range(count):
					try:
						next = itr.next()
					except StopIteration:
						# no further items, return what is left
						stop = True
						break
					else:
						l.append(next)
				if l:
					yield tuple(l)

		x1 = []
		x2 = []
		x3 = []
		x4 = []
		x5 = []
		for x in list(group(metadatas_sorted, 5)):
			try:
				if debug_mode: 
					print 'adding %d frames to x1' % len(x[0].get('shift_vectors'))
				x1.append(x[0].get('yt_id'))
				if debug_mode: 
					print 'adding %d frames to x2' % len(x[1].get('shift_vectors'))
				x2.append(x[1].get('yt_id'))
				if debug_mode: 
					print 'adding %d frames to x3' % len(x[2].get('shift_vectors'))
				x3.append(x[2].get('yt_id'))
				if debug_mode: 
					print 'adding %d frames to x4' % len(x[3].get('shift_vectors'))
				x4.append(x[3].get('yt_id'))
				if debug_mode: 
					print 'adding %d frames to x5' % len(x[4].get('shift_vectors'))
				x5.append(x[4].get('yt_id'))
			except IndexError, e:
				pass

		# def get_num_frames(x):
		# 	z = 0
		# 	return sum([len(y.get('shift_vectors')) for y in x])

		# print '1: %6d frames\n2: %6d frames\n3: %6d frames\n4: %6d frames\n5: %6d frames\n' % (get_num_frames(x1), get_num_frames(x2), get_num_frames(x3), get_num_frames(x4), get_num_frames(x5))
		
		return x1,x2,x3,x4,x5

def main():
	
	tweak = Tweak(method=None)
	x1,x2,x3,x4,x5 = tweak.fold(debug_mode=False)
	print x1,x2,x3,x4,x5
	print len(x1+x2+x3+x4+x5)

if __name__ == '__main__':
    main()
