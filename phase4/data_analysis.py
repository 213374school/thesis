#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import numpy as np
from collections import *
# for checking if file exists
import os

class Data:

	def __init__(self, path):

		f = open('%s/dump/data_dump.json' % path, 'r')
		self.dump = json.loads(f.read())

		self.videos = []
		filenames = ['%s/%s' % (path, filename) for filename in os.listdir(path) if filename.split('.')[-1] in ['json']]
		for filename in filenames:
			f = open(filename, 'r')
			content = json.loads(f.read())
			self.videos.append(content)
			f.close()

	@staticmethod
	def __get_filename(video):
		return video.get('filename').split('/')[-1]

	def __ytid_to_filename(self, ytid):

		filename = ytid
		return filename

	def __filename_to_ytid(self, filename):

		ytid = filename
		return ytid

	def __filenames_to_ytids(self, filenames):

		return [self.__filename_to_ytid(filename) for filename in filenames]

	@staticmethod
	def get_scores(video):

		scores = []
		segments = video.get('result').get('segments')		
		for segment in segments:
			scores.append(segment.get('score'))
		return scores

	@staticmethod
	def get_mean_score(video):

		scores = Data.get_scores(video=video)
		return np.mean(scores)

	def get_video_with_filename(self, filename):

		for video in self.videos:
			_filename = Data.__get_filename(video)
			if _filename == filename:
				return video
		raise Exception('video not found')

	def __get_filenames_with_dataset(self, datasets=[]):

		filenames = []
		for video in self.videos:
			_datasets = video.get('datasets')
			for _dataset in _datasets:
				if _dataset in datasets:
					filename = Data.__get_filename(video)
					filenames.append(filename)
					break
		return filenames

	def get_ytids_with_dataset(self, datasets=[]):

		filenames = self.__get_filenames_with_dataset(datasets=datasets)
		return self.__filenames_to_ytids(filenames=filenames)

	def __get_filenames_with_span_alpha(self, span_alpha):

		filenames = []
		for video in self.videos:
			# all ingredients have the same span_alpha
			_span_alpha = video.get('ingredients')[0].get('span_alpha')
			if _span_alpha == span_alpha:
				filename = Data.__get_filename(video)
				filenames.append(filename)
		return filenames

	def get_ytids_with_span_alpha(self, span_alpha):

		if span_alpha not in [0.25, 0.5]:
			raise Exception('invalid span alpha value. valid values are 0.25 and 0.50')

		filenames = self.__get_filenames_with_span_alpha(span_alpha=span_alpha)
		return self.__filenames_to_ytids(filenames=filenames)

	def __get_filenames_with_labels(self, labels):

		def has_labels(ingredient, labels):
			
			_labels = ingredient.get('labels')
			for _label in _labels:
				if _label not in labels:
					return 0
			return 1

		filenames = []
		for video in self.videos:
			ingredients = video.get('ingredients')
			for ingredient in ingredients:
				if has_labels(ingredient, labels):
					filename = Data.__get_filename(video)
					filenames.append(filename)
					break
		return filenames

	def get_ytids_with_labels(self, labels):

		filenames = self.__get_filenames_with_labels(labels=labels)
		return self.__filenames_to_ytids(filenames=filenames)

	def __get_filenames_with_org_ytids(self, ytids):

		def has_ytid(segment, ytids):
			
			_ytid = segment.get('ytid')
			return _ytid in ytids

		filenames = []
		for video in self.videos:
			segments = video.get('result').get('segments')
			for segment in segments:
				if has_ytid(segment, ytids):
					filename = Data.__get_filename(video)
					filenames.append(filename)
					break
		return filenames

	def get_ytids_with_org_ytids(self, ytids):

		filenames = self.__get_filenames_with_org_ytids(ytids=ytids)
		return self.__filenames_to_ytids(filenames=filenames)


def main():
	data = Data('./mt_out')
	print data.get_ytids_with_dataset(datasets=['acta_aarhus'])
	print data.get_ytids_with_span_alpha(span_alpha=0.25)
	video = data.get_video_with_filename('90fe6adcd2.avi')
	print Data.get_mean_score(video)
	labels = ['is_in_crowd']
	print 'videos with labels: %s' % labels
	print data.get_ytids_with_labels(labels=labels)
	ytids = ['wxiI97Qp08w']
	print data.get_ytids_with_org_ytids(ytids=ytids)

if __name__ == '__main__':
	main()