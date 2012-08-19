#!/usr/bin/env python
# -*- coding: utf-8 -*-

# input (label, min_segment_length)*, sort_order 
# sort_order: #labels;segment_length -> sort first by #labels present in a segment, break ties with segment_length
# output: listen er sorteret efter "sort_order". hvis input er 2 labels vil output indeholde op til 3 permuationer af segmenter, 
# en hvor første label er present i segmentet, en hvor anden label er present i segmentet, og en hvor begge labels er present i samme segment. 
# på denne måde smides intet væk (og det umiddelbart mest relevante er at finde forrest i listen).

import json
import random
try:
	import cv
	import cv2
	from common import draw_str
except Exception as e:
	print e
from segment_db import SegmentDatabase
from sort_candidates import sortCandidates
from collections import *
# for checking if file exists
import os

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

		# ytids = [candidate.get('ytid') for candidate in self.candidates]

		d = defaultdict(lambda: 0)
		# count the number of occurences of each candidate
		for candidate in self.candidates:
			d[candidate.get('ytid')] += len(candidate.get('l'))**2
			
		# sort by the number of occurences (largest first)
		d = sorted(d.items(), key=lambda (x,y): y, reverse=True)
		if lim > 0:
			d = d[:lim]
		print json.dumps(d, sort_keys=True, indent=4)
		# and finally the new list of ytids
		ytids = [x for (x,y) in d]

		print 'get_ytids(...) RESULT: ', ytids

		return ytids

	# def get_ytids2(self, lim=-1):

	# 	ytids = [candidate.get('ytid') for candidate in self.candidates]

	# 	d = defaultdict(lambda: 0)
	# 	# count the number of occurences of each candidate
	# 	for c in ytids: d[c] += 1
	# 	# sort by the number of occurences (largest first)
	# 	d = sorted(d.items(), key=lambda (x,y): y, reverse=True)
	# 	if lim > 0:
	# 		d = d[:lim]
	# 	print json.dumps(d, sort_keys=True, indent=4)
	# 	# and finally the new list of ytids
	# 	ytids = [x for (x,y) in d]

	# 	print 'get_ytids(...) RESULT: ', ytids

	# 	return ytids

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

	def __init__(self, labels, min_span=48, max_span=120, interval=10, span_alpha=0.5, required_labels=[], forbidden_labels=[]):
		self.labels = labels
		self.min_span = min_span
		self.max_span = max_span
		self.interval = interval
		self.span_alpha = span_alpha
		self.required_labels = required_labels
		self.forbidden_labels = forbidden_labels

	def __str__(self):

		return 'labels=%s, min_span=%d, max_span=%d, interval=%d, span_alpha=%f, required_labels=%s, forbidden_labels=%s' % (self.labels, self.min_span, self.max_span, self.interval, self.span_alpha, self.required_labels, self.forbidden_labels)

	def __to_dict__(self):

		return dict(
			labels=self.labels,
			min_span=self.min_span,
			max_span=self.max_span,
			interval=self.interval,
			span_alpha=self.span_alpha,
			required_labels=self.required_labels,
			forbidden_labels=self.forbidden_labels,
			)

def filename_generator(path):

	filename = '%s%s' % (path, hex(random.randint(1e6,1e12)).replace('0x', ''))
	if os.path.exists('%s.avi' % filename):
		# in the extremely unlikely case the file already exists we compute a new name
		return filename_generator(path)
	return filename

class Recipe:

	def __init__(self, name, ingredients, datasets=[]):

		self.name = name
		self.ingredients = ingredients
		self.segment_database = SegmentDatabase()
		self.ignore_list = []
		self.frames = []
		self.result = dict(segments=[])
		self.datasets = datasets
		if datasets:
			self.segment_database.trim_to_datasets(datasets)

		self.filename = filename_generator(path='./data/out/')
			
	def dump_to_json(self):

		filename = '%s.json' % self.filename
		
		dump = dict(
			ingredients=[ingredient.__to_dict__() for ingredient in self.ingredients],
			result=self.result,
			filename='%s.avi' % self.filename,
			datasets=self.datasets,
			)

		f = open(filename, 'w')
		f.write(json.dumps(dump))
		f.close()

	def get_frames(self, segment, captions=''):

		# print 'segment: ', segment

		start, end = segment.get('start'), segment.get('end')
		ytid = segment.get('ytid')

		cap = get_capture(ytid)
		fps = get_fps(cap)
		assert(fps == 24)

		captions += ' :: %s' % (self.name)
		frames = []
		if cap.set(cv.CV_CAP_PROP_POS_FRAMES, start):
			length = end - start
			print 'grabbing %d frames' % length
			for i in range(length):
				ret, frame = cap.read()
				if ret:
					# draw_str(frame, (20, 20), '%s: %s' % (ytid, captions))
					frames.append(frame)
				else:
					# problem is that setting a given frame in the video capture may actually jump forward to the closest keyframe
					# because of limitations with the video compression algorithm. for short clips this is likely to occur
					print 'ERROR: segment read cut short at index %d for segment %s' % (i, json.dumps(segment))
					break
					# raise Exception('no more frames, index = %d, segment: %s' % (i, json.dumps(segment)))
		else:
			raise Exception('unable to set seek position in video capture')
		print 'returning %d frames' % len(frames)
		return frames

	def bake(self):

		segment_database = self.segment_database
		frames = []
		for ingredient in self.ingredients:
			labels, excl_labels, min_span, max_span = ingredient.labels, [], ingredient.min_span, ingredient.max_span
			print 'labels=%s, excl_labels=%s, min_span=%d, max_span=%d' % (labels, excl_labels, min_span, max_span)
			
			candidate_factory = CandidateFactory(segment_database)
			candidates = candidate_factory.get_candidates(labels)
			# print '#immediate candidates: %d' % len(candidates)

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
			# print '#candidates: %d' % len(candidates)

			if candidates:
				# filter out invalid candidates
				candidates = filter(lambda x: x.get('score') >= 0, candidates)
				# compute the sum-square of scores
				score_sum = sum([candidate.get('score')**2 for candidate in candidates])
				if candidates: # if there are any valid candidates left
					new_candidates = []
					# we want the multiplier to be atleast 1e5
					min_score = candidates[-1].get('score')
					if min_score:
						multiplier = min(1e5, max(1e5, 1 / (min_score / score_sum)))
					else:
						multiplier = 1e5
					# print 'multiplier: ' , multiplier
					for candidate in candidates:
						# we want atleast 1 occurence
						probability_score = multiplier * candidate.get('score')**2 / score_sum
						# print 'probability_score: ', probability_score
						# print 'rel. rounding error: %2.2f%%' % (100 * abs(probability_score - max(1, int(round(probability_score)))) / probability_score)
						new_candidates += [candidate] * max(1, int(round(probability_score)))
					# print len(new_candidates)
					candidate = random.choice(new_candidates)

					print candidate

					start = candidate.get('start')
					end = candidate.get('end')
					ytid = candidate.get('ytid')
					score = candidate.get('score')

					self.result.get('segments').append(dict(ytid=ytid, start=start, end=end, score=score))
					frames += self.get_frames(candidate, captions='score: %2.2f' % (score))
					candidate['start'] = max(0, start-10*24)
					# no consequence if this actually extends the length of the video
					candidate['end'] = end+10*24
					self.ignore_list.append(candidate)
				else:
					print '\n******************\nno candidate matching: %s\n******************\n' % ingredient
			else:
				print '\n******************\nno candidate matching: %s\n******************\n' % ingredient
		self.frames = frames
		self.dump_to_json()
		return self

	def write_video(self, height=360, width=640, fps=24, fourcc=cv.CV_FOURCC('D','I','V','3')):
		
		filename = '%s.avi' % self.filename
		frames = self.frames
		writer = cv.CreateVideoWriter(filename, int(fourcc),fps,(int(width),int(height)),1)	
		for frame in frames:
			# convert frame to iPlImage
			frame = cv.fromarray(frame)
			cv_img = cv.CreateImageHeader((width, height), cv.IPL_DEPTH_8U, 3)
			cv.SetData(cv_img, frame.tostring(), width * 3)
			# write image
			cv.WriteFrame(writer, cv_img)
	
	def show_video(self):

		fps = 24
		for frame in self.frames:
			cv2.imshow('', frame)
			cv2.waitKey(int(1000/fps))

def get_random_recipe(num_ingredients, input_labels, max_labels_per_ingredient=3, span_alpha=None):

	ingredients = []
	clip_len_sum = 0
	for i in range(num_ingredients):
		num_labels = random.randint(1,max_labels_per_ingredient)
		while True:
			random.shuffle(input_labels)
			labels = input_labels[0:num_labels]
			# cant have both night and day labels
			if not ('is_day' in labels and 'is_night' in labels):
				break

		# multiplier is avrg. video len. divided by the number of clips to get the avr. clip len
		# current value produces videos in the range 25-35s
		multiplier = 45.0 / num_ingredients
		min_span = random.randint(2*24, int(multiplier*24))
		max_span = random.randint(min_span+6, 2*min_span+6)

		clip_len = ((max_span+min_span) / (2.0*24))
		clip_len_sum += clip_len
		
		# labels, min_span=48, max_span=120, interval=10, span_alpha=0.05, required_labels=[], forbidden_labels=[]
		ingredient = Ingredient(labels=labels, min_span=min_span, max_span=max_span, span_alpha=span_alpha)
		ingredients.append(ingredient)
		# print 'ingredient #%d: ' % i, ingredient
		# print 'desired clip len: %2.2fs' % clip_len
	# print '%2.2fs' % clip_len_sum
	return ingredients

def main():	

	# ['is_day', 'is_night', 'vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']
	# labels, min_span=48, max_span=120, interval=10, span_alpha=0.05, required_labels=[], forbidden_labels=[]

	# ACTA CPH
	recipies = []
	for datasets, span_alpha in [(['acta_cph'], 0.5), (['acta_cph'], 0.25)]:
		ingredients = [
			Ingredient(labels=['is_overview'], min_span=72, max_span=120, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_overview'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_in_crowd'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_in_crowd'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['has_person_in_focus'], min_span=96, max_span=184, required_labels=['has_person_in_focus'], forbidden_labels=['is_in_crowd'], span_alpha=span_alpha),
			Ingredient(labels=['has_person_in_focus'], min_span=96, max_span=184, required_labels=['has_person_in_focus'], forbidden_labels=['is_in_crowd'], span_alpha=span_alpha),
			Ingredient(labels=['is_overview'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha)
			]
		recipe = Recipe('Acta Cph.', ingredients, datasets)
		recipies.append(recipe)

	# ACTA AARHUS
	for datasets, span_alpha in [(['acta_aarhus'], 0.5), (['acta_aarhus'], 0.25)]:
		ingredients = [
			Ingredient(labels=['is_overview'], min_span=72, max_span=120, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_overview'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_in_crowd'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_in_crowd'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['has_person_in_focus'], min_span=96, max_span=184, required_labels=['has_person_in_focus'], forbidden_labels=['is_in_crowd'], span_alpha=span_alpha),
			Ingredient(labels=['has_person_in_focus'], min_span=96, max_span=184, required_labels=['has_person_in_focus'], forbidden_labels=['is_in_crowd'], span_alpha=span_alpha),
			Ingredient(labels=['is_overview'], min_span=72, max_span=144, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha)
			]
		recipe = Recipe('Acta Aarhus', ingredients, datasets)
		recipies.append(recipe)

	# COP15
	for datasets, span_alpha in [(['cop15'], 0.5), (['cop15'], 0.25)]:
		required_labels = ['is_day']
		ingredients = [
			Ingredient(labels=['is_overview'], min_span=72, max_span=120, required_labels=required_labels, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_overview'], min_span=72, max_span=144, required_labels=required_labels, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_in_crowd'], min_span=72, max_span=144, required_labels=required_labels, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['is_in_crowd'], min_span=72, max_span=144, required_labels=required_labels, forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha),
			Ingredient(labels=['has_person_in_focus'], min_span=96, max_span=184, required_labels=['has_person_in_focus'], forbidden_labels=['is_in_crowd'], span_alpha=span_alpha),
			Ingredient(labels=['has_person_in_focus'], min_span=96, max_span=184, required_labels=['has_person_in_focus', 'is_night'], forbidden_labels=['is_in_crowd'], span_alpha=span_alpha),
			Ingredient(labels=['is_overview'], min_span=72, max_span=144, required_labels=['is_night'], forbidden_labels=['has_person_in_focus'], span_alpha=span_alpha)
			]
		recipe = Recipe('COP15', ingredients, datasets)
		recipies.append(recipe)

	input_labels_cop15 = ['is_day', 'is_night', 'vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']
	input_labels_acta = ['is_day', 'vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']
	for datasets, span_alpha in [(['acta_cph'], 0.5), (['acta_cph'], 0.25), (['acta_aarhus'], 0.5), (['acta_aarhus'], 0.25), (['cop15'], 0.5), (['cop15'], 0.25)]:
		if 'cop15' in datasets:
			input_labels = input_labels_cop15
		else:
			input_labels = input_labels_acta
		ingredients = get_random_recipe(num_ingredients=5, input_labels=input_labels, span_alpha=span_alpha)
		recipe = Recipe('Random', ingredients, datasets)
		recipies.append(recipe)

	print 'made %d recipies. Start cooking...' % len(recipies)
	for recipe in recipies:
		recipe.bake().write_video()

	# make 3 totally random videos
	path = './data/'
	max_len = 10.0*24
	min_len = 2.0*24

	def write_video(filename, frame, height=360, width=640, fps=24, fourcc=cv.CV_FOURCC('D','I','V','3')):
		writer = cv.CreateVideoWriter(filename, int(fourcc),fps,(int(width),int(height)),1)	
		for frame in frames:
			# convert frame to iPlImage
			frame = cv.fromarray(frame)
			cv_img = cv.CreateImageHeader((width, height), cv.IPL_DEPTH_8U, 3)
			cv.SetData(cv_img, frame.tostring(), width * 3)
			# write image
			cv.WriteFrame(writer, cv_img)

	__ytids = [filename.split('.')[0] for filename in os.listdir(path) if filename.split('.')[-1] in ['m4v']]
	for dataset in ['acta_cph', 'acta_aarhus', 'cop15']:

		f = open('./datasets.json','r')
		d = json.loads(f.read()).get(dataset)
		f.close()

		ytids = []
		for ytid in __ytids:
			_ytid = ytid
			for part in ytid.split('_'):
				if 'part' in part:
					_ytid = ytid.replace('_%s' % part, '')
					break
			if _ytid in d:
				# append org. ytid
				ytids.append(ytid)
		picked = []
		for i in range(6):
			# pick a random ytid
			while True:
				ytid = random.choice(ytids)
				if ytid not in picked:
					picked.append(ytid)
					print '%s found in %s' % (ytid, dataset)
					break
		frames = []
		for ytid in picked:
			cap = get_capture(ytid)
			# get length in frames
			num_frames = get_num_frames(cap)
			seg_len = int(min(random.randint(min_len, max_len), num_frames))
			start_frame = random.randint(0, num_frames-seg_len)
			# end_frame = start_frame + seg_len
		
			fps = get_fps(cap)
			assert(fps == 24)

			if cap.set(cv.CV_CAP_PROP_POS_FRAMES, start_frame):
				length = seg_len
				print 'grabbing %d frames' % length
				for i in range(length):
					ret, frame = cap.read()
					if ret:
						# draw_str(frame, (20, 20), '%s: %s' % (ytid, captions))
						frames.append(frame)
					else:
						# problem is that setting a given frame in the video capture may actually jump forward to the closest keyframe
						# because of limitations with the video compression algorithm. for short clips this is likely to occur
						print 'ERROR: segment read cut short at index %d for ytid %s' % (i, ytid)
						break
						# raise Exception('no more frames, index = %d, segment: %s' % (i, json.dumps(segment)))
			else:
				raise Exception('unable to set seek position in video capture')
		filename = '%s.avi' % filename_generator('./data/out/')
		write_video(filename, frames)

if __name__ == '__main__':
	main()
