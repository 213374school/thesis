#!/usr/bin/env python
# -*- coding: utf-8 -*-

# input (label, min_segment_length)*, sort_order 
# sort_order: #labels;segment_length -> sort first by #labels present in a segment, break ties with segment_length
# output: listen er sorteret efter "sort_order". hvis input er 2 labels vil output indeholde op til 3 permuationer af segmenter, 
# en hvor første label er present i segmentet, en hvor anden label er present i segmentet, og en hvor begge labels er present i samme segment. 
# på denne måde smides intet væk (og det umiddelbart mest relevante er at finde forrest i listen).

import json
import random
import cProfile
try:
	import cv
	import cv2
	from common import draw_str
except Exception as e:
	print e
from segment_db import SegmentDatabase
from sort_candidates import sortCandidates
from collections import *

LABELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

def is_overlapping(a,b):

	return max(a.get('s')[0],b.get('s')[0]) < min(a.get('s')[1],b.get('s')[1])

def get_segment_len(x):
	
	return x.get('s')[1] - x.get('s')[0]

def get_overlap(a,b):

	segment = (max(a.get('s')[0],b.get('s')[0]), min(a.get('s')[1],b.get('s')[1]))
	labels = sorted(a.get('l') + b.get('l'))
	ytid = a.get('ytid')
	return dict(s=segment, l=labels, ytid=ytid)

def _has_ytid(ytid, item):

	return item.get('ytid') == ytid

class CandidateFactory:

	def __init__(self, segment_database):
		self.db = segment_database
		self.candidates = []

	def get_overlapping_segments(self, labels, min_segment_length=6):

		# check if labels from a is present in labels from b
		def f(a,b):
			for l in a.get('l'):
				if l in b.get('l'):
					return False
			return True

		candidates = self.candidates
		# compute candidates based on input candidates. then reiterate new candidates to produce even more
		for x in range(len(labels)-1):
			# copy the current candidates
			_candidates = list(candidates)
			# optimized loops
			for i in range(len(_candidates)):
				a = _candidates[i]
				for j in range(i+1, len(_candidates)):
					b = _candidates[j]
					# assert(a!=b)
					if a.get('ytid') == b.get('ytid') and is_overlapping(a,b) and f(a,b):
						c = get_overlap(a,b)
						# avoid duplicates and too short segments - the larger "candidates", the longer it takes to validate
						# duplicates will occur if we produce candidates with more than 2 labels
						if get_segment_len(c) > min_segment_length and c not in candidates:
							candidates.append(c)
			# possible optimization is to filter out candidates with only 1 label (need to do this only once)

	def sort(self):

		# Starting with Python 2.2, sorts are guaranteed to be stable. That means that when multiple records have the same key, their original order is preserved.
		self.candidates = sorted(self.candidates, key=lambda x: x.get('ytid'), reverse=True)
		self.candidates = sorted(self.candidates, key=lambda x: get_segment_len(x), reverse=True)
		self.candidates = sorted(self.candidates, key=lambda x: len(x['l']), reverse=True)

	def get_candidates(self, labels):

		for label in labels:
			self.candidates += self.db.get_with_label(label)

		self.get_overlapping_segments(labels)
		self.sort()
		return self.candidates

	def seg_len_filter(self, min_len, max_len):

		candidates = self.candidates
		if min_len > 0:
			candidates = filter(lambda x: get_segment_len(x) > min_len, candidates)
		if max_len > 0:
			candidates = filter(lambda x: get_segment_len(x) < max_len, candidates)

	def label_filter(self, labels=[], excl_labels=[]):

		candidates = self.candidates
		for label in labels:
			candidates = filter(lambda x: label in x.get('l'), candidates)
		for label in excl_labels:
			candidates = filter(lambda x: label not in x.get('l'), candidates)

	def get_ytids(self, lim=-1):

		ytids = [candidate.get('ytid') for candidate in self.candidates]

		d = defaultdict(lambda: 0)
		# count the number of occurences of each candidate
		for c in ytids: d[c] += 1
		# sort by the number of occurences (largest first)
		d = sorted(d.items(), key=lambda (x,y): y, reverse=True)
		if lim > 0:
			d = d[:lim]
		# and finally the new list of ytids
		ytids = [x for (x,y) in d]
		# print 'get_ytids(...): ', ytids

		return ytids

		# hella lot better than:
		# return list(set([candidate.get('ytid') for candidate in self.candidates]))

def get_capture(ytid):

	video_src = 'data/%s.m4v' % ytid
	try:
		cap = cv2.VideoCapture(video_src)
	except:
		video_src = 'data/%s.avi' % ytid
		cap = cv2.VideoCapture(video_src)
	return cap

def get_num_frames(cap):

	return cap.get(cv.CV_CAP_PROP_FRAME_COUNT)

def get_fps(cap):

	return cap.get(cv.CV_CAP_PROP_FPS)

class Ingredient:

	def __init__(self, labels, min_span=48, max_span=120, interval=10, span_alpha=0.05, required_labels=[], forbidden_labels=[]):
		self.labels = labels
		self.min_span = min_span
		self.max_span = max_span
		self.interval = interval
		self.span_alpha = span_alpha
		self.required_labels = required_labels
		self.forbidden_labels = forbidden_labels

	def __str__(self):

		return 'labels=%s, min_span=%d, max_span=%d, interval=%d, span_alpha=%f, required_labels=%s, forbidden_labels=%s' % (self.labels, self.min_span, self.max_span, self.interval, self.span_alpha, self.required_labels, self.forbidden_labels)

class Recipe:

	def __init__(self, ingredients):
		self.ingredients = ingredients
		self.segment_database = SegmentDatabase()
		self.ignore_list = []
			
	def get_frames(self, segment, labels='', max_len=15*24):

		# print 'segment: ', segment

		start, end = segment.get('s')
		ytid = segment.get('ytid')

		cap = get_capture(ytid)
		fps = get_fps(cap)
		assert(fps == 24)
		# print 'fps: ', fps

		frames = []
		if cap.set(cv.CV_CAP_PROP_POS_FRAMES, start):
			length = int(min(get_segment_len(segment), max_len))
			print 'grabbing %d frames' % length
			for i in range(length):
				ret, frame = cap.read()
				if ret:
					draw_str(frame, (20, 20), '%s: %s' % (ytid, labels))
					frames.append(frame)
				else:
					# problem is that setting a given frame in the video capture may actually jump forward to the closest keyframe
					# because of limitations with the video compression algorithm. for short clips this is likely to occur
					print 'ERROR: segment read cut short at index %d for segment %s' % (i, json.dumps(segment))
					break
					# raise Exception('no more frames, index = %d, segment: %s' % (i, json.dumps(segment)))
		else:
			raise Exception('unable to set seek position in video capture')
		return frames

	def bake(self):

		segment_database = self.segment_database
		frames = []
		for ingredient in self.ingredients:
			labels, excl_labels, min_span, max_span = ingredient.labels, [], ingredient.min_span, ingredient.max_span
			print 'labels=%s, excl_labels=%s, min_span=%d, max_span=%d' % (labels, excl_labels, min_span, max_span)
			
			candidate_factory = CandidateFactory(segment_database)
			candidates = candidate_factory.get_candidates(labels)
			print '#immediate candidates: %d' % len(candidates)

			ytids = candidate_factory.get_ytids(20)
			query = dict(
				labels=labels,
				required=ingredient.required_labels,
				forbidden=ingredient.forbidden_labels,
				)
			interval = ingredient.interval
			spanAlpha = ingredient.span_alpha
			minSpan = ingredient.min_span
			maxSpan = ingredient.max_span
			ignore_list = self.ignore_list

			candidates = sortCandidates(ytids=ytids, query=query, minSpan=minSpan, maxSpan=maxSpan, interval=interval, spanAlpha=spanAlpha, segment_database=segment_database, ignoreList=ignore_list)
			print '#candidates: %d' % len(candidates)

			# reformat
			for candidate in candidates:
				candidate['s'] = (candidate.get('start'), candidate.get('end'))

			if candidates:
				# segment = candidates[random.randint(0,len(candidates)-1)]
				score_sum = sum([candidate.get('score') for candidate in candidates])
				# filter out invalid candidates
				candidates = filter(lambda x: x.get('score') >= 0, candidates)
				# if there are any valid candidates left
				if candidates:
					new_candidates = []
					# we want the multiplier to be atleast 1e5
					multiplier = min(1e5, max(1e5, 1 / (candidates[-1].get('score') / score_sum)))
					# print 'multiplier: ' , multiplier
					for candidate in candidates:
						# we want atleast 1 occurence
						probability_score = multiplier * candidate.get('score') / score_sum
						# print 'probability_score: ', probability_score
						# print 'rel. rounding error: %2.2f%%' % (100 * abs(probability_score - max(1, int(round(probability_score)))) / probability_score)
						new_candidates += [candidate] * max(1, int(round(probability_score)))
					print len(new_candidates)
					candidate = random.choice(new_candidates)

					print candidate
					self.ignore_list.append(candidate)
					frames += self.get_frames(candidate, labels, max_len=maxSpan)
				else:
					print 'no candidate matching: %s' % ingredient
			else:
				raise Exception('no candidate matching: %s' % ingredient)
		return frames

def write_video(filename, frames, height=360, width=640, fps=24, fourcc=cv.CV_FOURCC('D','I','V','3')):
	
	writer = cv.CreateVideoWriter(filename, int(fourcc),fps,(int(width),int(height)),1)	
	for frame in frames:

		# convert frame to iPlImage
		frame = cv.fromarray(frame)
		cv_img = cv.CreateImageHeader((width, height), cv.IPL_DEPTH_8U, 3)
		cv.SetData(cv_img, frame.tostring(), width * 3)
		# write image
		cv.WriteFrame(writer, cv_img)

def main():	

	# dummy_labels = ['is_day', 'is_night', 'vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']
	# dummy_labels = ['vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']

	ingredients = [
		Ingredient(labels=['is_day', 'is_overview']),
		Ingredient(labels=['is_day', 'is_in_crowd', 'vertical_oscillation']),
		Ingredient(labels=['is_day', 'has_person_in_focus']),
		Ingredient(labels=['is_night']),
		Ingredient(labels=['is_night', 'vertical_oscillation']),
		Ingredient(labels=['is_night', 'has_police']),
		Ingredient(labels=['is_night'])
		]
	recipe = Recipe(ingredients)
	frames = recipe.bake()
	write_video('testout.avi', frames)

	# fps = 24
	# for frame in frames:
	# 	cv2.imshow('', frame)
	# 	cv2.waitKey(int(1000/fps))

if __name__ == '__main__':
	# cProfile.run('main()')
	main()
