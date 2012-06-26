#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import math
import pylab
# import time
# import datetime

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

class ROCpt():

	def __init__(self, tp, fp, tn, fn, label=''):
		
		self.tp = float(tp)
		self.fp = float(fp)
		self.tn = float(tn)
		self.fn = float(fn)
		self.label = label

	def positives(self):

		return self.tp + self.fn

	def negatives(self):

		return self.fp + self.tn

	# true positives rate
	def tp_rate(self):

		if self.positives() > 0:
			# print self.tp / self.positives()
			return self.tp / self.positives()
		else:
			return 0.0

	# false positives rate
	def fp_rate(self):

		if self.negatives() > 0:
			return self.fp / self.negatives()
		else:
			return 0.0

	# true negatives rate
	def tn_rate(self):

		if self.negatives() > 0:
			return self.tn / self.negatives()
		else:
			return 0.0

	# false negatives rate
	def fn_rate(self):

		if self.positives() > 0:
			return self.fn / self.positives()
		else:
			return 0.0			

	def pos_precision(self):

		if (self.tp + self.fp) > 0:
			return self.tp / (self.tp + self.fp)
		else:
			return None

	def pos_recall(self):

		return self.tp_rate()

	def neg_precision(self):

		if (self.tn + self.fn) > 0:
			return self.tn / (self.tn + self.fn)
		else:
			return None

	def neg_recall(self):

		return self.tn_rate()		

	# def accuracy(self):

	# 	return self.tp / (self.tp + self.fp)

	def pos_f_measure(self):

		if self.pos_precision() and self.pos_recall():
			return 2.0 / (1/self.pos_precision() + 1/self.pos_recall())
		else:
			return None

	def neg_f_measure(self):

		if self.neg_precision() and self.neg_recall():
			return 2.0 / (1/self.neg_precision() + 1/self.neg_recall())
		else:
			return None

class ROCPlot():
	def __init__(self, filename=None, show_legend=True, plot_on=True, fig_title=''):

		self.show_legend = show_legend
		self.plot_on = plot_on

		if self.plot_on:
			pylab.figure(dpi=100, figsize=(11,7))

		if filename:
			f = open(filename,'r')
			content = f.read()
			content = json.loads(content)		
			f.close()

			data = content.get('data')

			def extract(x):
				return ROCpt(x.get('tp'), x.get('fp'), x.get('tn'), x.get('fn'), label=x.get('label', ''))
			rocpts = [extract(x) for x in data]
			self.plot_positive_rates(rocpts)
			self.plot_negative_rates(rocpts)
			self.plot_f_rates2(rocpts)

			self.show()

	def show(self):
		
		if self.plot_on:
			if self.show_legend:
				pylab.legend(loc='best')
			pylab.show()

	def sort(self, data):
		# sorts the data and return the sorted data + the permutation indices
		return sorted(data), sorted(range(len(data)), key = data.__getitem__)

	def plot_positive_rates(self, data, label=''):

		if self.plot_on:
			if type(data) == type([]):
				rocpts = data
				fp_rates, indices = self.sort([rocpt.fp_rate() for rocpt in rocpts])
				tp_rates = [rocpt.tp_rate() for rocpt in rocpts]
				tp_rates = [tp_rates[indice] for indice in indices]
				AUC = np.trapz(tp_rates, fp_rates)

				pylab.subplot(1,3,1, title='Positive Rate, AUC = %2.2f' % AUC)
				pylab.plot([0,1],[0,1], ":k")
				pylab.axis([0,1,0,1])  
				pylab.xlabel('False positive rate.')
				pylab.ylabel('True positive rate.')
				pylab.grid(True)
				pylab.plot(fp_rates, tp_rates,"or", label=label)
				
	def plot_negative_rates(self, data, label=''):

		if self.plot_on:
			if type(data) == type([]):
				rocpts = data
				fn_rates, indices = self.sort([rocpt.fn_rate() for rocpt in rocpts])
				tn_rates = [rocpt.tn_rate() for rocpt in rocpts]
				tn_rates = [tn_rates[indice] for indice in indices]
				AUC = np.trapz(tn_rates, fn_rates)

				pylab.subplot(1,3,2, title='Negative Rate, AUC = %2.2f' % AUC)
				pylab.plot([0,1],[0,1], ":k")
				pylab.axis([0,1,0,1])  
				pylab.xlabel('False negative rate.')
				pylab.ylabel('True negative rate.')
				pylab.grid(True)
				pylab.plot(fn_rates, tn_rates,"or", label=label)

	def plot_f_rates(self, data, label=''):
		
		if self.plot_on:
			pylab.subplot(1,3,3, title='F-rates')
			pylab.axis([0,1,0,1])  
			pylab.xlabel('Positive F-measure.')
			pylab.ylabel('Negative F-measure.')
			pylab.grid(True)
			if type(data) == type([]):
				rocpts = data
				pos_f_measures = [rocpt.pos_f_measure() for rocpt in rocpts]
				neg_f_measures = [rocpt.neg_f_measure() for rocpt in rocpts]
				pylab.plot(neg_f_measures, pos_f_measures,"or", label=label)

	def plot_f_rates2(self, data, label=''):
		
		if self.plot_on:
			if type(data) == type([]):
				rocpts = data
				def fm1(x):
					if x.pos_precision() and x.neg_recall():
						return 2.0 / (1/x.pos_precision() + 1/x.neg_recall())
					else:
						return None

				def fm2(x):
					if x.neg_precision() and x.pos_recall():
						return 1.0 - 2.0 / (1/x.neg_precision() + 1/x.pos_recall())
					else:
						return None

				f1_measures = [fm1(rocpt) for rocpt in rocpts]
				f2_measures = [fm2(rocpt) for rocpt in rocpts]

				f1m = []
				f2m = []
				for i in range(len(f1_measures)):
					if f1_measures[i] is None or f2_measures[i] is None:
						pass
					else:
						f1m.append(f1_measures[i])
						f2m.append(f2_measures[i])
				f1_measures = f1m
				f2_measures = f2m
				AUC = -np.trapz(f1_measures, f2_measures)

				pylab.subplot(1,3,3, title='F-rates, AUC = %2.2f' % AUC)
				pylab.axis([0,1,0,1])  
				pylab.plot([0,1],[0,1], ":k")
				pylab.xlabel('F1-measure.')
				pylab.ylabel('F1-measure.')
				pylab.grid(True)
				pylab.plot(f2_measures, f1_measures,"or", label=label)

	def plot_x_rates(self, data, label=''):
		
		if self.plot_on:
			pylab.subplot(1,3,3, title='???')
			pylab.plot([0,1],[0,1], ":k")
			pylab.axis([0,1,0,1])  
			pylab.xlabel('Positive precision.')
			pylab.ylabel('negative recall.')
			pylab.grid(True)
			if type(data) == type([]):
				rocpts = data
				# fp_rates = [rocpt.fp_rate() for rocpt in rocpts]
				# tp_rates = [rocpt.tp_rate() for rocpt in rocpts]
				# fn_rates = [rocpt.fn_rate() for rocpt in rocpts]
				tn_rates = [rocpt.tn_rate() for rocpt in rocpts if rocpt.precision() is not None]
				pp = [rocpt.precision() for rocpt in rocpts if rocpt.precision() is not None]
				
				pylab.plot(tn_rates, pp,"or", label=label)			

	def generate_file(self, filename, data):

		content = json.dumps(dict(data=[dict(tp=tp,fp=fp,tn=tn,fn=fn,label=label, p=p) for tp, fp, tn, fn, label, p in data]))
		f = open(filename,'w')
		f.write(content)
		f.close()		

	def help(self):

		help_txt =  """
	# below are various ways to use the ROCPlot class

	roc_plot = ROCPlot()
	# define a number of points in ROC-space	
	rocpts = [ROCpt(12,2,13,2), ROCpt(22,6,7,3), ROCpt(22,3,14,7)]	
	# plot each point
	for rocpt in rocpts:
		roc_plot.plot(rocpt)
	# when done plotting points tell ROCPlot to show the final figure
	roc_plot.show()	

	# a data-file can be generated
	data = [(2,1,4,2),(6,2,5,1)]
	roc_plot.generate_file('roc_data.txt', data)

	# one can also load data from a filename
	roc_plot = ROCPlot(filename='roc_data.txt')
		"""
		print help_txt

help_message = '''USAGE: roc.py filename'''

def main():

	try:
		import sys
		filename = sys.argv[1]
	except:
		print help_message
		return

	ROCPlot(filename=filename, show_legend=False, fig_title=filename)

if __name__ == '__main__':
    main()