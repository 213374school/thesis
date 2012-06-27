#!/usr/bin/python

import os
import threading
import time
import Queue
import sys
import cv2
import json
import math
import numpy as np
import vid_segmenter as segmenter
getVideoMetadata = segmenter.getVideoMetadata
smoothTriangle = segmenter.smoothTriangle
from compute_frame_state import computeFrameStateAnders as computeFrameState

help_message = '''
USAGE: %s <video_source_folder>''' % __file__

def main():

	try:
		path = sys.argv[1]
	except:
		print help_message
		return

	listing = [filename for filename in os.listdir(path) if filename.split('.')[-1] in ['m4v','avi']]

	for filename in listing:
		video_src = '%s%s' % (path, filename)
		filename = video_src.split('/')[-1]
		ytid = filename.split('.')[0]	
		metadata_filename = './metadata/%s.json' % ytid

		metadata,frames = getVideoMetadata(video_src)

		# quality analysis - computation time is very short, but we must get the optimal parameter, p, at some point
		shift_vectors = metadata['phase1']['shift_vectors']
		stand_dev = metadata['phase1']['stand_dev']
		
		# from tweak.py
		degree = 12
		try:
			magnitudes = smoothTriangle((np.array([math.sqrt(x**2 + y**2) for x,y in shift_vectors])**2)/(63**2), degree)	
			contrast = smoothTriangle((127.5 - np.array(stand_dev)) / 127.5, degree)
		except IndexError as e:
			# too little data in segment will cause this error
			print 'error in %s when computing magnitudes and contrast' % ytid
			continue

		states, state_values = computeFrameState(magnitudes, contrast, p=0.015)
		metadata['frame_states'] = states

		content = json.dumps(metadata)
		# do not write a file if json parser fails
		if content:
			# write to disc
			f = open(metadata_filename,'w')	
			f.write(content)
			f.close()
		else:
			print '\nerror when writing metadata for %s' % ytid		
		
if __name__ == '__main__':
    main()