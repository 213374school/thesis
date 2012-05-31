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

# Find a JSON parser
try:
	import json
except ImportError:
	try:
		import simplejson as json
	except ImportError:
		print 'ERROR: JSON parser not found!'

helptxt = """usage:\n./peopledetect.py src_folder"""
from collections import deque
 
from collections import deque
 
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
	cap, fps = None, 0
	for i in range(1,5):
		# check each "coreX" folder
		exts = ['m4v', 'avi']
		for ext in exts:
			if os.path.isfile('%s/core%d/%s.%s' % (data_folder, i, ytid, ext)):
				print '%s found in: "core%d"' % (ytid, i)
				video_src = '%s/core%d/%s.%s' % (data_folder, i, ytid, ext)
				cap = video.create_capture(video_src)
				capture = cv.CaptureFromFile(video_src)
				fps = cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS)
				w = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
				h =  int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
	return cap, fps, w, h

center_rectangle = ((200, 30), (440, 270))

def is_in_focus_center(x,y,w,h):

	ul, lr = center_rectangle
	cx, cy = (x+w/2, y+h/2)
	# print 'cx,cy = (%d,%d)' % (cx,cy)
	return cx >= ul[0] and cx <= lr[0] and cy >= ul[1] and cy <= lr[1]

def main():
	try:
		metadata_folder = sys.argv[1]
	except:
		print helptxt
	else:
		ytids_lib = get_ytids_lib(metadata_folder)
		# print ytids_lib
		ytids = ytids_lib.get('ytids', [])
		ytids = [ytids[20]] # 20 = tale
		for ytid in ytids:
			bd = json.loads(open('%s/bodydetect/%s.json' % (metadata_folder, ytid),'r').read())
			fd = json.loads(open('%s/facedetect/%s.json' % (metadata_folder, ytid),'r').read())
			pr = json.loads(open('%s/profile/%s.json'	% (metadata_folder, ytid),'r').read())
			
			cap, fps, vw, vh = get_video(metadata_folder, ytid)
			font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 1.0, 1.0)
			body = bd.get('body')
			face = fd.get('faces')
			prof = pr.get('profile')

			# check for consistency
			if len(body) == len(face) and len(face) == len(prof):
				detected_objects = [body[i] + face[i] + prof[i] for i in range(len(body))]

			index = 0
			person_in_focus_frames_count = 0
			person_frames_count = 0
			# minimum number of neighboring rectangles (7 or 8 seems like a good value - there is an article where they determine that 7 is the best REF!!!)
			n_min = 8
			period = 6
			sma = Simplemovingaverage(period)
			period = 4
			focus_sma = Simplemovingaverage(period)
			while True:
				ret, frame = cap.read()
				if ret:
					img = cv.fromarray(frame)
				else:
					break

				people_count = 0
				person_in_focus_center = False
				for (x,y,w,h),n in body[index]:
					color = cv.RGB(25, 25, 112) # midnight blue 25-25-112
					if n > n_min:
						people_count += 1
						cv.Rectangle(img, (x,y), (x+w,y+h), color)
						cv.PutText(img, 'B', (x+w/2,y+h/2), font, color)
						if not person_in_focus_center:
							person_in_focus_center = is_in_focus_center(x,y,w,h)
				for (x,y,w,h),n in face[index]:
					color = cv.RGB(0, 100, 0) # dark green 0-100-0
					if n > n_min:
						people_count += 1
						cv.Rectangle(img, (x,y), (x+w,y+h), color)						
						cv.PutText(img, 'F', (x+w/2,y+h/2), font, color)
						if not person_in_focus_center:
							person_in_focus_center = is_in_focus_center(x,y,w,h)
				for (x,y,w,h),n in prof[index]:
					color = cv.RGB(178, 34, 34) # firebrick 178-34-34
					if n > n_min:
						people_count += 1
						cv.Rectangle(img, (x,y), (x+w,y+h), color)						
						cv.PutText(img, 'P', (x+w/2,y+h/2), font, color)
						if not person_in_focus_center:
							person_in_focus_center = is_in_focus_center(x,y,w,h)

				index += 1

				person_in_focus_center = round(focus_sma(int(person_in_focus_center)))
				# center focus
				color = cv.RGB(255, 0, 0) # red
				if person_in_focus_center:
					color = cv.RGB(0, 255, 0) # green
					person_in_focus_frames_count += 1
				ul, lr = center_rectangle
				cv.Rectangle(img, ul, lr, color)

				# people count
				people_count = sma(people_count)
				color = cv.RGB(255, 0, 0) # red
				if people_count:
					color = cv.RGB(0, 255, 0) # green
					person_frames_count += 1
				cv.PutText(img, 'mov. avr. people count: %d' % people_count, (24,24), font, color)
				cv.PutText(img, 'people count (frames): %d' % person_frames_count, (24, vh-int(1.0*24)), font, cv.RGB(255, 255, 255))
				cv.PutText(img, 'focus count (frames): %d (%2.1f%%)' % (person_in_focus_frames_count, 100.0 * person_in_focus_frames_count / index), (24, vh-int(0.5*24)), font, cv.RGB(255, 255, 255))

				ShowImage("people detection demo", img)
				cv2.waitKey(int(1000.0/fps))

# ./src/peopledetect.py "metadata"
if __name__ == "__main__":
	 main()