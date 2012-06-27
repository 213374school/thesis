#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json

helptxt = """%s metadata_folder""" % __file__

def main():
	
	try:
		metadata_folder = sys.argv[1]
	except:
		print helptxt
	else:
		files = [filename for filename in os.listdir(metadata_folder) if filename.split('.')[-1] in ['json']]
		# files = [files[0]]
		for f in files:
			metadata_filename = '%s%s' % (metadata_folder, f)
			# print metadata_filename
			f = open(metadata_filename,'r')
			content = f.read()
			metadata = json.loads(content)     
			f.close()

			content = json.dumps(metadata, sort_keys=True, indent=4)

			# do not write a file if json parser fails
			if content:
				# write to disc
				f = open(metadata_filename,'w') 
				f.write(content)
				f.close()

if __name__ == "__main__":
	 main()