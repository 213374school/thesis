#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import urllib

def main():
	# bulkupload videos to YouTube
	
	# to use http (???): http://pycurl.sourceforge.net/

	email = 't.nicksen@gmail.com'
	password = 'ozF1!F2x_NJt'
	category = 'Education'
	keywords = ''
	description = 'thesis.fmitcar.appspot.com/thesis/'

	try:
		path = sys.argv[1]
	except:	
		path = './' # default to current directory (calling)

	files = [filename for filename in os.listdir(path) if filename.split('.')[-1] in ['m4v','avi']]

	for filename in files:
		title = filename.split('.')[0]
		
		command = 'python ./youtube-ul.py --email=%s --password=%s --title="%s" --description="%s" --category="%s" --keywords="%s"  %s' % (email, password, title, description, category, keywords, filename)
		print command
		os.system(command)
	
if __name__ == "__main__":

	# main()

	raw_input("REMEMBER TO MAKE VIDEOS PUBLIC HERE: https://www.youtube.com/my_videos - Press Enter to get a list of uploaded (public) YouTube IDs...")

	# to get videos: curl https://gdata.youtube.com/feeds/api/users/ThomNicksen/uploads?alt=json&&prettyprint=true
	url = 'https://gdata.youtube.com/feeds/api/users/ThomNicksen/uploads?alt=json'
	response = urllib.urlopen(url).read()	
	content = json.loads(response)
	entries = content.get('feed').get('entry')
	ytids = []
	for entry in entries:
		medias = entry.get('media$group').get('media$content')
		# there are 3 entries in this. we want the first
		media = medias[0]
		url = media.get('url') # form: https://www.youtube.com/v/t8OWJ_VlOnQ?version=3&f=user_uploads&app=youtube_gdata
		ytid = url.replace('https://www.youtube.com/v/', '').replace('?version=3&f=user_uploads&app=youtube_gdata', '')
		ytids.append(ytid)
		# print json.dumps(media, sort_keys=True, indent=4)	
	
	# build a string we can copy paste directly into app engine cms, ex.: t8OWJ_VlOnQ,khjtPXCIh_o,a3gR-zDZlmw,6IU6G-DXjBc

	s = ''
	for i, ytid in enumerate(ytids):
		if i < len(ytids)-1:
			s += '%s,' % ytid
		else:
			s += ytid
	print s

	# goto: https://www.youtube.com/my_videos
	# print json.dumps(content, sort_keys=True, indent=4)
