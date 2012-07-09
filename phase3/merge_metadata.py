#!/usr/bin/python

import os
import sys
import json

def main():

	files1, files2 = [filename for filename in os.listdir('./metadata/') if filename.split('.')[-1] in ['json']], [filename for filename in os.listdir('./lauges_metadata/') if filename.split('.')[-1] in ['json']]
	
	for fn1 in files1:
		assert fn1 in files2

		f1 = open('./metadata/%s' % (fn1),'r')
		f2 = open('./lauges_metadata/%s' % (fn1),'r')
		content1 = f1.read()
		content2 = f2.read()

		d1 = json.loads(content1)
		d2 = json.loads(content2)

		# put data from content2 into content1
		# print content1, content2
		for k in d2:
			try:
				assert (not k in d1)
			except Exception as e:
				print e
			d1[k] = d2[k]
		content1 = json.dumps(d1)
		f1 = open('./metadata/%s' % (fn1),'w')
		f1.write(content1)
		f1.close()
		print 'wrote %d bytes to %s' % (len(content1), fn1)

if __name__ == '__main__':
    main()