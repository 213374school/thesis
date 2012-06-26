#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import math
import pylab
import time
import datetime
import roc
import os

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

import tweak2
import threading
import Queue
from multiprocessing import Process, Pipe

class Worker(threading.Thread):

	def __init__(self, in_queue, out_queue, method, smoothness_degree=0):
		threading.Thread.__init__(self)

		self.label = str(method.__name__)
		self.tweak = tweak2.Tweak(method, smoothness_degree=smoothness_degree)
		self.in_queue = in_queue
		self.out_queue = out_queue

	def run(self):

		while True:

			#grabs parameter from queue
			p = self.in_queue.get()

			tp,fp,tn,fn = self.tweak.tweak(p)	
			label = self.label

			result = tp,fp,tn,fn, label, p
			self.out_queue.put(result, block=False)

			#signals to queue job is done
			self.in_queue.task_done()

class Gatherer(threading.Thread):

	def __init__(self, in_queue, num_results, filename):
		threading.Thread.__init__(self)

		self.in_queue = in_queue
		self.num_results = num_results
		self.filename = filename
		self.data = []

	def run(self):

		# stop = False
		while True:

			#grabs result from queue and append to data
			result = self.in_queue.get()
			self.data.append(result)
			
			print '%d, %d' % (len(self.data), self.num_results)

			if len(self.data) == self.num_results:
				# stop = True
				roc_plot = roc.ROCPlot(plot_on=False)
				roc_plot.generate_file(self.filename, self.data)

			#signals to queue job is done
			self.in_queue.task_done()

import compute_frame_state
computeFrameStateAnders = compute_frame_state.computeFrameStateAnders
computeFrameStateAnders2 = compute_frame_state.computeFrameStateAnders2
computeFrameStateSquare = compute_frame_state.computeFrameStateSquare
computeFrameStateCubic = compute_frame_state.computeFrameStateCubic
computeFrameStateLauge = compute_frame_state.computeFrameStateLauge
computeFrameStateMagnitudeOnly = compute_frame_state.computeFrameStateMagnitudeOnly
computeFrameStateContrastOnly = compute_frame_state.computeFrameStateContrastOnly

help_message = '''USAGE: roc.py <method> [outfile] [threads] [#param] [smoothness_degree]'''

def main():

	# roc_plot = ROCPlot()
	# data = [(2,1,4,2,'A'),(6,2,5,1,'B')]
	# roc_plot.generate_file('roc_data.txt', data)

	# roc_plot = ROCPlot(filename='roc_data.txt')

	# WTF???
	# 16 threads, 16 params: 2:11
	# 4 threads, 16 params: 2:02
	# 2 threads, 16 params: 2:07
	# 32 threads, 64 params: 

	try:
		import sys
		method_name = sys.argv[1]		
	except:
		print help_message
		return	

	try:
		outfile = sys.argv[2]
	except:
		outfile = 'roc_out_%s.txt' % method_name

	try:
		threads = int(sys.argv[3])
	except:
		threads = 4

	try:
		num_params = sys.argv[4]
	except:
		num_params = 100

	try:
		smoothness_degree = int(sys.argv[5])
	except:
		smoothness_degree = 0

	if method_name == 'anders':
		method = computeFrameStateAnders
	elif method_name == 'square':
		method = computeFrameStateSquare
	elif method_name == 'cubic':
		method = computeFrameStateCubic
	elif method_name == 'anders2':
		method = computeFrameStateAnders2
	elif method_name == 'magnitude':
		method = computeFrameStateMagnitudeOnly
	elif method_name == 'contrast':
		method = computeFrameStateContrastOnly
	elif method_name == 'lauge':
		method = computeFrameStateLauge

	filename = outfile
	generate_data = True
	if generate_data:
		start = time.time()

		data = []
		import compute_frame_state	
		# params = np.append(np.linspace(1e-6,1.0,96), np.linspace(0.5+1e-6,1,20))
		params = np.linspace(0,1.0,101)[1:]
		if method_name == 'lauge':
			params1 = np.linspace(0,1.0,101)[1:] # magnitude
			params2 = np.linspace(0,1.0,11)[1:] # contrast
			params = []
			for p1 in params1:
				for p2 in params2:
					params.append((p1,p2))
			# try:
			# 	fix_param = float(sys.argv[5])
			# except:
			# 	print 'must choose a fixed parameter'
			# 	return
			# else:
			# 	print 'fixed parameter at %2.2f' % fix_param
			# fix one parameter and iterate the other
			# magnitude, contrast
			# params = [(fix_param, x) for x in params]

		print 'generating data with %d threads. #parameters: %d' % (threads, len(params))


		path = './DataSet/frame_states/%s' % (method.__name__)
		if not os.path.exists(path):
			os.makedirs(path)

		threads = min(threads, len(params))
		in_queue = Queue.Queue()
		out_queue = Queue.Queue()
		#spawn a pool of threads, and pass them queue instance 
		for i in range(threads):
			print 'spawning worker #%d' % i
			t = Worker(in_queue, out_queue, method, smoothness_degree)
			t.setDaemon(True)
			t.start()

		print 'spawning gatherer'
		t = Gatherer(out_queue, len(params), filename)
		t.setDaemon(True)
		t.start()	

		#populate queue with data   
		for p in params:
			if method_name == 'lauge':
				print 'adding: %s(%f,%f)' % (method.__name__, p[0], p[1])
			else:
				print 'adding: %s(%f)' % (method.__name__, p)
			in_queue.put(p)

		print 'waiting for jobs to complete...'
		#wait on the queue until everything has been processed     
		in_queue.join()
		print 'workers done!'
		out_queue.join()
		print 'gatherer done!'
		print 'Done and done!'

		end = time.time()

		elapsed_time = end - start
		print 'elapsed time: %d:%02d' % (int(elapsed_time/60.0), int(elapsed_time % 60.0))

	# roc.ROCPlot(filename=filename, show_legend=False)

if __name__ == '__main__':
    main()    	