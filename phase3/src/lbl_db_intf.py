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

LABELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

def is_overlapping(a,b):

	# return a.get('ytid') == b.get('ytid') and a.get('l') != b.get('l') and a != b and max(a.get('s')[0],b.get('s')[0]) < min(a.get('s')[1],b.get('s')[1])
	return max(a.get('s')[0],b.get('s')[0]) < min(a.get('s')[1],b.get('s')[1])

def validate_dummy_segment(ds, dummies):

	for dummy in dummies:
		if ds.get('ytid') == dummy.get('ytid') and ds.get('l') == dummy.get('l') and is_overlapping(dummy, ds):
			return False
	return True

def gen_dummy_segment(labels, ytids, dummies, min_segment_length=36):

	for i in range(5):
		a = random.randint(0,2159-min_segment_length)
		b = random.randint(a+1,2160)
		l = [random.choice(labels)]
		ytid = random.choice(ytids)
		ds = dict(s=(a,b), l=l, ytid=ytid)
		# need to check that the new dummy segment does not overlap an existing segment
		if validate_dummy_segment(ds, dummies):
			return ds
	return None

def create_dummy_date(size=100, num_labels=5, num_videos=5):

	global db

	dummies = []
	ytids = range(1,num_videos)
	labels = sorted(random.sample(LABELS, num_labels))
	print 'dummy labels: ', labels
	for i in range(size):
		ds = gen_dummy_segment(labels,ytids, dummies)
		if ds:
			dummies.append(ds)
	return dummies, labels

def get_segment_len(x):
	return x.get('s')[1] - x.get('s')[0]

def _has_label(label, item):
	# print label, item
	return label in item['l']

def _has_ytid(ytid, item):
	# print ytid, item
	return ytid in item['ytid']

def _get_with_ytid(ytid):

	# equivalent to builtin filter-function
	items = []
	for item in db:
		if _has_ytid(ytid, item):
			items.append(item)
	return items

def _get_with_label(label):

	# equivalent to builtin filter-function
	return [item for item in db if _has_label(label, item)]

def get_overlap(a,b):

	segment = (max(a.get('s')[0],b.get('s')[0]), min(a.get('s')[1],b.get('s')[1]))
	labels = sorted(a.get('l') + b.get('l'))
	ytid = a.get('ytid')
	# return dict(s=segment, l=labels, ytid=ytid, org=(a,b))
	return dict(s=segment, l=labels, ytid=ytid)

def get_overlapping_segments(labels, candidates, min_segment_length=6):

	# check if labels from a is present in labels from b
	def f(a,b):
		for l in a.get('l'):
			if l in b.get('l'):
				return False
		return True

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
	return candidates

def sort(candidates):

	# Starting with Python 2.2, sorts are guaranteed to be stable. That means that when multiple records have the same key, their original order is preserved.
	candidates = sorted(candidates, key=lambda x: x.get('ytid'), reverse=True)
	candidates = sorted(candidates, key=lambda x: get_segment_len(x), reverse=True)
	candidates = sorted(candidates, key=lambda x: len(x['l']), reverse=True)
	return candidates

def _has_ytid(ytid, item):
	return item.get('ytid') == ytid

def get_labels_for_ytid(ytid):

	candidates = [item for item in db if _has_ytid(ytid, item)]
	labels = list(set([candidate.get('l')[0] for candidate in candidates]))
	return labels

def get_segments(labels):

	candidates = []
	for label in labels:
		candidates += _get_with_label(label)

	candidates = get_overlapping_segments(labels, candidates)
	candidates = sort(candidates)
	return candidates

def open_db():

	global db
	f = open('./database.json','r')
	database = json.loads(f.read())
	f.close()
	db = database

	print 'DB size: %d, %dkb' % (len(db), len(json.dumps(db))/1000)

def seg_len_filter(candidates, min_len, max_len):

	if min_len > 0:
		candidates = filter(lambda x: get_segment_len(x) > min_len, candidates)
	if max_len > 0:
		candidates = filter(lambda x: get_segment_len(x) < max_len, candidates)
	return candidates

def label_filter(candidates, labels=[], excl_labels=[]):

	for label in labels:
		candidates = filter(lambda x: label in x.get('l'), candidates)
	for label in excl_labels:
		candidates = filter(lambda x: label not in x.get('l'), candidates)

	return candidates

def get_capture(ytid):

	video_src = 'data/%s.m4v' % ytid
	try:
		cap = cv2.VideoCapture(video_src)
	except:
		video_src = 'data/%s.avi' % ytid
		cap = cv2.VideoCapture(video_src)
	return cap

def get_num_frames(ytid):

	return get_capture(ytid).get(cv.CV_CAP_PROP_FRAME_COUNT)
	
def get_frames(segment, labels='', max_len=15*24):

	print 'segment: ', segment

	start, end = segment.get('s')
	ytid = segment.get('ytid')

	cap = get_capture(ytid)

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

def get_summary(recipe):

	frames = []
	for labels, excl_labels, min_seg_len, max_seg_len in recipe:
		print 'labels=%s, excl_labels=%s, min_seg_len=%d, max_seg_len=%d' % (labels, excl_labels, min_seg_len, max_seg_len)
		candidates = get_segments(labels)

		# print '**********************'
		# candidates = candidates[:50]
		# candidates = sorted(candidates, key=lambda x: x.get('ytid'))
		# for candidate in candidates:
		# 	print candidate.get('ytid')
		# print '**********************'
		# return []
		# candidates = rank_sort(candidates, None)
		# _candidates_before_exclusion = list(candidates)
		# candidates = label_filter(candidates, [], excl_labels)
		# print '#candidates: %d, excl_labels=%s' % (len(candidates), excl_labels)
		# candidates = seg_len_filter(candidates, min_seg_len, max_seg_len)
		print '#candidates: %d' % len(candidates)

		if candidates:
			segment = candidates[random.randint(0,len(candidates)-1)]
			# frames += get_frames(segment, ''.join(labels), random.randint(2.5*24, 5.5*24))
			# max_len = random.randint(2.5*24, 5.5*24)
			frames += get_frames(segment, labels, max_seg_len)
		else:
			print '***'
			for x in _candidates_before_exclusion:
				print x
			print '***'
			raise Exception('no segment matching: labels=%s, excl_labels=%s, min_seg_len=%d, max_seg_len=%d' % (labels, excl_labels, min_seg_len, max_seg_len))
	return frames

def main():	

	ytid = 'a8USSTeb8_I'
	print _get_with_ytid(ytid)
	return

	# ['vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']
	recipe = [
		(['is_day', 'is_overview'], [], 2.5*24, 5.0*24), 
		(['is_day', 'is_in_crowd', 'vertical_oscillation'], [], 2.5*24, 5.0*24), 
		(['is_day', 'has_person_in_focus'], [], 2.5*24, 5.0*24), 
		(['is_night'], [], 2.5*24, 5.9*24), 
		(['is_night', 'vertical_oscillation'], [], 2.5*24, 5.0*24), 
		(['is_night', 'has_police'], [], 2.5*24, 5.0*24), 
		(['is_night'], [], 2.5*24, 5.0*24)
	]
	
	frames = get_summary(recipe)

	fps = 24
	for frame in frames:
		cv2.imshow('', frame)
		cv2.waitKey(int(1000/fps))

if __name__ == '__main__':

	global dummy_labels
	# #segments, #labels, #videos
	# db, dummy_labels = create_dummy_date(2500, 7, 75)
	open_db()
	# dummy_labels = ['is_day', 'is_night', 'vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']
	dummy_labels = ['vertical_oscillation', 'is_overview', 'is_in_crowd', 'has_police', 'has_person_in_focus']
	# cProfile.run('main()')
	main()

	# db, dummy_labels = create_dummy_date(5, 2, 2)
	# print 'dummy segments:\n', json.dumps(db, sort_keys=True, indent=4), '\n'
	# print json.dumps(main(), sort_keys=True, indent=4)
