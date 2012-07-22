#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

def _has_label(label, item):

	# print label, item
	return label in item['l']

def _has_ytid(ytid, item):

	# print ytid, item
	return ytid in item['ytid']

class SegmentDatabase:

	def __init__(self):
		self.db = None
		self._open_db()

	def get_with_ytid(self, ytid):

		# equivalent to builtin filter-function
		items = []
		for item in self.db:
			if _has_ytid(ytid, item):
				items.append(item)
		return items

	def get_with_label(self, label):

		# equivalent to builtin filter-function
		return [item for item in self.db if _has_label(label, item)]

	def get_labels_for_ytid(self, ytid):

		candidates = [item for item in self.db if _has_ytid(ytid, item)]
		labels = list(set([candidate.get('l')[0] for candidate in candidates]))
		return labels

	def trim_to_datasets(self, dataset_list):
		# acta_cph, acta_aarhus, cop15

		f = open('./datasets.json','r')
		d = json.loads(f.read())
		f.close()

		dataset = []
		for dtset in dataset_list:
			dataset += d.get(dtset)

		new_db = []
		for segment in self.db:
			ytid = segment.get('ytid')
			# ytid.split('_')

			for part in ytid.split('_'):
				if 'part' in part:
					ytid = ytid.replace('_%s' % part, '')
					break
			
			if ytid in dataset:
				new_db.append(segment)

		self.db = new_db
		print 'DB size: %d, %dkb' % (len(self.db), len(json.dumps(self.db))/1000)

	def remove_ignored_files(self):

		ignore = ['']
		def filter_fun(x):
			for ytid in ignore:
				if x.get('ytid') in ignore:
					return False
			return True

		self.db = filter(filter_fun, self.db)

	def _open_db(self):
		
		f = open('./database.json','r')
		self.db = json.loads(f.read())
		self.remove_ignored_files()
		f.close()
		
	# not working properly now we have "classifyed" the code
	# def validate_dummy_segment(self, ds, dummies):

	# 	for dummy in dummies:
	# 		if ds.get('ytid') == dummy.get('ytid') and ds.get('l') == dummy.get('l') and is_overlapping(dummy, ds):
	# 			return False
	# 	return True

	# def gen_dummy_segment(self, labels, ytids, dummies, min_segment_length=36):

	# 	for i in range(5):
	# 		a = random.randint(0,2159-min_segment_length)
	# 		b = random.randint(a+1,2160)
	# 		l = [random.choice(labels)]
	# 		ytid = random.choice(ytids)
	# 		ds = dict(s=(a,b), l=l, ytid=ytid)
	# 		# need to check that the new dummy segment does not overlap an existing segment
	# 		if self.validate_dummy_segment(ds, dummies):
	# 			return ds
	# 	return None

	# def create_dummy_data(self, size=100, num_labels=5, num_videos=5):

	# 	dummies = []
	# 	ytids = range(1,num_videos)
	# 	labels = sorted(random.sample(LABELS, num_labels))
	# 	print 'dummy labels: ', labels
	# 	for i in range(size):
	# 		ds = self.gen_dummy_segment(labels,ytids, dummies)
	# 		if ds:
	# 			dummies.append(ds)
	# 	self.db = dummies
	# 	return dummies, labels