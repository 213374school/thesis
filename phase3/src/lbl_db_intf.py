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

LABELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

def is_overlapping(a,b):

	return a.get('ytid') == b.get('ytid') and a.get('l') != b.get('l') and a != b and max(a.get('s')[0],b.get('s')[0]) < min(a.get('s')[1],b.get('s')[1])

def validate_dummy_segment(ds, dummies):

	for dummy in dummies:
		if not is_overlapping(dummy, ds):
			return True
	return True

def gen_dummy_segment(labels, ytids, dummies, min_segment_length=36):

	for i in range(5):
		a = random.randint(0,2159-min_segment_length)
		b = random.randint(a+1,2160)
		l = random.choice(labels)
		ytid = random.choice(ytids)
		ds = dict(s=(a,b), l=l, ytid=ytid)
		# need to check that the new dummy segment does not overlap an existing segment
		if validate_dummy_segment(ds, dummies):
			return ds

def create_dummy_date(size=100, num_labels=5, num_videos=5):

	dummies = []
	ytids = range(1,num_videos)
	labels = random.sample(LABELS, num_labels)
	for i in range(size):
		ds = gen_dummy_segment(labels,ytids, dummies)
		dummies.append(ds)
	return dummies

def get_segment_len(x):
	return x.get('s')[1] - x.get('s')[0]

def _has_label(label, item):
	# print label, item
	return label in item['l']

def _get_with_label(label):

	# equivalent to builtin filter-function
	return [item for item in db if _has_label(label, item)]

def get_overlap(a,b):

	segment = (max(a.get('s')[0],b.get('s')[0]), min(a.get('s')[1],b.get('s')[1]))
	labels = sorted(a.get('l') + b.get('l'))
	ytid = a.get('ytid')
	return dict(s=segment, l=labels, ytid=ytid)

def get_overlapping_segments(labels, candidates, min_segment_length=36):

	_candidates = []
	for a in candidates:
		for b in candidates:
			if is_overlapping(a,b):
				c = get_overlap(a,b)
				# avoid duplicates and too short segments
				if get_segment_len(c) > min_segment_length and c not in _candidates:
					_candidates.append(c)

	return _candidates

def sort(candidates):

	return sorted(candidates, key=lambda x: len(x['l']), reverse=True)

def get_segments(labels):

	candidates = []
	for label in labels:
		candidates += _get_with_label(label)
	
	candidates += get_overlapping_segments(labels, candidates)

	candidates = sort(candidates)
	return candidates

def main():

	global db
	# #segments, #labels, #videos
	db = create_dummy_date(5000, 7, 75)

	labels = random.sample(LABELS, 3)
	print 'DB size: %d' % len(db)

	for i in range(1):
		candidates = get_segments(labels)

	# candidates = get_segments(labels)
	print '#candidates: %d' % len(candidates)
	# print 'candidates: ', json.dumps(candidates[:5], sort_keys=True, indent=4)

if __name__ == '__main__':
	# cProfile.run('main()')
	main()