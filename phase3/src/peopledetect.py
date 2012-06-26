#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import cv2.cv as cv
from cv2.cv import *
import video
import cv2
# for printing on one line
from sys import stdout
import os
import math
import pylab
import numpy as np
import numpy

# Find a JSON parser
try:
	import json
except ImportError:
	try:
		import simplejson as json
	except ImportError:
		print 'ERROR: JSON parser not found!'

helptxt = """usage:\n./peopledetect.py src_folder [-v] [-p] [ytid]
-v show video
-p show plot
ytid YouTube ID"""

from collections import deque

def smoothTriangle(lst=[], degree=1):

	if degree < 1:
		print 'degree must be > 1'
		return

	triangle = numpy.array(range(degree)+[degree]+range(degree)[::-1])+1
	lst = numpy.array(lst)
	lst_lenght = len(lst)
	tri_len = len(triangle)
	_max = lst_lenght - degree
	triangle_normal_sum = float(sum(triangle))
	
	smoothed_lst = []
	for i in range(lst_lenght):

		if i > degree and i < _max:
			new_value = sum(triangle * lst[i-degree:i+degree+1]) / triangle_normal_sum
		else:
			left = degree - min(i, degree)
			right = degree + min(degree, lst_lenght - 1 - i) + 1			
			tri = triangle[left:right]
			triangle_sum = sum(tri)

			new_value = 0.0
			for j in range(len(tri)):

				pos = j + i + left - degree
				new_value += tri[j] * lst[pos]
		
			new_value /= triangle_sum

		smoothed_lst.append(new_value)

	return smoothed_lst

class Simplemovingaverage():
	def __init__(self, period):
		assert period == int(period) and period > 0, "Period must be an integer >0"
		self.period = period
		self.stream = deque()
 
	def __call__(self, n):
		stream = self.stream
		stream.append(n)	# appends on the right
		streamlength = len(stream)
		if streamlength > self.period:
			stream.popleft()
			streamlength -= 1
		if streamlength == 0:
			average = 0
		else:
			average = sum( stream ) / streamlength
 
		return average

def get_ytids_lib(metadata_folder):

		# first check 'metadata_folder'
		if os.path.isdir('%s/bodydetect' % metadata_folder) and os.path.isdir('%s/profile' % metadata_folder) and os.path.isdir('%s/facedetect' % metadata_folder):
			filename = '%s/%s' % (metadata_folder, 'ytids.json')
			if not os.path.isfile(filename):
				folder_bd = '%s/bodydetect' % metadata_folder
				folder_pr = '%s/profile' 	% metadata_folder
				folder_fd = '%s/facedetect' % metadata_folder

				files_bd = [f for f in os.listdir(folder_bd) if f.split('.')[-1] in ['json']]
				files_pr = [f for f in os.listdir(folder_pr) if f.split('.')[-1] in ['json']]
				files_fd = [f for f in os.listdir(folder_fd) if f.split('.')[-1] in ['json']]

				ytids = []
				if len(files_fd) == len(files_pr) and len(files_pr) == len(files_bd):
					files_bd = sorted(files_bd)
					files_pr = sorted(files_pr)
					files_fd = sorted(files_fd)
					for i in range(len(files_fd)):
						ytid_fd = json.loads(open('%s/bodydetect/%s' % (metadata_folder, files_fd[i]),'r').read()).get('ytid')
						ytid_bd = json.loads(open('%s/bodydetect/%s' % (metadata_folder, files_bd[i]),'r').read()).get('ytid')
						ytid_pr = json.loads(open('%s/bodydetect/%s' % (metadata_folder, files_pr[i]),'r').read()).get('ytid')
						if ytid_pr and ytid_bd and ytid_fd and ytid_fd == ytid_pr and ytid_pr == ytid_bd:
							ytids.append(ytid_pr)
				else:
					print 'mismatch in metadata!'
					return None
				ytids_lib = dict(ytids=ytids)
				if ytids_lib:
					f = open(filename,'w') 
					f.write(json.dumps(ytids_lib))
					f.close()
			else:
				ytids_lib = json.loads(open(filename,'r').read())
			# print ytids_lib
			return ytids_lib
		else:
			print 'invalid folder: %s. must contain following dirs: "bodydetect, profile, facedetect"' % metadata_folder
			return None

def get_video(metadata_folder, ytid):

	data_folder = '%s/../data' % metadata_folder
	cap, fps, w, h, num_frames = None, -1, -1, -1, -1
	for i in range(1,5):
		# check each "coreX" folder
		exts = ['m4v', 'avi']
		for ext in exts:
			if os.path.isfile('%s/core%d/%s.%s' % (data_folder, i, ytid, ext)):
				# print '%s found in: "core%d"' % (ytid, i)
				video_src = '%s/core%d/%s.%s' % (data_folder, i, ytid, ext)
				cap = video.create_capture(video_src)
				capture = cv.CaptureFromFile(video_src)
				fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
				w = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
				h =  int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
				num_frames = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT) - 3 # always 3 too many????

	return cap, fps, w, h, num_frames

# rectangle that encapsulates the center of the image (any object detected within these boundaries are in focus)
center_rectangle = ((200, 30), (440, 270))

def is_in_focus_center(x,y,w,h):

	ul, lr = center_rectangle
	cx, cy = (x+w/2, y+h/2)
	return cx >= ul[0] and cx <= lr[0] and cy >= ul[1] and cy <= lr[1]

def main():
	try:
		video_src = sys.argv[1]
	except:
		print helptxt
	else:
		show_video = False
		show_plot = False
		ytid = None
		try:
			args = sys.argv[2:]
		except:
			args = []
		for arg in args:
			if arg == '-v':
				show_video = True
			elif arg == '-p':
				show_plot = True
			elif arg == '-?':
				print helptxt
				return
			else:
				ytid = arg

		# ytids_lib = get_ytids_lib(metadata_folder)

		### display youtube id's and their index
		# i = 0
		# for v in ytids_lib.get('ytids'):
		# 	print '%d: %s' % (i, v)
		# 	i += 1

		# ytids = ytids_lib.get('ytids', [])
		# if ytid:
		# 	ytids = [ytid]
		# ytids = [ytids[10]] # 10,20 = tale, 32 = tæt på i crowd, 33 = a bit of everything
		# for ytid in ytids:

		filename = video_src.split('/')[-1]
		ytid = filename.split('.')[0]
		metadata_folder = './metadata'

		bd = json.loads(open('%s/bodydetect/%s.json' % (metadata_folder, ytid),'r').read())
		fd = json.loads(open('%s/facedetect/%s.json' % (metadata_folder, ytid),'r').read())
		pr = json.loads(open('%s/profile/%s.json'	% (metadata_folder, ytid),'r').read())
		
		cap, fps, vw, vh, num_frames = get_video(metadata_folder, ytid)
		if not cap:
			print 'error in %s' % ytid
			return
			# continue
			
		font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1.0, 1.0)
		body = bd.get('body')
		face = fd.get('faces')
		prof = pr.get('profile')

		# check for consistency
		if len(body) == len(face) and len(face) == len(prof):
			detected_objects = [body[i] + face[i] + prof[i] for i in range(len(body))]

		index = 0
		person_in_focus_frames_count = 0
		people_in_frame_count = 0
		in_crowds = []
		in_focus = []
		# minimum number of neighboring rectangles (7 or 8 seems like a good value - there is an article where they determine that 7 is the best REF!!!)
		n_min = 7 # *PARAM*

		# setup simple moving average
		period = 4 # *PARAM*
		ppl_cnt_sma = Simplemovingaverage(period)
		period = 4 # *PARAM*
		focus_sma = Simplemovingaverage(period)
		period = 12 # *PARAM*
		incrowd_sma = Simplemovingaverage(period)

		def compute_area(w,h):
			return w*h

		imgs = []
		largest_bounding_rectangle_areas = []
		people_counts = []
		while True:
			ret, frame = cap.read()
			if ret:
				img = cv.fromarray(frame)
			else:
				break

			# nice to know :D
			stdout.write('computing: %2.1f%%\r' % (100.0 * index / num_frames))
			stdout.flush()

			people_count = 0
			person_in_focus_center = False
			largest_bounding_rectangle_area = 0
			for (x,y,w,h),n in body[index]:
				color = cv.RGB(25, 25, 112) # midnight blue 25-25-112
				if n > n_min:
					# area = compute_area(w,h)
					# if area > largest_bounding_rectangle_area:
					# 	largest_bounding_rectangle_area = area
					people_count += 1
					cv.Rectangle(img, (x,y), (x+w,y+h), color)
					cv.PutText(img, 'B', (x+w/2,y+h/2), font, color)
					if not person_in_focus_center:
						person_in_focus_center = is_in_focus_center(x,y,w,h)
			for (x,y,w,h),n in face[index]:
				color = cv.RGB(0, 100, 0) # dark green 0-100-0
				if n > n_min:
					area = compute_area(w,h)
					if area > largest_bounding_rectangle_area:
						largest_bounding_rectangle_area = area						
					people_count += 1
					cv.Rectangle(img, (x,y), (x+w,y+h), color)						
					cv.PutText(img, 'F', (x+w/2,y+h/2), font, color)
					if not person_in_focus_center:
						person_in_focus_center = is_in_focus_center(x,y,w,h)
			for (x,y,w,h),n in prof[index]:
				color = cv.RGB(178, 34, 34) # firebrick 178-34-34
				if n > n_min:
					area = compute_area(w,h)
					if area > largest_bounding_rectangle_area:
						largest_bounding_rectangle_area = area						
					people_count += 1
					cv.Rectangle(img, (x,y), (x+w,y+h), color)						
					cv.PutText(img, 'P', (x+w/2,y+h/2), font, color)
					if not person_in_focus_center:
						person_in_focus_center = is_in_focus_center(x,y,w,h)

			largest_bounding_rectangle_areas.append(largest_bounding_rectangle_area)

			index += 1

			# person in center focus
			person_in_focus_center = round(focus_sma(int(person_in_focus_center)))
			color = cv.RGB(255, 0, 0) # red
			if person_in_focus_center:
				color = cv.RGB(0, 255, 0) # green
				person_in_focus_frames_count += 1
			ul, lr = center_rectangle
			cv.Rectangle(img, ul, lr, color)

			# before moving avr.
			people_counts.append(people_count)

			# people count
			people_count = ppl_cnt_sma(float(people_count))
			color = cv.RGB(255, 0, 0) # red
			if people_count:
				color = cv.RGB(0, 255, 0) # green
				people_in_frame_count += 1

			# are we (with)in a crowd? *PARAM*
			in_crowd = round(incrowd_sma(int(people_count > 1))) == 1

			cv.PutText(img, '%02d:%02d of %02d:%02d' % (index / fps / 60, (index / fps) % 60, num_frames / fps / 60, (num_frames / fps) % 60), (vw - 130, 16), font, cv.RGB(0, 0, 0))

			cv.PutText(img, 'mov. avr. people count: %d' % people_count, (4, 16), font, color)
			cv.PutText(img, 'in crowd: %s' % str(in_crowd), (4, 32), font, cv.RGB(0, 255, 0) if people_count > 1 else cv.RGB(255, 0, 0))
			cv.PutText(img, 'people in frame count: %d (%2.1f%%)' % (people_in_frame_count, 100.0 * people_in_frame_count / index), (4, vh-int(1.0*24)), font, cv.RGB(255, 255, 255))
			cv.PutText(img, 'person in focus count: %d (%2.1f%%)' % (person_in_focus_frames_count, 100.0 * person_in_focus_frames_count / index), (4, vh-int(0.5*24)), font, cv.RGB(255, 255, 255))

			if show_video:
				imgs.append(img)
			in_crowds.append(int(in_crowd))
			in_focus.append(person_in_focus_center)

		# out = json.dumps(dict(in_crowds=in_crowds, in_focus=in_focus, largest_bounding_rectangle_areas=largest_bounding_rectangle_areas, people_counts=people_counts))
		out = json.dumps(dict(in_focus=in_focus, largest_bounding_rectangle_areas=largest_bounding_rectangle_areas, people_counts=people_counts))
		# do not write a file if json parser fails
		if out:
			# write to disc
			f = open('%s/peopledetect/%s.json' % (metadata_folder, ytid),'w') 
			f.write(out)
			f.close()

		stdout.write('computing: %2.1f%% done\r' % 100.0)
		stdout.flush()
		print ''

		if show_video:
			for img in imgs:
				ShowImage("people detection demo, %s" % ytid, img)
				cv2.waitKey(int(1000.0/fps))

		if show_plot:

			t = np.linspace(0, num_frames/fps, num_frames)

			pylab.figure(figsize=(10,10))		
			pylab.suptitle('%s' % ytid, fontsize=16)

			in_crowds_smooth = smoothTriangle(in_crowds, 6)
			pylab.subplot(2,1,1, title='in crowd')
			pylab.plot(t, in_crowds_smooth,".k")  
			pylab.plot(t, in_crowds_smooth,"-k")  
			pylab.axis([0,t[-1],0,1.1])
			pylab.xlabel('secs.')
			pylab.grid(True)

			in_focus_smooth = smoothTriangle(in_focus, 6)
			pylab.subplot(2,1,2, title='in focus')
			pylab.plot(t, in_focus_smooth,".k")  
			pylab.plot(t, in_focus_smooth,"-k")  
			pylab.axis([0,t[-1],0,1.1])
			pylab.xlabel('secs.')
			pylab.grid(True)

			pylab.show()			

# ./src/peopledetect.py "metadata"
if __name__ == "__main__":
	 main()
