#!/usr/bin/python

import urllib2
import json
import os
import sys
import time
import Queue
import threading
import string


def main(argv=None):

	# Do search on youtube
	searchURL = 'https://gdata.youtube.com/feeds/api/users/laugejepsen/uploads/?v=2&max-results=50&alt=json'

	response = urllib2.urlopen(searchURL)
	resultString = response.read()
	result = json.loads(resultString)


	# Process the result
	feed = result.get('feed')
	entries = feed.get('entry')
	videos = []
	for entry in entries:

		mediaGroup = entry.get('media$group')
		uploadedTime = mediaGroup.get('yt$uploaded').get('$t')
		title = mediaGroup.get('media$title').get('$t')
		length = int(mediaGroup.get('yt$duration').get('seconds'))
		videoID = mediaGroup.get('yt$videoid').get('$t')
		keywords = mediaGroup.get('media$keywords').get('$t')
		category = mediaGroup.get('media$category')[0].get('$t')

		video = {'id':videoID, 'title': title, 'length':length, 'uploaded': uploadedTime, 'category': category, 'keywords':keywords}
		videos.append(video)

	for video in videos:
		print '%s (%d seconds long)' % (video.get('id'), video.get('length'))

	#return videos


if __name__ == '__main__': 
	main()