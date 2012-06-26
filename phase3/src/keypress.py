#!/usr/bin/env python

import sys
import cv2
import cv
import video
from common import anorm2, draw_str
import time

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
USAGE: keypress.py <video_source>'''

def main():
	try:
		video_src = sys.argv[1]
	except:
		print help_message
		return

	cap = video.create_capture(video_src)
	capture = cv.CaptureFromFile(video_src)
	fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
	num_frames = float(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT))

	keyDown = False
	states = []

	index = 0
	while True:

		ret, frame = cap.read()
		if ret:
			if len(states) == 0:
				# show first frame and let user decide if it is good or bad
				draw_str(frame, (20, 40), 'BAD')
				cv2.imshow('', frame)
				ch = cv2.waitKey(2500)
			else:
				ch = cv2.waitKey(int(1000/fps))

			if ch != -1: # key pressed
				keyDown = True if not keyDown else False

			if keyDown:
				state = 'GOOD'
				states.append(1)
			else:
				state = 'BAD'
				states.append(0)

			# draw_str(frame, (20, 40), state)
			draw_str(frame, (20, 20), '%s, %2d:%02d\t %2.2f%%' % (state, int((index / fps) / 60), int((index / fps) % 60), 100.0 * index / num_frames))
			cv2.imshow('', frame)

			index += 1
		else:
			# no more frames...
			break
	d = dict(states=states)
	content = json.dumps(d)

	# do not write a file if json parser fails
	if content:
		# write to disc
		f = open('%s.txt' % video_src,'w')	
		f.write(content)
		f.close()
	else:
		print 'error in json parser'

if __name__ == '__main__':
    main()