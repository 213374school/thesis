#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import os
import json
import sys

def triangleSmooth(lst=[], degree=1):

	if degree < 1:
		print 'degree must be > 1'
		return

	triangle = np.array(range(degree)+[degree]+range(degree)[::-1])+1
	lst = np.array(lst)
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

def calcStd(lst, no_frames=12):

	varianceList = [0] * no_frames
	for i in range(no_frames,len(lst)):
		subList = lst[i-no_frames:i+1]
		varianceList.append(np.std(subList))
	return varianceList


def getPeopleInFrame(ytid):
	return []

def getPersonInFocus(ytid):

	try:
		ytid = ytid.split('.')[0]
	except Exception as e:
		print e, ytid	

	metadata_filename = '%s/metadata/peopledetect/%s.json' % (os.path.dirname(os.path.realpath(__file__)) + '/../', ytid)
	if os.path.isfile(metadata_filename):
		f = open(metadata_filename,'r')
		content = f.read()
		_lib = json.loads(content)     
		f.close()
	else:
		_lib = dict()
	return _lib.get('in_focus', [])

def getBlueChannelMean(ytid):

	try:
		ytid = ytid.split('.')[0]
	except Exception as e:
		print e, ytid	

	metadata_filename = '%s/metadata/blue_channel/%s.json' % (os.path.dirname(os.path.realpath(__file__)) + '/../', ytid)
	if os.path.isfile(metadata_filename):
		f = open(metadata_filename,'r')
		content = f.read()
		_lib = json.loads(content)     
		f.close()
	else:
		_lib = dict()
	return _lib.get('blue_mean', [])

def hasPolicePresenceLabeller(ytid):
	return []

def hasPersonInFocusLabeller(ytid, smoothness_degree=36, cutoff_val=0.3, max_interval_neighbor_distance=24, min_interval_size=5*24):

	# smooth over smoothness_degree/24 seconds and all values < cutoff_val are set to 0
	# neighboring intervals that are less than max_interval_neighbor_distance are merged into one
	# if an interval is shorter than min_interval_size frames then it is discarded

	try:
		ytid = ytid.split('.')[0]
	except Exception as e:
		print e, ytid
	print ytid

	pif = getPersonInFocus(ytid)
	if pif:
		# print 'pif: ', pif
		pif_smooth = triangleSmooth(pif, smoothness_degree)
		# print 'pif smooth (BEFORE): ', pif_smooth
		pif_smooth = np.array(np.array(pif_smooth) > cutoff_val, dtype=np.int64)
		print 'cut off %d of %d values' % (sum(np.array(np.array(pif_smooth) < cutoff_val, dtype=np.int64)), len(pif_smooth))
		# print 'pif smooth (AFTER): ', pif_smooth
		out = []
		frame_start_index = -1
		frame_end_index = -1
		for i in range(len(pif_smooth)):
			if pif_smooth[i]:
				if frame_start_index == -1:
					frame_start_index = i
				frame_end_index = i + 1
			# if neither is -1
			elif not (frame_start_index == frame_end_index == -1):
				out.append((frame_start_index, frame_end_index))
				frame_start_index = frame_end_index = -1

		print 'out: ', out
		print '#sequences: %d' % len(out)

		# sanity check
		for a,b in out:
			for i in range(a,b):
				if not pif_smooth[i]:
					raise Exception('sanity check failed in %s for video %s' % (hasPersonInFocusLabeller.__name__, ytid))

		# we will now merge the neighboring intervals and delete the very short intervals
		out_merged = out
		while True:
			merged_or_removed_interval = False
			for i in range(len(out_merged)-1):
				a1,b1 = out[i]
				a2,b2 = out[i+1]
				# print 'inspecting intervals: ', out[i], ', ', out[i+1]				
				interval_distance = a2 - b1
				if interval_distance < max_interval_neighbor_distance:
					# print 'merging intervals: ', out[i], ', ', out[i+1]
					out_merged[i] = (a1,b2)
					del out_merged[i+1]
					merged_or_removed_interval = True
					break

				if b1 - a1 < min_interval_size:
					# print 'deleting interval: ', out[i]
					del out_merged[i]
					merged_or_removed_interval = True
					break
				if b2 - a2 < min_interval_size:
					# print 'deleting interval: ', out[i+1]
					del out_merged[i+1]
					merged_or_removed_interval = True
					break						
			if not merged_or_removed_interval:
				break

		print 'out_merged: ', out_merged
		print '#sequences: %d' % len(out_merged)
		fps = 24
		for a,b in out_merged:
			print '%02d:%02d -> %02d:%02d' % (a/fps/60, a/fps%60, b/fps/60, b/fps%60)

		return out_merged
	else:
		return []

# print os.path.dirname(os.path.realpath(__file__)) + '/../'

def main():

	ytid = sys.argv[1].split('/')[-1]
	hasPersonInFocusLabeller(ytid)

if __name__ == "__main__":
	 main()