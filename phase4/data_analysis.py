#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import random
import numpy as np
from collections import *
import cProfile
import os
import answers

std = np.std
var = np.var
mean = np.mean
sqrt = math.sqrt

LoS = """0.005 level of significance: z_a = 3.30\n0.010 level of significance: z_a = 2.33
0.025 level of significance: z_a = 1.96\n0.050 level of significance: z_a = 1.645\n0.100 level of significance: z_a = 1.28"""

def computeZ(x1, x2, delta=0.0):

	# p. 256 

	n1, n2 = float(len(x1)), float(len(x2))
	v1, v2 = var(x1), var(x2)
	Z = ((mean(x1)-mean(x2)) - delta) / sqrt((v1/n1) + (v2/n2))
	return Z

class Data:

	def __init__(self, path='.'):

		self.file2yt = {'d370ccc56c': '2C7Y5Shw5p8', 'bf7dc9f5ca': '48QPI1wz1QY', '2806c14722': '5swFsRKsI7I', '9891596ecf': '75IHEvP7An4', '2f7a25e921': '7sao2_7sKms', '3b95a67d38': '8sk2HWj4zhU', 'a8d1de1e81': 'BbS0GQLp4CQ', '913eef2ed2': 'E1v6_GvB3j4', '143a413f62': 'G9YeDzzwyVQ', '77baa022f1': 'HlOIeCzXSCI', '57d23634ac': 'MLzAuBHSiTU', 'c23777fd98': 'Mu7JJEHonGE', '48b62f11dc': 'XYHr6gZqkTs', '3f79a5f7f1': 'ZFSYWB1BcxE', '80a451d4c2': 'a7k7gemEwsE', '90fe6adcd2': 'ho1CjPB02F8', 'dd7d1998f8': 'hrxbQNTBqNQ', '625838c2b1': 'j_pkzYcJ8j0', '7babfd31c4': 'pBw6UJa6-_w', '14e177dd42': 'rEFkglQCcXg', '98b1d02056': 'yrfnIujswX8'}
		self.yt2file = {'2C7Y5Shw5p8': 'd370ccc56c', '48QPI1wz1QY': 'bf7dc9f5ca', '5swFsRKsI7I': '2806c14722', '75IHEvP7An4': '9891596ecf', '7sao2_7sKms': '2f7a25e921', '8sk2HWj4zhU': '3b95a67d38', 'BbS0GQLp4CQ': 'a8d1de1e81', 'E1v6_GvB3j4': '913eef2ed2', 'G9YeDzzwyVQ': '143a413f62', 'HlOIeCzXSCI': '77baa022f1', 'MLzAuBHSiTU': '57d23634ac', 'Mu7JJEHonGE': 'c23777fd98', 'XYHr6gZqkTs': '48b62f11dc', 'ZFSYWB1BcxE': '3f79a5f7f1', 'a7k7gemEwsE': '80a451d4c2', 'ho1CjPB02F8': '90fe6adcd2', 'hrxbQNTBqNQ': 'dd7d1998f8', 'j_pkzYcJ8j0': '625838c2b1', 'pBw6UJa6-_w': '7babfd31c4', 'rEFkglQCcXg': '14e177dd42', 'yrfnIujswX8': '98b1d02056'}

		f = open('data_dump.json', 'r')
		self.dump = json.loads(f.read())

		self.videos = []
		filenames = ['%s/%s' % (path, filename) for filename in os.listdir(path) if filename.split('.')[-1] in ['json'] and filename != 'data_dump.json']
		# print filenames
		for filename in filenames:
			f = open(filename, 'r')
			content = json.loads(f.read())
			self.videos.append(content)
			f.close()

	@staticmethod
	def __get_filename(video):
		return video.get('filename').split('/')[-1]

	def __ytid_to_filename(self, ytid):

		if ytid not in self.yt2file:
			raise Exception('no corresponding filename for ytid: %s' % ytid)

		filename = self.yt2file.get(ytid)
		return filename

	def __filename_to_ytid(self, filename):

		_filename = filename.split('.')[0]
		if _filename not in self.file2yt:
			raise Exception('no corresponding ytid for filename: %s' % _filename)

		ytid = self.file2yt.get(_filename)
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
		if 'cop15' in datasets:
			filenames += ['2f7a25e921.m4v', '77baa022f1.m4v', 'dd7d1998f8.avi']
		if 'acta_aarhus' in datasets:
			filenames += ['2806c14722.avi']
		if 'acta_cph' in datasets:
			filenames += ['48b62f11dc.avi', '57d23634ac.m4v', '3f79a5f7f1.m4v', 'c23777fd98.m4v', '14e177dd42.m4v']
		return filenames

	# get: total random, label random, edited, recipe

	def __get_filenames_with_total_random_recipe(self):
		return ['dd7d1998f8.avi', '2806c14722.avi', '48b62f11dc.avi']

	def get_ytid_with_total_random_recipe(self):
		return self.__filenames_to_ytids(self.__get_filenames_with_total_random_recipe())

	def __get_filenames_with_random_label_recipe(self):
		return ['3b95a67d38.avi', '7babfd31c4.avi', '80a451d4c2.avi', '90fe6adcd2.avi', '143a413f62.avi', 'd370ccc56c.avi']

	def get_ytid_with_random_label_recipe(self):
		return self.__filenames_to_ytids(self.__get_filenames_with_random_label_recipe())

	def __get_filenames_human_edited(self):
		return ['2f7a25e921.m4v', '77baa022f1.m4v', '57d23634ac.m4v', '3f79a5f7f1.m4v', 'c23777fd98.m4v', '14e177dd42.m4v']

	def get_ytid_human_edited(self):
		return self.__filenames_to_ytids(self.__get_filenames_human_edited())

	def __get_filenames_with_designer_recipe(self):
		return ['98b1d02056.avi', '913eef2ed2.avi', '625838c2b1.avi', '9891596ecf.avi', 'a8d1de1e81.avi', 'bf7dc9f5ca.avi']

	def get_ytid_with_designer_recipe(self):
		return self.__filenames_to_ytids(self.__get_filenames_with_designer_recipe())

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
	data = Data()
	# print data.get_ytids_with_dataset(datasets=['acta_aarhus'])
	# print data.get_ytids_with_span_alpha(span_alpha=0.25)
	# video = data.get_video_with_filename('90fe6adcd2.avi')
	# print Data.get_mean_score(video)
	# labels = ['is_in_crowd']
	# print 'videos with labels: %s' % labels
	# print data.get_ytids_with_labels(labels=labels)
	# ytids = ['wxiI97Qp08w']
	# print 'videos with ytids: %s' % ytids
	# print data.get_ytids_with_org_ytids(ytids=ytids)

	# print data.get_ytid_with_total_random_recipe()
	# print data.get_ytid_with_random_label_recipe()
	# print data.get_ytid_with_designer_recipe()
	# print data.get_ytid_human_edited()

	aarh = data.get_ytids_with_dataset(datasets=['acta_aarhus'])
	acph = data.get_ytids_with_dataset(datasets=['acta_cph'])
	cop15 = data.get_ytids_with_dataset(datasets=['cop15'])
	tr = data.get_ytid_with_total_random_recipe()
	lr = data.get_ytid_with_random_label_recipe()
	design = data.get_ytid_with_designer_recipe()
	human_edit = data.get_ytid_human_edited()
	low_alpha = data.get_ytids_with_span_alpha(span_alpha=0.25)
	high_alpha = data.get_ytids_with_span_alpha(span_alpha=0.50)

	all_answers = answers.loadAllAnswers()

	print '\nlow alpha'
	la_video_answers = answers.trimAnswersToYTIDs(all_answers, low_alpha)
	answers.showScoresForAnswers(la_video_answers)

	print '\nhigh alpha'
	ha_video_answers = answers.trimAnswersToYTIDs(all_answers, high_alpha)
	answers.showScoresForAnswers(ha_video_answers)
	
	print 'ACTA Aarhus'
	aarh_video_answers = answers.trimAnswersToYTIDs(all_answers, aarh)
	answers.showScoresForAnswers(aarh_video_answers)

	print '\nACTA cph.'
	acph_video_answers = answers.trimAnswersToYTIDs(all_answers, acph)
	answers.showScoresForAnswers(acph_video_answers)

	print '\nCOP15'
	cop15_video_answers = answers.trimAnswersToYTIDs(all_answers, cop15)
	answers.showScoresForAnswers(cop15_video_answers)

	print '\ntotally random'
	tr_video_answers = answers.trimAnswersToYTIDs(all_answers, tr)
	answers.showScoresForAnswers(tr_video_answers)	

	print '\nrandom label'
	lr_video_answers = answers.trimAnswersToYTIDs(all_answers, lr)
	answers.showScoresForAnswers(lr_video_answers)

	print '\ndesigner'
	des_video_answers = answers.trimAnswersToYTIDs(all_answers, design)
	answers.showScoresForAnswers(des_video_answers)

	print '\nhuman edited'
	hum_video_answers = answers.trimAnswersToYTIDs(all_answers, human_edit)
	answers.showScoresForAnswers(hum_video_answers)

	def get_answers(videos):
		content = []
		editing = []
		clip_len = []
		video_len = []
		for vid in videos:
			for answer in vid.get('answers'):
				if answer.get('question_title') == 'content':
					content.append(answer.get('answer_value'))
				if answer.get('question_title') == 'editing':
					editing.append(answer.get('answer_value'))
				if answer.get('question_title') == 'clip len':
					clip_len.append(answer.get('answer_value'))
				if answer.get('question_title') == 'video len':
					video_len.append(answer.get('answer_value'))
		return content, editing, clip_len, video_len

	# compare totally random to designer

	content, editing, clip_len, video_len = get_answers(tr_video_answers)	
	x1 = content

	content, editing, clip_len, video_len = get_answers(des_video_answers)	
	x2 = content

	print ''
	print LoS
	d = 0.025
	Z = computeZ(x1,x2, d)
	print '\nZ = %2.3f, d = %2.4f\n' % (Z, d)
	# if d == 0:
	# 	# alt. hypothesis: u1 != u2
	# 	if Z > 1.645:
	# 		print 'reject H0 at 0.1 level of significance'
	# 	else:
	# 		print 'cannot reject H0 at 0.1 level of significance'
	# if d > 0:
	# 	# alt. hypothesis: u1 > u2
	# 	if Z > 1.28:
	# 		print 'reject H0 at 0.1 level of significance'
	# 	else:
	# 		print 'cannot reject H0 at 0.1 level of significance'
	# if d < 0:
	# 	pass
	# 	# alt. hypothesis: u1 < u2

	print ''

if __name__ == '__main__':
	main()
