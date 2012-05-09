#!/usr/bin/env python

import cv2
import cv
import video
from common import anorm2, draw_str
import time
import sys
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

help_message = '''
USAGE: keypress2.py <video_source> [-?]
-o to override saved cuts
'''

def main():
	argv = sys.argv
	try:
		video_src = argv[1]
	except:
		print help_message
		return

	override = True if len(argv) > 2 and argv[2] == '-o' else False
	cuts_filename = '%s_cuts.txt' % video_src

	if override:
		os.remove(cuts_filename)

	cut_indexes = []
	if os.path.isfile(cuts_filename):
		f = open(cuts_filename,'r')
		content = f.read()
		d = json.loads(content)
		cut_indexes = d.get('cut_indexes', [])

	
	capture = cv.CaptureFromFile(video_src)
	fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	num_frames = float(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT))
	# t = np.linspace(0, num_frames/fps, num_frames)

	if not cut_indexes:
		cap = video.create_capture(video_src)
		human_delay = int(60.0 / fps) # X ms
		index = 0
		# show cut across the screen for this many frames
		countdown = 0
		while True:

			ret, frame = cap.read()
			if ret:
				
				ch = cv2.waitKey(int(1000/fps))

				if ch != -1: # key pressed
					# do cut
					cut_index = max(0, index-human_delay)
					cut_indexes.append(cut_index)
					countdown = 15
					# print 'cut at frame #%d: %2.2f' % (cut_index, cut_index * fps / 1000.0)
					
				if countdown > 0:
					draw_str(frame, (320, 180), 'CUT')
					countdown -= 1
				
				draw_str(frame, (20, 20), 'frame #%d: %2d:%02d -- %2.2f%%' % (index, int((index / fps) / 60), int((index / fps) % 60), 100.0 * index / num_frames))
				cv2.imshow('', frame)

				index += 1
			else:
				# no more frames...
				break

		d = {'cut_indexes' : cut_indexes}
		content = json.dumps(d)

		# do not write a file if json parser fails
		if content:
			# write to disc
			f = open(cuts_filename,'w')	
			f.write(content)
			f.close()

	part = 0
	fourcc = cv.CV_FOURCC('D','I','V','3') # MPEG-4.3
	width = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
	height =  int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
	frame_size = (int(width), int(height))
	index = 0
	frame_offset = int(fps/4.0)
	for cut_index in cut_indexes:
		# print '%d -> %d' % (index, cut_index - frame_offset)
		writer = cv.CreateVideoWriter("./%s_part%03d.avi" % (video_src.split('.')[-2], part), fourcc, fps, frame_size, 1)
		for i in range(index, cut_index - frame_offset):
			frame = cv.QueryFrame(capture)
			cv.WriteFrame(writer, frame)
			index += 1

		# skip "frame_offset" frames on each side of the cut
		for i in range(index, index + 2 * frame_offset):
			frame = cv.QueryFrame(capture)
			index += 1
		part += 1

	# print 'writing last part'
	writer = cv.CreateVideoWriter("./%s_part%03d.avi" % (video_src.split('.')[-2], part), fourcc, fps, frame_size, 1)
	while True:
		try:
			frame = cv.QueryFrame(capture)
			cv.WriteFrame(writer, frame)
		except Exception as e:
			# print e
			break

if __name__ == '__main__':
    main()
    