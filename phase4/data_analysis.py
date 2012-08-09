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
import pylab
import matplotlib

plt = matplotlib.pyplot

# R interface
from rpy import *
r_friedman = r.friedman_test

std = np.std
var = np.var
mean = np.mean
array = np.array
sqrt = math.sqrt

LoS = """0.005 level of significance: z_a = 3.30\n0.010 level of significance: z_a = 2.33
0.025 level of significance: z_a = 1.96\n0.050 level of significance: z_a = 1.645\n0.100 level of significance: z_a = 1.28"""

# show output with text color (nice for finding significant effect in Friedman test)
SHOW_WITH_TEXT_COLOR = 0

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

def friedman(ys):

	def to_matrix(ys):
		# convert a pseudo-matrix to a matrix useable in R

		# compute length of each pseudo-row
		lens = [len(y) for y in ys]
		# print lens
		# get the longest
		max_len = max(lens)

		for i, y in enumerate(ys):
			ys[i] += [None] * (max_len - len(y))

		nys = []
		for y in ys:
			nys += y
		return r.matrix(nys, nrow=max_len)

	y = to_matrix(ys)
	# print y
	f = r_friedman(y=y)

	# DoF
	df = f.get('parameter').get('df')
	# p-value
	p = f.get('p.value')
	method = f.get('method')
	statistic = f.get('statistic')

	print method
	print 'DoF: ', df
	print 'p-value: ', p
	k = statistic.keys()[0]
	v = statistic.get(k)
	
	if SHOW_WITH_TEXT_COLOR:
		txt_clr = '\033[91m' # RED
		if df == 1 and v >= 3.841 or df == 2 and v >= 5.991 or df == 3 and v >= 7.815:
			txt_clr = '\033[92m' # GREEN
		print '%s: %s%2.2f\033[0m' % (k, txt_clr, v)
	else:
		print '%s: %2.2f' % (k, v)
	print ''

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

	# alpha
	la_video_answers = answers.trimAnswersToYTIDs(all_answers, low_alpha)
	ha_video_answers = answers.trimAnswersToYTIDs(all_answers, high_alpha)

	#datasets
	aarh_video_answers = answers.trimAnswersToYTIDs(all_answers, aarh)
	acph_video_answers = answers.trimAnswersToYTIDs(all_answers, acph)
	cop15_video_answers = answers.trimAnswersToYTIDs(all_answers, cop15)

	#recipies
	tr_video_answers = answers.trimAnswersToYTIDs(all_answers, tr)
	lr_video_answers = answers.trimAnswersToYTIDs(all_answers, lr)
	des_video_answers = answers.trimAnswersToYTIDs(all_answers, design)
	hum_video_answers = answers.trimAnswersToYTIDs(all_answers, human_edit)

	# print '\nlow alpha'
	# answers.showScoresForAnswers(la_video_answers)

	# print '\nhigh alpha'
	# answers.showScoresForAnswers(ha_video_answers)
	
	# print 'ACTA Aarhus'
	# answers.showScoresForAnswers(aarh_video_answers)

	# print '\nACTA cph.'
	# answers.showScoresForAnswers(acph_video_answers)

	# print '\nCOP15'
	# answers.showScoresForAnswers(cop15_video_answers)

	# print '\ntotally random'
	# answers.showScoresForAnswers(tr_video_answers)	

	# print '\nrandom label'
	# answers.showScoresForAnswers(lr_video_answers)

	# print '\ndesigner'
	# answers.showScoresForAnswers(des_video_answers)

	# print '\nhuman edited'
	# answers.showScoresForAnswers(hum_video_answers)

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
		# compute a total score by adding each category elementwise (and then convert to standard integer)
		total_score = [float(x/4.0) for x in list(np.sum([content, editing, clip_len, video_len], 0))]
		return content, editing, clip_len, video_len, total_score

	plot_barcharts = 0
	if plot_barcharts:
		##################
		# plot barcharts #
		##################

		# number of bins
		N = 5
		# figure export format
		format = 'png'

		# http://matplotlib.sourceforge.net/examples/pylab_examples/histogram_demo_extended.html
		# http://matplotlib.sourceforge.net/api/pyplot_api.html#matplotlib.pyplot.bar
		for j, (va, fig_title) in enumerate([(tr_video_answers, 'Totally random'), (lr_video_answers, 'Label random'), (des_video_answers, 'Designer'), (hum_video_answers, 'Human edited')]):
		# for j, (va, fig_title) in enumerate([(tr_video_answers, 'Totally random')]):
			content, editing, clip_len, video_len = get_answers(va)
			pylab.figure(j+1) # figsize=(10,10)
			pylab.suptitle(fig_title, fontsize=16)
			for i, (x, title) in enumerate([(content, 'Content'), (editing, 'Editing'), (clip_len, 'Clip length'), (video_len, 'Video length')]):
				pylab.subplot(2,2,i+1, title=title)
				# x = filter(lambda z: z, x) # remove 0's
				# histogram functions counts occurence of each element in different bins (into the 'n' variable)
				n, bins, patches = pylab.hist(x, bins=N); # print n, bins, patches
				# setting alpha to 0 to not show this plot
				pylab.setp(patches, 'alpha', 0.0, 'facecolor', 'b')
				ind = np.arange(N) - 2 # [-2,-1,0,1,2]
				plt.bar(left=ind, height=n, width=1.0, color='g')
				plt.xticks(ind + 1/2.0, ('TD', 'SD', 'DK', 'SA', 'TA'))
				pylab.grid(True)
			# http://matplotlib.sourceforge.net/api/pyplot_api.html#matplotlib.pyplot.savefig
			fname = './figs/%s_barplot.%s' % (fig_title.lower().replace(' ', ''), format)
			plt.savefig(fname, format=format)
		pylab.show()

	#################
	# Friedman test #
	#################

	# do a Friedman test (http://en.wikipedia.org/wiki/Friedman_test), similar to a Kruskal-Wallis (KW) test (p. 318)
	# the Friedman test is a non-parametric repeated measure on way ANOVA, non-parametric meaning we do not make assumptions on the normality of the data
	# (the data is not normal distributed), and the repeated measure ...
	# http://en.wikipedia.org/wiki/Friedman_test
	# http://yatani.jp/HCIstats/KruskalWallis
	# http://stat.ethz.ch/R-manual/R-patched/library/stats/html/friedman.test.html
	# http://www.gardenersown.co.uk/education/lectures/r/nonparam.htm#friedman
	# http://www.r-statistics.com/2010/04/repeated-measures-anova-with-r-tutorials/
	# http://vassarstats.net/textbook/ch15a.html
	# Friedman vs KW:
	# http://stats.stackexchange.com/questions/12030/friedman-vs-kruskal-wallis-test
	# http://www.aiaccess.net/English/Glossaries/GlosMod/e_gm_kruskal.htm

	y1 = get_answers(tr_video_answers)
	y2 = get_answers(lr_video_answers)
	y3 = get_answers(des_video_answers)
	y4 = get_answers(hum_video_answers)

	for i, t in enumerate(['content', 'editing', 'clip length', 'video length', 'total score']):
		print 'doing Friedman test for %s (recipies)' % t
		friedman([y1[i], y2[i], y3[i], y4[i]])

	y1 = get_answers(aarh_video_answers)
	y2 = get_answers(acph_video_answers)
	y3 = get_answers(cop15_video_answers)
	for i, t in enumerate(['content', 'editing', 'clip length', 'video length', 'total score']):
		print 'doing Friedman test for %s (datasets)' % t
		friedman([y1[i], y2[i], y3[i]])

	y1 = get_answers(la_video_answers)
	y2 = get_answers(ha_video_answers)
	for i, t in enumerate(['content', 'editing', 'clip length', 'video length', 'total score']):
		print 'doing Friedman test for %s (alpha-span)' % t
		friedman([y1[i], y2[i]])

	#################
	# post-hoc test #
	#################

	# everything is inconclusive

if __name__ == '__main__':
	main()
