#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import math
import pylab
import time
import datetime
import roc
import os
import sys
import hashlib
import matplotlib.pyplot as pyplot
from mpl_toolkits.mplot3d import axes3d
import warnings
import seg_result_comparison as calcErr
simpleCompare = calcErr.simpleCompare
sectionCompareBetter = calcErr.sectionCompareBetter

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
import segment_stats
Segment = segment_stats.Segment

import compute_frame_state
computeFrameStateAnders = compute_frame_state.computeFrameStateAnders
computeFrameStateAnders2 = compute_frame_state.computeFrameStateAnders2
computeFrameStateSquare = compute_frame_state.computeFrameStateSquare
computeFrameStateCubic = compute_frame_state.computeFrameStateCubic
computeFrameStateLauge = compute_frame_state.computeFrameStateLauge
computeFrameStateMagnitudeOnly = compute_frame_state.computeFrameStateMagnitudeOnly
computeFrameStateContrastOnly = compute_frame_state.computeFrameStateContrastOnly

help_message = '''USAGE: roc.py <method> [outfile] [threads] [#param] [smoothness_degree]'''

finaltest_filename = 'finaltest2.json'

def get_hash(mylist=[]):

    algorithm = 'sha512'
    m = hashlib.new(algorithm)

    hash_string = ''.join(sorted(mylist))
    m.update(hash_string)
    
    return m.hexdigest()

def main():

	try:
		compare_method = sys.argv[1]
		if compare_method == 'simple':
			compare_method = simpleCompare
		elif compare_method == 'temporal':
			compare_method = sectionCompareBetter
		else:
			raise Exception
		smoothness_degree = int(sys.argv[2])
		tolerance = int(sys.argv[3])
	except Exception as e:
		print e
		return

	show_plot = False
	# smoothness_degree computed for 0 & 12 with simpleCompare
	# compare_method, smoothness_degree, tolerance = simpleCompare, 12, 0
	# computed for smoothness_degree = 0, tolerance = 24, 72, 120
	# compare_method, smoothness_degree, tolerance = sectionCompareBetter, 0, 120

	print 'compare method: %s, smoothness: %d' % (compare_method.__name__, smoothness_degree)
	if compare_method == sectionCompareBetter:
		print 'tolerance: %d' % tolerance

	tweak = tweak2.Tweak(method=None)
	x1,x2,x3,x4,x5 = tweak.fold(debug_mode=False)
	xs = [x1,x2,x3,x4,x5]

	def fY(x):
		if x.pos_precision() and x.neg_recall():
			return 2.0 / (1/x.pos_precision() + 1/x.neg_recall())
		else:
			return None

	def fX(x):
		if x.neg_precision() and x.pos_recall():
			return 1.0 - 2.0 / (1/x.neg_precision() + 1/x.pos_recall())
		else:
			return None	

	if os.path.isfile('./DataSet/%s' % finaltest_filename):
		f = open('./DataSet/%s' % finaltest_filename, 'r')
		content = f.read()
		finaltest = json.loads(content)
	else:
		finaltest = dict()

	# methods = [computeFrameStateLauge, computeFrameStateAnders, computeFrameStateMagnitudeOnly, computeFrameStateContrastOnly, computeFrameStateCubic]

	computeFrameStateLauge = compute_frame_state.computeFrameStateCummulative
	methods = [computeFrameStateLauge]
	
	# methods = [computeFrameStateAnders, computeFrameStateMagnitudeOnly, computeFrameStateContrastOnly, computeFrameStateCubic]
	for method in methods:
		print 'method: %s' % method.__name__

		data_dict = finaltest
		if compare_method != simpleCompare:
			key = '%s_%d' % (compare_method.__name__, tolerance)
			if not data_dict.get(key):
				data_dict[key] = dict()
			data_dict = data_dict[key]

		if not data_dict.get(method.__name__):
			data_dict[method.__name__] = dict()
		data_dict = data_dict[method.__name__]
		if not data_dict.get('smoothness_degree_%d' % smoothness_degree):
			data_dict['smoothness_degree_%d' % smoothness_degree] = dict()
		data_dict = data_dict['smoothness_degree_%d' % smoothness_degree]

		dists_test = []
		best_cords_train = []
		best_cords_test = []
		bad_seqs_total = []
		good_seqs_total = []
		best_params = []

		for i in range(len(xs)):

			params = np.linspace(0,1.0,101)[1:]
			if method == computeFrameStateLauge:
				params1 = np.linspace(0,1.0,101)[1:] # magnitude
				params2 = np.linspace(0,1.0,11)[1:] # contrast
				params = []
				for p1 in params1:
					for p2 in params2:
						params.append((p1,p2))

			train = [x for x in xs]
			del train[i]
			# flatten list
			train = sum(train, [])
			tweak_train = tweak2.Tweak(method=method, videoIDs=train, smoothness_degree=smoothness_degree, compare_method=compare_method, tolerance=tolerance)
			best_param = params[0]
			best_dist = math.sqrt(2)
			bx, by = 0,0

			if method == computeFrameStateLauge:
				ax = pyplot.figure(figsize=(8,8)).add_subplot(111, projection='3d')
				X,Y = np.meshgrid(np.linspace(0,1.0,11)[1:], np.linspace(0,1.0,101)[1:])
			else:
				pylab.figure(figsize=(10,10))
				pylab.axis([0,1,0,1])  
				pylab.xlabel('cost')
				pylab.ylabel('benefit')
				pylab.grid(True)
			
			files_fingerprint = get_hash(train)
			if not data_dict.get(files_fingerprint):
				data_dict[files_fingerprint] = dict()
			_data_dict = data_dict[files_fingerprint]

			Z = np.empty((100, 10))
			index = 0
			for p in params:
				if _data_dict.get('param_%s' % str(p)):
					res = _data_dict.get('param_%s' % str(p))
					truePositives, falsePositives, trueNegatives, falseNegatives = 	res.get('tp'), res.get('fp'), res.get('tn'), res.get('fn')
				else:
					# print 'computing result for method %s, parameter %s' % (method.__name__, str(p))
					if index % 25 == 0:
						print '%2.2f%% done (bucket #%d)' % (100.0 * index / len(params), i)
					truePositives, falsePositives, trueNegatives, falseNegatives = tweak_train.tweak(p=p)
					_data_dict['param_%s' % str(p)] = dict()
					_data_dict['param_%s' % str(p)]['tp'] = truePositives
					_data_dict['param_%s' % str(p)]['fp'] = falsePositives
					_data_dict['param_%s' % str(p)]['tn'] = trueNegatives
					_data_dict['param_%s' % str(p)]['fn'] = falseNegatives

				# print 'done for p = %f' % p
				roc_pt = roc.ROCpt(truePositives, falsePositives, trueNegatives, falseNegatives)
				x = fX(roc_pt)
				y = fY(roc_pt)
				if method == computeFrameStateLauge:
					Z[int(index / 10), index % 10] = y
					X[int(index / 10), index % 10] = x
					Y[int(index / 10), index % 10] = p[1]
				
				try:
					dist = math.sqrt((1-y)**2 + x**2)
				except:
					dist = math.sqrt(2)
					if method == computeFrameStateLauge:
						Z[int(index / 10), index % 10] = 0
						X[int(index / 10), index % 10] = 1
				else:	
					pass			
					# print 'dist = %2.2f' % dist
				index += 1
				if dist < best_dist:
					best_param = p
					best_dist = dist
					bx = x
					by = y
					# print 'new best parameter = %f, dist = %f, x = %f y = %f' % (best_param, best_dist, x, y)				
				if not method == computeFrameStateLauge:
					pylab.plot(x, y, "or")
			if method == computeFrameStateLauge:

				# prepend and append 0's and 1's
				X = np.concatenate((X,np.zeros((1,10))), axis=0)
				X = np.concatenate((np.ones((1,10)), X), axis=0)
				Z = np.concatenate((Z, np.zeros((1,10))), axis=0)
				Z = np.concatenate((np.ones((1,10)), Z), axis=0)
				Y = np.concatenate((np.array([np.linspace(0,1.0,11)[1:]]), Y), axis=0)
				Y = np.concatenate((Y, np.array([np.linspace(0,1.0,11)[1:]])), axis=0)

				for j in range(10):
					points = zip(Z[:,j], X[:,j], Y[:,j])
					points = sorted(points)
					X[:,j] = [p[1] for p in points]
					Z[:,j] = [p[0] for p in points]
					Y[:,j] = [p[2] for p in points]

				ax.plot_surface(X,Y,Z, rstride=1, cstride=1)
				ax.set_xlabel('cost')
				ax.set_ylabel('contrast')
				ax.set_zlabel('benefit')
				# pyplot.show()
			
			else:
				pylab.plot(bx, by, "ob")
				pylab.savefig('./figs/%s_%s_smooth%d_tol%d_bucket#%d' % (method.__name__, compare_method.__name__, smoothness_degree, tolerance, i))
			
			best_cords_train.append((bx,by))
			
			if show_plot:
				pylab.show()

			test = xs[i]
			tweak_test = tweak2.Tweak(method=method, videoIDs=test, smoothness_degree=smoothness_degree, compare_method=compare_method, tolerance=tolerance)
			files_fingerprint = get_hash(test)
			if not data_dict.get(files_fingerprint):
				data_dict[files_fingerprint] = dict()
			_data_dict = data_dict[files_fingerprint]

			if _data_dict.get('param_%s' % str(best_param)):
				res = _data_dict.get('param_%s' % str(best_param))
				truePositives, falsePositives, trueNegatives, falseNegatives = 	res.get('tp'), res.get('fp'), res.get('tn'), res.get('fn')
			else:
				truePositives, falsePositives, trueNegatives, falseNegatives = tweak_test.tweak(p=best_param)
				_data_dict['param_%s' % str(best_param)] = dict()
				_data_dict['param_%s' % str(best_param)]['tp'] = truePositives
				_data_dict['param_%s' % str(best_param)]['fp'] = falsePositives
				_data_dict['param_%s' % str(best_param)]['tn'] = trueNegatives
				_data_dict['param_%s' % str(best_param)]['fn'] = falseNegatives
			roc_pt = roc.ROCpt(truePositives, falsePositives, trueNegatives, falseNegatives)
			y = fY(roc_pt)
			x = fX(roc_pt)
			dist = math.sqrt((1-y)**2 + x**2)
			dists_test.append(dist)

			best_params.append(best_param)
			if method == computeFrameStateLauge:
				print 'distance for best parameter((%2.2f, %2.2f)): %2.2f' % (best_param[0], best_param[1], dist)
			else:
				print 'distance for best parameter(%2.2f): %2.2f' % (best_param, dist)

			best_cords_test.append((x,y))

			# avr. segment lengths ao.
			_data_dict = _data_dict['param_%s' % str(best_param)]
			if not _data_dict.get('segment_stats'):
				_data_dict['segment_stats'] = dict()
			_data_dict = _data_dict['segment_stats']

			print 'computing segment lengths...'
			for vid_id in test:
				if _data_dict.get(vid_id):
					bad_seqs, good_seqs = _data_dict[vid_id]['bad_seqs'], _data_dict[vid_id]['good_seqs']
				else:
					# print 'computing segment lenght for method %s, ID %s, parameter %s' % (method.__name__, vid_id, str(best_param))
					segment = Segment('./DataSet/frame_states/%s/%s.%s.smoo%d.txt' % (method.__name__, vid_id, str(best_param), smoothness_degree))
					bad_seqs, good_seqs = segment.compute()
					_data_dict[vid_id] = dict()
					_data_dict[vid_id]['bad_seqs'] = bad_seqs
					_data_dict[vid_id]['good_seqs'] = good_seqs
				bad_seqs_total += bad_seqs
				good_seqs_total += good_seqs

		# end "for i in range(buckets):"
		
		if method == computeFrameStateLauge:
			best_params1 = [x[0] for x in best_params]
			best_params2 = [x[1] for x in best_params]
			print 'param: (%2.3f,%2.3f), std. dev. (%2.1f, %2.1f)%% '% (np.mean(best_params1), np.mean(best_params2), 100 * np.std(best_params1) / np.mean(best_params1), 100 * np.std(best_params2) / np.mean(best_params2))
		else:
			print 'param: %2.3f, std. dev. %2.1f%% '% (np.mean(best_params), 100 * np.std(best_params) / np.mean(best_params))

		pylab.figure(figsize=(7,7))
		pylab.axis([0,1,0,1])  
		pylab.xlabel('cost')
		pylab.ylabel('benefit')
		pylab.grid(True)
		for x,y in best_cords_train:
			pylab.plot(x, y, "ob")
		for x,y in best_cords_test:
			pylab.plot(x, y, "or")
		pylab.savefig('./figs/%s_%s_smooth%d_tol%d' % (method.__name__, compare_method.__name__, smoothness_degree, tolerance))

		print 'avr. distance score: %2.2f, std. dev. %2.2f%%' % (np.mean(dists_test), 100.0 * np.std(dists_test) / np.mean(dists_test))
		print 'avr. good sequence lenght: %2.1f, std. dev. %2.1f%%, median: %2.1f' % (np.mean(good_seqs_total), 100.0 * np.std(good_seqs_total) / np.mean(good_seqs_total), np.median(good_seqs_total))
		print 'avr. bad sequence lenght: %2.1f, std. dev. %2.1f%%, median: %2.1f' % (np.mean(bad_seqs_total), 100.0 * np.std(bad_seqs_total) / np.mean(bad_seqs_total), np.median(bad_seqs_total))
		print 'longest good sequence: %d, shortest good sequence: %d' % (max(good_seqs_total), min(good_seqs_total))
		print 'longest bad sequence: %d, shortest bad sequence: %d' % (max(bad_seqs_total), min(bad_seqs_total))

		##########################
		# AUC for entire dataset #
		##########################

		print 'computing AUC'

		params = np.linspace(0,1.0,101)[1:]
		if method == computeFrameStateLauge:
			params1 = np.linspace(0,1.0,101)[1:] # magnitude
			params2 = np.linspace(0,1.0,11)[1:] # contrast
			params = []
			for p1 in params1:
				for p2 in params2:
					params.append((p1,p2))

		data_set = [x for x in xs]
		# flatten list
		data_set = sum(data_set, [])
		tweak_tweak = tweak2.Tweak(method=method, videoIDs=data_set, smoothness_degree=smoothness_degree, compare_method=compare_method, tolerance=tolerance)
		fx_measures = [0]
		fy_measures = [0]

		if method == computeFrameStateLauge:
			ax = pyplot.figure(figsize=(8,8)).add_subplot(111, projection='3d')
			X,Y = np.meshgrid(np.linspace(0,1.0,11)[1:], np.linspace(0,1.0,101)[1:])
		else:
			pylab.figure(figsize=(7,7))
			pylab.axis([0,1,0,1])  
			pylab.xlabel('cost')
			pylab.ylabel('benefit')
			pylab.grid(True)

		files_fingerprint = get_hash(data_set)
		if not data_dict.get(files_fingerprint):
			data_dict[files_fingerprint] = dict()
		_data_dict = data_dict[files_fingerprint]		

		index = 0
		Z = np.empty((100, 10))
		for p in params:
			if _data_dict.get('param_%s' % str(p)):
				res = _data_dict.get('param_%s' % str(p))
				truePositives, falsePositives, trueNegatives, falseNegatives = 	res.get('tp'), res.get('fp'), res.get('tn'), res.get('fn')
			else:
				# print 'computing result for method %s, parameter %s' % (method.__name__, str(p))
				if index % 25 == 0:
					print '%2.2f%% done' % (100.0 * index / len(params))				
				truePositives, falsePositives, trueNegatives, falseNegatives = tweak_tweak.tweak(p=p)
				_data_dict['param_%s' % str(p)] = dict()
				_data_dict['param_%s' % str(p)]['tp'] = truePositives
				_data_dict['param_%s' % str(p)]['fp'] = falsePositives
				_data_dict['param_%s' % str(p)]['tn'] = trueNegatives
				_data_dict['param_%s' % str(p)]['fn'] = falseNegatives			
			
			# truePositives, falsePositives, trueNegatives, falseNegatives = 	res.get('tp'), res.get('fp'), res.get('tn'), res.get('fn')
		
			# truePositives, falsePositives, trueNegatives, falseNegatives = tweak_tweak.tweak(p=p)
			# print 'done for p = %f' % p
			roc_pt = roc.ROCpt(truePositives, falsePositives, trueNegatives, falseNegatives)
			y = fY(roc_pt)
			x = fX(roc_pt)

			if method == computeFrameStateLauge:
				Z[int(index / 10), index % 10] = y
				X[int(index / 10), index % 10] = x
				Y[int(index / 10), index % 10] = p[1]
			try:
				dist = math.sqrt((1-y)**2 + x**2)
			except:
				if method == computeFrameStateLauge:
					Z[int(index / 10), index % 10] = 0
					X[int(index / 10), index % 10] = 1
			else:
				if not method == computeFrameStateLauge:
					pylab.plot(x, y, "ok")
					fx_measures.append(x)
					fy_measures.append(y)
			index += 1

		if method == computeFrameStateLauge:

			# prepend and append 0's and 1's
			X = np.concatenate((X,np.zeros((1,10))), axis=0)
			X = np.concatenate((np.ones((1,10)), X), axis=0)
			Z = np.concatenate((Z, np.zeros((1,10))), axis=0)
			Z = np.concatenate((np.ones((1,10)), Z), axis=0)
			Y = np.concatenate((np.array([np.linspace(0,1.0,11)[1:]]), Y), axis=0)
			Y = np.concatenate((Y, np.array([np.linspace(0,1.0,11)[1:]])), axis=0)

			for i in range(10):
				points = zip(Z[:,i], X[:,i], Y[:,i])
				points = sorted(points)
				X[:,i] = [p[1] for p in points]
				Z[:,i] = [p[0] for p in points]
				Y[:,i] = [p[2] for p in points]
			
			ax.plot_surface(X,Y,Z, rstride=1, cstride=1)
			ax.set_xlabel('cost')
			ax.set_ylabel('contrast')
			ax.set_zlabel('benefit')
			
			AUCs = []
			for i in range(10):			
				AUCs.append(np.trapz(Z[:,i], X[:,i]))

			print 'AUC(mean) = %2.2f, std. dev. = %2.2f%%' % (np.mean(AUCs), 100.0 * np.std(AUCs) / np.mean(AUCs))
			# pyplot.show()
		else:
			pylab.plot(1, 1, "ok")
			pylab.plot(0, 0, "ok")

			fx_measures.append(1)
			fy_measures.append(1)
			points = zip(fx_measures, fy_measures)
			points = sorted(points)
			fx_measures = [p[0] for p in points]
			fy_measures = [p[1] for p in points]

			AUC = np.trapz(fy_measures, fx_measures)		
			print 'AUC = %2.2f' % AUC

		if not method == computeFrameStateLauge:
			pylab.savefig('./figs/%s_%s_smooth%d_tol%d_AUC' % (method.__name__, compare_method.__name__, smoothness_degree, tolerance))
		
	content = json.dumps(finaltest)
	# write to disc
	f = open('./DataSet/%s' % finaltest_filename,'w')	
	f.write(content)
	f.close()	

if __name__ == '__main__':
    main()    	