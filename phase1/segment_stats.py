#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

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

help_message = '''USAGE: xxx.py filename'''

class Segment():

	def __init__(self, filename):
		self.filename = filename

	def compute(self):

		f = open(self.filename,'r')
		content = f.read()
		content = json.loads(content)		
		f.close()

		states = content.get('frame_states', [])

		# array of sequence lengths for zeroes and ones
		bad_seqs = []
		good_seqs = []

		bsl = 0
		gsl = 0
		prev_state = states[0]
		for index in range(len(states)):
			
			state = states[index]
			if state != prev_state or index == len(states)-1:
				if index == len(states)-1:
					if state:
						gsl += 1
					else:
						bsl += 1
				if gsl:
					good_seqs.append(gsl)
				else:
					bad_seqs.append(bsl)
				gsl = 0
				bsl = 0

			if state:
				gsl += 1
			else:
				bsl += 1
			prev_state = state

		# import os
		# os.system('clear')

		# print 'bad sequences', bad_seqs
		# print 'good sequences', good_seqs

		# print 'bad sequences (sorted)', sorted(bad_seqs)
		# print 'good sequences (sorted)', sorted(good_seqs)

		# print '\n#frames: %d\n' % len(states)

		# print '#bad state sequences: %d' % len(bad_seqs)
		# print 'longest bad state sequences: %d' % (max(bad_seqs) if bad_seqs else 0)
		# print 'mean bad state sequence length: %d' % int(np.mean(bad_seqs))
		# print 'std. dev. bad state sequence length: %d' % int(np.std(bad_seqs))
		# print 'median bad state sequence length: %d' % int(np.median(bad_seqs))

		# print ''

		# print '#good state sequences: %d' % len(good_seqs)
		# print 'longest good state sequences: %d' % (max(good_seqs) if good_seqs else 0)
		# print 'mean good state sequence length: %d' % int(np.mean(good_seqs))
		# print 'std. dev. good state sequence length: %d' % int(np.std(good_seqs))
		# print 'median good state sequence length: %d' % int(np.median(good_seqs))

		return bad_seqs, good_seqs

def main():

	try:
		import sys
		filename = sys.argv[1]
	except:
		print help_message
		return

	segment = Segment(filename)
	segment.compute()

if __name__ == '__main__':
    main()
